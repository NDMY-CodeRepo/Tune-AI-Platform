"""Live approval rejection, revision, audit and concurrency checks; no migration."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
import json
from pathlib import Path
from unittest.mock import patch
import uuid
from fastapi.testclient import TestClient
from apps.api.main import app
from shared.snowflake_service import get_service
from shared.desk_service import TICKETS

ROOT=Path(__file__).resolve().parents[1]


def run():
    s=get_service();client=TestClient(app,raise_server_exceptions=False)
    def schema(name):return s.query("SELECT SHA2(GET_DDL('SCHEMA',?,TRUE),256) HASH",[name]).iloc[0,0]
    before={name:schema(name) for name in ['TUNE_BI_DB.APP_STATE','TUNE_BI_DB.GOLD']}
    actor='validation.effort.review';tid=str(uuid.uuid4())
    body=dict(ticket_id=tid,actor=actor,business_unit='Claims',category='ENHANCEMENT',title='[Validation] Effort approval decisions '+tid[:8],
        description='Illustrative approval, rejection and revision checks. No production request or delivery implied.',
        justification='Validate the effort approval workflow.',priority='MEDIUM',required_by=str(date.today()+timedelta(days=14)),
        business_impact='Synthetic validation only.',data_domain='Motor',output_format='Dashboard')
    response=client.post('/api/desk/tickets',json=body);assert response.status_code==200,response.text
    data=response.json();t=data['ticket']
    def change(role='Data Team',expected=200,**payload):
        nonlocal data,t
        version=t['VERSION']
        response=client.post(f'/api/desk/tickets/{tid}/updates',json={
            'actor':'demo.engineer' if role=='Data Team' else actor,'role':role,'version':version,'entry_type':'STATUS_UPDATE',**payload})
        assert response.status_code==expected,(response.status_code,response.text)
        if expected==200:data=response.json();t=data['ticket']
        else:assert s.ticket(tid)['VERSION']==version,'Rejected operation mutated ticket'
        return response
    change(changes={'STATUS':'TRIAGED','ASSIGNED_TO':'demo.engineer','CONFIRMED_PRIORITY':'HIGH'})
    change(expected=422,changes={'STATUS':'IN_PROGRESS'})
    change(expected=422,effort_action='SUBMIT',changes={'EFFORT_ESTIMATE':'M'})
    change(effort_action='SUBMIT',changes={'EFFORT_ESTIMATE':'M','ASSESSMENT_NOTES':'Data mapping, development and validation are required.'})
    original_revision=t['EFFORT_ASSESSMENT_VERSION']
    assert t['STATUS']=='AWAITING_BU_APPROVAL' and t['ASSESSED_BY']=='demo.engineer' and t['ASSESSED_AT']
    change('Business User',expected=422,effort_action='APPROVE',assessment_version=original_revision)
    change('Business User',expected=422,effort_action='REJECT',assessment_version=original_revision,confirmed=True)
    change(expected=422,effort_action='APPROVE',assessment_version=original_revision,confirmed=True)
    change('Business User',effort_action='REJECT',assessment_version=original_revision,confirmed=True,message='Please reduce scope before engineering begins.')
    assert t['STATUS']=='REJECTED' and t['APPROVAL_DECIDED_BY']==actor and t['APPROVAL_DECIDED_AT']
    assert t['APPROVAL_COMMENTS']=='Please reduce scope before engineering begins.'
    change(expected=422,changes={'STATUS':'IN_PROGRESS'})
    change(expected=422,effort_action='SUBMIT')
    change(effort_action='REASSESS')
    change(effort_action='SUBMIT',changes={'EFFORT_ESTIMATE':'S','ASSESSMENT_NOTES':'Reduced mapping and targeted validation.'})
    assert t['EFFORT_ASSESSMENT_VERSION']>original_revision and t['APPROVAL_DECISION'] is None
    change('Business User',expected=422,effort_action='APPROVE',assessment_version=original_revision,confirmed=True)
    # Decision persistence must roll back together with all approval audit entries.
    snapshot=s.ticket(tid);history_count=len(s.activity(tid))
    with patch.object(s,'_activity',side_effect=RuntimeError('simulated decision audit failure')):
        change('Business User',expected=503,effort_action='APPROVE',assessment_version=t['EFFORT_ASSESSMENT_VERSION'],confirmed=True)
    assert s.ticket(tid)==snapshot and len(s.activity(tid))==history_count
    # Two contradictory decisions made from the same version: exactly one succeeds.
    shared_version=t['VERSION'];shared_revision=t['EFFORT_ASSESSMENT_VERSION']
    def decide(action):
        return client.post(f'/api/desk/tickets/{tid}/updates',json={
            'actor':actor,'role':'Business User','version':shared_version,'effort_action':action,
            'assessment_version':shared_revision,'confirmed':True,'entry_type':'STATUS_UPDATE','message':'Concurrent decision validation.'})
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(decide,['APPROVE','REJECT']))
    assert sorted(r.status_code for r in responses)==[200,409]
    data=next(r.json() for r in responses if r.status_code==200);t=data['ticket']
    assert len([a for a in data['activity'] if a['ENTRY_TYPE'] in ('EFFORT_APPROVED','EFFORT_REJECTED')])==2
    if t['STATUS']=='REJECTED':
        change(effort_action='REASSESS');change(effort_action='SUBMIT')
        change('Business User',effort_action='APPROVE',assessment_version=t['EFFORT_ASSESSMENT_VERSION'],confirmed=True)
    approved_revision=t['EFFORT_ASSESSMENT_VERSION']
    assert t['APPROVAL_VALID']
    change(expected=422,changes={'EFFORT_ESTIMATE':'L','STATUS':'IN_PROGRESS'})
    change(changes={'EFFORT_ESTIMATE':'L','ASSESSMENT_NOTES':'Expanded scope requires additional development and validation.'})
    assert t['STATUS']=='TRIAGED' and not t['APPROVAL_VALID'] and t['APPROVAL_DECISION'] is None
    change(expected=422,changes={'STATUS':'IN_PROGRESS'})
    change(effort_action='SUBMIT')
    change('Business User',expected=422,effort_action='APPROVE',assessment_version=approved_revision,confirmed=True)
    change('Business User',effort_action='APPROVE',assessment_version=t['EFFORT_ASSESSMENT_VERSION'],confirmed=True,message='Expanded effort acknowledged.')
    change(changes={'STATUS':'IN_PROGRESS'})
    # Notes revisions during active work also withdraw engineering readiness.
    change(changes={'ASSESSMENT_NOTES':'Revised validation scope during implementation.'})
    assert t['STATUS']=='TRIAGED' and not t['APPROVAL_VALID']
    change(expected=422,changes={'STATUS':'IN_PROGRESS'})
    change(effort_action='SUBMIT')
    change('Business User',effort_action='APPROVE',assessment_version=t['EFFORT_ASSESSMENT_VERSION'],confirmed=True)
    change(changes={'STATUS':'IN_PROGRESS'})
    change(changes={'STATUS':'RESOLVED','RESOLUTION_NOTES':'Illustrative effort workflow validated. No production output delivered.'})
    change('Business User',changes={'STATUS':'CLOSED'})
    kinds={x['ENTRY_TYPE'] for x in data['activity']}
    assert {'EFFORT_ASSESSED','EFFORT_SUBMITTED','APPROVAL_REQUESTED','EFFORT_REJECTED','EFFORT_APPROVED','EFFORT_REVISED'}<=kinds
    # A historical ticket remains readable; a rejected start attempt does not modify it.
    legacy=s.query(f"SELECT * FROM {TICKETS} WHERE EFFORT_ASSESSMENT_VERSION IS NULL AND STATUS='RESOLVED' ORDER BY CREATED_AT LIMIT 1")
    assert not legacy.empty
    old=legacy.iloc[0].to_dict()
    assert client.get(f'/api/desk/tickets/{old["TICKET_ID"]}',params={'actor':'demo.engineer','role':'Data Team'}).status_code==200
    blocked=client.post(f'/api/desk/tickets/{old["TICKET_ID"]}/updates',json={'actor':'demo.engineer','role':'Data Team','version':int(old['VERSION']),
        'entry_type':'STATUS_UPDATE','changes':{'STATUS':'IN_PROGRESS'}})
    assert blocked.status_code==422
    assert s.ticket(old['TICKET_ID'])==old
    after={name:schema(name) for name in before};assert before==after
    result=dict(status='PASS',ticket_id=tid,reference=t['REFERENCE'],assessment_persistence='PASS',approval_confirmation='PASS',
        rejection_reason_and_actor_timestamp='PASS',rejected_work_blocked='PASS',explicit_reassessment_resubmission='PASS',
        stale_assessment_revision_blocked='PASS',revised_size_invalidates_approval='PASS',revised_notes_during_work_invalidates_approval='PASS',
        concurrent_decisions_single_winner='PASS',decision_and_audit_atomic_rollback='PASS',audit_event_types=sorted(kinds),
        legacy_ticket_access_preserved='PASS',unapproved_legacy_reopening_blocked='PASS',final_status=t['STATUS'],
        schema_before=before,schema_after=after)
    (ROOT/'validation/desk_effort_acceptance.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':run()
