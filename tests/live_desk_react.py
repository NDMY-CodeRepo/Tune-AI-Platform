"""Live HTTP/Snowflake desk acceptance; retains one labelled validation ticket closed."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
import json
from pathlib import Path
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from apps.api.main import app
from shared.snowflake_service import get_service

ROOT=Path(__file__).resolve().parents[1]


def run():
    s=get_service();client=TestClient(app,raise_server_exceptions=False)
    def schema(name):
        return s.query("SELECT SHA2(GET_DDL('SCHEMA',?,TRUE),256) HASH",[name]).iloc[0,0]
    before={name:schema(name) for name in ['TUNE_BI_DB.APP_STATE','TUNE_BI_DB.GOLD']}
    actor='validation.react.desk';tid=str(uuid.uuid4())
    def checked(response):
        assert response.status_code==200,(response.status_code,response.text)
        return response.json()
    body=dict(ticket_id=tid,actor=actor,business_unit='Motor',category='REPORT_REQUEST',
        title='[Validation] React Service Desk '+tid[:8],description='Synthetic React HTTP workflow rehearsal. No real report requested.',
        justification='Verify the React adapter preserves the established workflow.',priority='MEDIUM',
        required_by=str(date.today()+timedelta(days=14)),business_impact='Synthetic demonstration only.',data_domain='Motor',
        existing_reference='Validation dataset reference',reporting_period='October 2026',
        required_fields='Month, channel, claims paid',output_format='Excel')
    data=checked(client.post('/api/desk/tickets',json=body));t=data['ticket']
    assert t['STATUS']=='NEW' and t['REFERENCE'].startswith('TDS-')
    assert t['DATA_DOMAIN']=='Motor' and t['REQUIRED_FIELDS']=='Month, channel, claims paid'
    retried=checked(client.post('/api/desk/tickets',json=body))
    assert retried['ticket']['TICKET_ID']==tid and len(retried['activity'])==len(data['activity'])
    def update(role='Data Team',**payload):
        nonlocal data,t
        data=checked(client.post(f'/api/desk/tickets/{tid}/updates',json={
            'actor':'demo.engineer' if role=='Data Team' else actor,'role':role,'version':t['VERSION'],**payload}))
        t=data['ticket']
    assert client.post(f'/api/desk/tickets/{tid}/updates',json={'actor':'demo.engineer','role':'Data Team','version':t['VERSION'],
        'entry_type':'STATUS_UPDATE','changes':{'STATUS':'RESOLVED','ASSIGNED_TO':'demo.engineer','RESOLUTION_NOTES':'invalid shortcut'}}).status_code==422
    update(entry_type='STATUS_UPDATE',changes={'STATUS':'TRIAGED','ASSIGNED_TO':'demo.engineer','CONFIRMED_PRIORITY':'HIGH',
        'TARGET_DATE':str(date.today()+timedelta(days=7)),'EFFORT_ESTIMATE':'M'})
    assert client.post(f'/api/desk/tickets/{tid}/updates',json={'actor':'demo.engineer','role':'Data Team','version':t['VERSION'],
        'entry_type':'STATUS_UPDATE','changes':{'STATUS':'IN_PROGRESS'}}).status_code==422
    update(entry_type='STATUS_UPDATE',effort_action='SUBMIT',changes={
        'EFFORT_ESTIMATE':'M','ASSESSMENT_NOTES':'Data mapping, development and validation are required.'})
    assert t['STATUS']=='AWAITING_BU_APPROVAL' and t['ASSESSED_BY']=='demo.engineer' and t['ASSESSED_AT']
    update('Business User',entry_type='STATUS_UPDATE',effort_action='APPROVE',assessment_version=t['EFFORT_ASSESSMENT_VERSION'],confirmed=True)
    assert t['STATUS']=='APPROVED' and t['APPROVAL_VALID']
    update(entry_type='STATUS_UPDATE',changes={'STATUS':'IN_PROGRESS','PROGRESS_NOTES':'Confirmed source fields and report grain.'})
    queue=checked(client.get('/api/desk/tickets',params={'actor':'demo.engineer','role':'Data Team','scope':'All records','status':'IN_PROGRESS','owner':'demo.engineer','priority':'HIGH'}))
    assert any(x['TICKET_ID']==tid for x in queue['rows'])
    update(entry_type='CLARIFICATION_REQUEST',message='Should this use settlement month?')
    assert t['STATUS']=='WAITING_FOR_BU'
    visible=checked(client.get(f'/api/desk/tickets/{tid}',params={'actor':actor}))
    assert any(a['ENTRY_TYPE']=='CLARIFICATION_REQUEST' and 'settlement month' in a['MESSAGE'] for a in visible['activity'])
    assert client.get(f'/api/desk/tickets/{tid}',params={'actor':'different.requester'}).status_code==404
    update('Business User',entry_type='CLARIFICATION_RESPONSE',message='Yes, please use settlement month.',resume=True)
    assert t['STATUS']=='IN_PROGRESS'
    assert any(a['ENTRY_TYPE']=='CLARIFICATION_RESPONSE' for a in data['activity'])
    update(message='Private validation implementation note.',internal=True)
    visible=checked(client.get(f'/api/desk/tickets/{tid}',params={'actor':actor}))
    assert not any(a['IS_INTERNAL'] or 'Private validation' in a['MESSAGE'] for a in visible['activity'])
    assert client.post(f'/api/desk/tickets/{tid}/updates',json={'actor':actor,'role':'Business User','version':t['VERSION'],
        'entry_type':'STATUS_UPDATE','changes':{'ASSIGNED_TO':'tampered'}}).status_code==422
    assert client.post(f'/api/desk/tickets/{tid}/updates',json={'actor':actor,'role':'Business User','version':1,'message':'stale'}).status_code==409
    version=t['VERSION']
    with patch.object(s,'_activity',side_effect=RuntimeError('simulated activity outage')):
        assert client.post(f'/api/desk/tickets/{tid}/updates',json={'actor':'demo.engineer','role':'Data Team','version':version,'message':'atomic rollback test'}).status_code==503
    assert s.ticket(tid)['VERSION']==version
    update(entry_type='STATUS_UPDATE',changes={'STATUS':'RESOLVED','RESOLUTION_NOTES':'Synthetic API workflow verified. No actual report delivered.',
                                             'DELIVERED_REFERENCE':'REACT-VALIDATION-OUTPUT'})
    visible=checked(client.get(f'/api/desk/tickets/{tid}',params={'actor':actor}))
    assert visible['ticket']['DELIVERED_REFERENCE']=='REACT-VALIDATION-OUTPUT' and visible['ticket']['STATUS']=='RESOLVED'
    update('Business User',entry_type='STATUS_UPDATE',changes={'STATUS':'IN_PROGRESS'},message='Synthetic reopening verification.')
    update(entry_type='STATUS_UPDATE',changes={'STATUS':'RESOLVED','RESOLUTION_NOTES':'Synthetic verification completed again. No report delivered.'})
    update('Business User',entry_type='STATUS_UPDATE',changes={'STATUS':'CLOSED'},message='Requester confirmed closure.')
    assert t['STATUS']=='CLOSED'
    version=t['VERSION']
    def competing(_):
        return client.post(f'/api/desk/tickets/{tid}/updates',json={'actor':'demo.engineer','role':'Data Team','version':version,'message':'HTTP version competition verification.'}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(competing,range(2)))
    assert sorted(outcomes)==[200,409],outcomes
    checked(client.get('/api/desk/overview',params={'actor':actor,'scope':'All records'}))
    checked(client.get('/api/desk/overview',params={'actor':'demo.engineer','role':'Data Team','dimension':'Status'}))
    catalogue=checked(client.get('/api/desk/catalogue',params={'keyword':'Motor','domain':'Motor'}))
    assert all(r['BUSINESS_DOMAIN']=='Motor' for r in catalogue['rows'])
    html=client.get('/desk');assert html.status_code==200 and 'Tune Data Service Desk' in html.text
    assert client.get('/').status_code==200
    after={name:schema(name) for name in before}
    assert before==after,(before,after)
    result=dict(status='PASS',ticket_id=tid,reference=t['REFERENCE'],
        request_fields='PASS',retry_idempotency='PASS',queue_filtering='PASS',triage_assignment='PASS',
        effort_assessment_approval_gate='PASS',clarification_both_directions='PASS',internal_note_visibility='PASS',requester_guards='PASS',
        stale_version_409='PASS',history_failure_atomic_rollback='PASS',resolution_visibility='PASS',reopen_closure='PASS',
        concurrent_http_update_one_winner='PASS',catalogue_filter='PASS',separate_frontend_routes='PASS',
        schema_hashes_before=before,schema_hashes_after=after,
        browser='NOT VERIFIED: HTTP and build checks do not establish browser rendering or clicks')
    (ROOT/'validation/desk_react_acceptance.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    run()
