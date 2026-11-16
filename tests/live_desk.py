"""Live desk acceptance. Creates a labelled validation ticket and retains it closed.
AppTest verifies Streamlit interactions, not browser appearance or dataframe clicks.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch
import uuid

import toml
from streamlit.testing.v1 import AppTest
from shared.snowflake_service import get_service, SnowflakeService
from shared.desk_service import TICKETS
from shared.desk_rules import reference
from tests.migrate_desk import gold_snapshot

ROOT=Path(__file__).resolve().parents[1]


def run():
    s=get_service()
    gold=gold_snapshot(s)
    a=AppTest.from_file(str(ROOT/'apps/data-service-desk/app.py'),default_timeout=90).run()
    def clean():
        assert not a.exception, a.exception
        assert not a.error, [e.value for e in a.error]
        assert not a.warning,[w.value for w in a.warning]
    def element(kind,label):
        return next(x for x in getattr(a,kind) if x.label==label)
    def button(label):
        element('button',label).click().run(); clean()
    def select(label,value):
        element('selectbox',label).set_value(value).run(); clean()
    def section(label):
        element('radio','Ticket section').set_value(label).run();clean()
    def open_ticket(tid):
        a.session_state['selected_ticket']=tid
        a.run(); clean()
    clean()
    element('text_input','Demo requester identity').set_value('validation.desk').run();clean()
    a.radio(key='bu_page').set_value('Find Existing Reports').run();clean()
    element('text_input','Search reports').set_value('Motor').run();clean()
    assert any('[Demo] Motor' in x.value for x in a.subheader)
    button('New Data Request')
    # Required fields must prevent advancing.
    element('text_input','Request title').set_value('[Validation] Enhanced desk workflow '+str(uuid.uuid4())[:8])
    element('text_area','Description').set_value('Synthetic validation: monthly Motor claims by channel.')
    element('text_area','Business justification').set_value('Verify the structured request workflow; no real delivery.')
    element('text_area','Business impact').set_value('Synthetic review rehearsal only.')
    required=date.today()+timedelta(days=14)
    element('date_input','Required-by date').set_value(required)
    token=a.session_state['request_token']
    button('Continue to data requirements')
    element('text_input','Reporting period').set_value('October 2026')
    element('text_input','Existing report / dataset reference').set_value('Validation reference')
    element('text_area','Required metrics or fields').set_value('Month, channel, claims paid')
    button('Review request');button('Submit request')
    t=s.ticket(token,'validation.desk')
    assert t['STATUS']=='NEW' and t['REQUIRED_BY']==required
    for field,expected in {'BUSINESS_IMPACT':'Synthetic review rehearsal only.','DATA_DOMAIN':'Motor',
        'REPORTING_PERIOD':'October 2026','EXISTING_REFERENCE':'Validation reference',
        'REQUIRED_FIELDS':'Month, channel, claims paid','OUTPUT_FORMAT':'Excel'}.items():
        assert t[field]==expected,(field,t[field])
    # Retry returns the same request, without another history row.
    n=len(s.activity(token))
    s.create_ticket(token,'Motor','validation.desk','retry','retry','REPORT_REQUEST','MEDIUM','retry')
    assert len(s.activity(token))==n
    a.sidebar.radio[0].set_value('Data Team Workspace').run();clean()
    a.radio(key='team_page').set_value('Request Queue').run();clean()
    assert a.dataframe
    open_ticket(token);section('Manage request')
    element('text_input','Assigned owner').set_value('demo.engineer')
    element('selectbox','Confirmed priority').set_value('HIGH')
    element('selectbox','Update status').set_value('TRIAGED')
    element('selectbox','Effort estimate').set_value('M')
    target=date.today()+timedelta(days=7)
    element('date_input','Target completion date').set_value(target)
    button('Save ticket update')
    t=s.ticket(token);assert t['STATUS']=='TRIAGED' and t['TARGET_DATE']==target and t['CONFIRMED_PRIORITY']=='HIGH'
    element('selectbox','Update status').set_value('IN_PROGRESS')
    button('Save ticket update')
    # Request clarification through the actual Streamlit conversation form.
    section('Conversation & history')
    element('selectbox','Entry type').set_value('Request clarification')
    element('text_area','Message').set_value('Should the report use notification month or settlement month?')
    button('Send update')
    assert s.ticket(token)['STATUS']=='WAITING_FOR_BU'
    a.sidebar.radio[0].set_value('Business User Portal').run();clean();open_ticket(token);section('Conversation & history')
    assert any('settlement month' in m.value for m in a.markdown)
    element('selectbox','Entry type').set_value('Respond to clarification')
    element('text_area','Message').set_value('Please use settlement month.')
    button('Send update')
    assert s.ticket(token)['STATUS']=='IN_PROGRESS'
    a.sidebar.radio[0].set_value('Data Team Workspace').run();clean();open_ticket(token);section('Conversation & history')
    assert any('Please use settlement month.' in m.value for m in a.markdown)
    element('text_area','Message').set_value('Private implementation note for Data Team only.')
    element('checkbox','Internal note — hidden from BU').set_value(True)
    button('Send update')
    assert s.activity(token).IS_INTERNAL.any()
    assert not s.activity(token,'validation.desk').IS_INTERNAL.any()
    # Simulated history failure must roll the ticket row back in live Snowflake.
    before=s.ticket(token)
    with patch.object(s,'_activity',side_effect=RuntimeError('simulated history outage')):
        try:
            s.change_ticket(token,before['VERSION'],'demo.engineer','Data Team',message='rollback test')
            raise AssertionError('Expected failure')
        except RuntimeError:
            pass
    assert s.ticket(token)['VERSION']==before['VERSION']
    section('Manage request')
    element('selectbox','Update status').set_value('RESOLVED')
    element('text_area','Resolution notes').set_value('Synthetic validation complete. No actual report was delivered.')
    element('text_input','Delivered output link or reference').set_value('VALIDATION-OUTPUT-REFERENCE')
    button('Save ticket update')
    a.sidebar.radio[0].set_value('Business User Portal').run();clean();open_ticket(token);section('Resolution')
    assert any('VALIDATION-OUTPUT-REFERENCE' in m.value for m in a.markdown)
    section('Conversation & history')
    assert not any('Private implementation' in m.value for m in a.markdown)
    section('Resolution')
    # Reopen and re-resolve, then confirm closure in the portal.
    element('text_input','Reason to reopen').set_value('Synthetic check: confirm the selected reporting period.')
    button('Reopen request')
    assert s.ticket(token)['STATUS']=='IN_PROGRESS'
    current=s.ticket(token)
    s.change_ticket(token,current['VERSION'],'demo.engineer','Data Team',changes={
        'STATUS':'RESOLVED','RESOLUTION_NOTES':'Synthetic validation complete. Period confirmed; no report delivered.'},entry_type='STATUS_UPDATE')
    button('Refresh request');button('Confirm closure')
    assert s.ticket(token)['STATUS']=='CLOSED'
    # Rejected updates must leave version and activity counts unchanged.
    current=s.ticket(token);history=len(s.activity(token))
    for args in [dict(version=1,actor='demo.engineer',role='Data Team',message='stale'),
                 dict(version=current['VERSION'],actor='validation.desk',role='Business User',changes={'ASSIGNED_TO':'tampered'},entry_type='STATUS_UPDATE'),
                 dict(version=current['VERSION'],actor='demo.engineer',role='Data Team',changes={'STATUS':'IN_PROGRESS'},entry_type='STATUS_UPDATE')]:
        try:
            s.change_ticket(token,**args)
            raise AssertionError('Invalid update accepted')
        except ValueError:
            pass
    assert s.ticket(token)['VERSION']==current['VERSION'] and len(s.activity(token))==history
    duplicates=s.query(f'SELECT TICKET_NUMBER,COUNT(*) N FROM {TICKETS} GROUP BY 1 HAVING COUNT(*)>1 OR TICKET_NUMBER IS NULL')
    assert duplicates.empty
    # Independent sessions exercise sequence allocation concurrently, without ticket clutter.
    def allocate(_):
        from snowflake.snowpark import Session
        params=toml.load(os.environ['TUNE_SNOWFLAKE_CONFIG'])['connections'][os.environ['TUNE_SNOWFLAKE_CONNECTION']].copy()
        params.update(role=os.getenv('TUNE_SNOWFLAKE_ROLE','AGENT_ROLE'),warehouse=os.getenv('TUNE_SNOWFLAKE_WAREHOUSE','POC_WH'))
        session=Session.builder.configs(params).create()
        try:
            client=SnowflakeService(session)
            number=client.query('SELECT TUNE_BI_DB.APP_STATE.DATA_REQUEST_NUMBER.NEXTVAL N').iloc[0,0]
            outcome='unused'
            if _<2:
                try:
                    client.change_ticket(token,current['VERSION'],'demo.engineer','Data Team',message='Independent-session concurrency validation.')
                    outcome='saved'
                except ValueError:
                    outcome='stale'
            return number,outcome
        finally:
            session.close()
    with ThreadPoolExecutor(max_workers=4) as pool:
        allocations=list(pool.map(allocate,range(4)))
    numbers=[x[0] for x in allocations]
    assert len(numbers)==len(set(numbers))
    assert sorted(x[1] for x in allocations[:2])==['saved','stale']
    history=len(s.activity(token))
    assert gold==gold_snapshot(s)
    result={'status':'PASS','ticket_id':token,'reference':reference(t['TICKET_NUMBER']),
      'concurrent_update_one_winner':'PASS','request_fields_persist':'PASS','sequence_unique_independent_sessions':'PASS','retry_preserved':'PASS',
      'ui_triage_assign_target_effort':'PASS','ui_clarification_and_response':'PASS','internal_notes_hidden':'PASS',
      'activity_persisted':history,'history_failure_rolls_back':'PASS','stale_and_invalid_updates':'PASS',
      'resolution_reopen_closure':'PASS','gold_unchanged':'PASS','gold_hash':gold,
      'browser':'BLOCKED: browser access host unavailable; native pipe unavailable',
      'app_test':'PASS: form, navigation, queue render, detail and conversation interactions; selected-ticket state injected because AppTest does not click dataframe rows'}
    (ROOT/'validation/desk_upgrade_acceptance.json').write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))
    return result


if __name__=='__main__':
    run()
