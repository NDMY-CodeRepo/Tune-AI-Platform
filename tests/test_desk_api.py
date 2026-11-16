"""React desk adapter contracts: identity scope, version conflicts, role guards and writes."""
from datetime import date,timedelta
from unittest.mock import patch
import uuid
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app, DIST
from tests.test_desk_workflow import FakeDesk


def client():
    return TestClient(app)


def new_body():
    return dict(ticket_id=str(uuid.uuid4()),actor='bu',business_unit='Motor',title='Request',
                description='Description',justification='Business reason',category='REPORT_REQUEST',priority='MEDIUM',
                required_by=str(date.today()+timedelta(days=7)),business_impact='Monthly review',data_domain='Motor',output_format='Excel')


def test_create_reuses_workflow_and_rejects_team_owned_fields():
    body=new_body()
    with patch('apps.api.desk.get_service') as service,patch('apps.api.desk.ticket_payload',return_value={'ticket':{'TICKET_ID':body['ticket_id']}}):
        response=client().post('/api/desk/tickets',json=body)
        assert response.status_code==200,response.text
        service.return_value.create_ticket.assert_called_once_with(body['ticket_id'],'Motor','bu','Request','Description','REPORT_REQUEST','MEDIUM','Business reason',
            required_by=body['required_by'],business_impact='Monthly review',data_domain='Motor',existing_reference='',reporting_period=None,required_fields=None,output_format='Excel')
        assert client().post('/api/desk/tickets',json={**body,'ASSIGNED_TO':'tampered'}).status_code==422
        assert service.return_value.create_ticket.call_count==1


def test_business_user_list_is_scoped_and_filters_are_forwarded():
    with patch('apps.api.desk.get_service') as service:
        service.return_value.desk_queue.return_value=pd.DataFrame()
        response=client().get('/api/desk/tickets',params={'actor':'bu','priority':"HIGH'--",'sort':'Priority'})
    assert response.status_code==200
    service.return_value.desk_queue.assert_called_once_with('bu','All','All','All',"HIGH'--",'All','Priority','Exclude validation')
    service.return_value.desk_owners.assert_not_called()


def test_business_user_cannot_fetch_other_requester_history():
    desk=FakeDesk()
    with patch('apps.api.desk.get_service',return_value=desk):
        response=client().get('/api/desk/tickets/id',params={'actor':'someone.else','role':'Business User'})
    assert response.status_code==404
    assert not any('JOIN' in sql for sql,_ in desk.statements)


@pytest.mark.parametrize('changes',[{'ASSIGNED_TO':'other'},{'CONFIRMED_PRIORITY':'LOW'},{'STATUS':'RESOLVED'},{'DELIVERED_REFERENCE':'fake'}])
def test_business_user_mutation_guard_is_not_just_frontend(changes):
    desk=FakeDesk()
    with patch('apps.api.desk.get_service',return_value=desk):
        response=client().post('/api/desk/tickets/id/updates',json={'actor':'bu','role':'Business User','version':1,'entry_type':'STATUS_UPDATE','changes':changes})
    assert response.status_code==422
    assert not any(sql.startswith('UPDATE') for sql,_ in desk.statements)


def test_stale_version_returns_conflict_without_mutation():
    desk=FakeDesk();desk.row['VERSION']=2
    with patch('apps.api.desk.get_service',return_value=desk):
        response=client().post('/api/desk/tickets/id/updates',json={'actor':'bu','role':'Business User','version':1,'message':'hello'})
    assert response.status_code==409 and 'another session' in response.json()['detail']
    assert not any(sql.startswith('UPDATE') for sql,_ in desk.statements)


def test_clarification_requires_visible_question_and_correct_stored_status():
    with patch('apps.api.desk.get_service',return_value=FakeDesk()):
        body={'actor':'engineer','role':'Data Team','version':1,'entry_type':'CLARIFICATION_REQUEST'}
        assert client().post('/api/desk/tickets/id/updates',json=body).status_code==422
        assert client().post('/api/desk/tickets/id/updates',json={**body,'message':'Question','internal':True}).status_code==422
        assert client().post('/api/desk/tickets/id/updates',json={**body,'entry_type':'STATUS_UPDATE','changes':{'STATUS':'WAITING_FOR_BU'},'message':'question'}).status_code==422


def test_react_build_is_separate_from_intelligence():
    if not (DIST/'desk.html').exists():
        assert client().get('/desk').status_code==503
        return
    assert client().get('/desk').status_code==200
    assert '<title>Tune Data Service Desk</title>' in client().get('/desk').text
    assert '<title>Tune Data Service Desk</title>' not in client().get('/').text
    assert client().get('/api/desk/meta').json()['notice'].endswith('not authentication or authorization.')


def test_desk_write_obeys_existing_same_origin_guard():
    with patch('apps.api.desk.get_service') as service:
        response=client().post('/api/desk/tickets',json=new_body(),headers={'origin':'https://unrelated.example'})
    assert response.status_code==403 and not service.called


def test_update_unknown_fields_and_null_status_are_rejected():
    body={'actor':'bu','role':'Business User','version':1,'entry_type':'STATUS_UPDATE'}
    with patch('apps.api.desk.get_service') as service:
        assert client().post('/api/desk/tickets/id/updates',json={**body,'changes':{'TICKET_NUMBER':123}}).status_code==422
        assert client().post('/api/desk/tickets/id/updates',json={**body,'changes':{'STATUS':None}}).status_code==422
        assert client().post('/api/desk/tickets/id/updates',json=body).status_code==422
        assert not service.called
