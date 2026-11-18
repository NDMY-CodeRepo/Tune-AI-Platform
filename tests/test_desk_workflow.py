"""Workflow contract and mutation failure tests. Live Snowflake coverage is separate."""
from contextlib import contextmanager
from threading import RLock
from unittest.mock import patch
import pandas as pd
import pytest
from shared.desk_rules import (STATUSES,TRANSITIONS,validate_ticket_change,validate_request,reference,safe_link)
from shared.snowflake_service import SnowflakeService

EDGES={('NEW','TRIAGED'),('TRIAGED','AWAITING_BU_APPROVAL'),
       ('AWAITING_BU_APPROVAL','APPROVED'),('AWAITING_BU_APPROVAL','REJECTED'),
       ('APPROVED','IN_PROGRESS'),('REJECTED','TRIAGED'),('IN_PROGRESS','WAITING_FOR_BU'),
       ('WAITING_FOR_BU','IN_PROGRESS'),('IN_PROGRESS','RESOLVED'),('RESOLVED','CLOSED'),('RESOLVED','IN_PROGRESS')}

@pytest.mark.parametrize('old',STATUSES)
@pytest.mark.parametrize('new',STATUSES)
def test_every_status_pair(old,new):
    if old==new or (old,new) in EDGES:
        validate_ticket_change(old,new,'engineer','resolution')
    else:
        with pytest.raises(ValueError):
            validate_ticket_change(old,new,'engineer','resolution')

@pytest.mark.parametrize('status',STATUSES[1:])
def test_non_new_status_requires_owner(status):
    with pytest.raises(ValueError,match='owner'):
        validate_ticket_change(status,status,'','resolution')

@pytest.mark.parametrize('status',['RESOLVED','CLOSED'])
def test_resolution_is_required_on_same_status_save(status):
    with pytest.raises(ValueError,match='Resolution'):
        validate_ticket_change(status,status,'engineer','')

@pytest.mark.parametrize('field',['CONFIRMED_PRIORITY','ASSIGNED_TO','STATUS','is_demo','ticket_number'])
def test_request_creation_rejects_team_fields(field):
    with pytest.raises(ValueError):
        validate_request('Motor','user','title','details','REPORT_REQUEST','HIGH','reason',{field:'tampered'})

@pytest.mark.parametrize('url',['javascript:alert(1)','file:///secret','data:text/html,hello','https:///broken',None])
def test_links_reject_unsafe_schemes(url):
    assert not safe_link(url)


def test_reference_grows_without_truncation():
    assert reference(123)=='TDS-000123'
    assert reference(1000000)=='TDS-1000000'


class FakeDesk(SnowflakeService):
    def __init__(self):
        super().__init__(None)
        self.statements=[]
        self.row={'TICKET_ID':'id','REQUESTER':'bu','VERSION':1,'STATUS':'IN_PROGRESS',
                  'ASSIGNED_TO':'engineer','RESOLUTION_NOTES':None,'CONFIRMED_PRIORITY':'HIGH'}
        self.fail_activity=False
    def query(self,sql,params=None):
        self.statements.append((sql,params))
        if sql.startswith('SELECT *'):
            if 'AND REQUESTER=?' in sql and params[-1]!='bu':
                return pd.DataFrame()
            return pd.DataFrame([self.row])
        if sql.startswith('UPDATE'):
            return pd.DataFrame([{'rows':1}])
        if 'INSERT INTO' in sql and self.fail_activity:
            raise RuntimeError('History insert failed')
        return pd.DataFrame([{'rows':1}])


def test_failed_history_rolls_back_ticket_mutation():
    s=FakeDesk();s.fail_activity=True
    with pytest.raises(RuntimeError,match='History'):
        s.change_ticket('id',1,'engineer','Data Team',changes={'STATUS':'RESOLVED','RESOLUTION_NOTES':'done'},entry_type='STATUS_UPDATE')
    assert s.statements[-1][0]=='ROLLBACK'
    assert not any(sql=='COMMIT' for sql,_ in s.statements)


def test_client_status_cannot_bypass_stored_state():
    s=FakeDesk()
    with pytest.raises(ValueError):
        s.update_ticket('id',1,'RESOLVED','CLOSED','engineer','','done')
    assert not any(sql.startswith('UPDATE') for sql,_ in s.statements)

@pytest.mark.parametrize('changes',[{'ASSIGNED_TO':'hijack'},{'CONFIRMED_PRIORITY':'LOW'},{'STATUS':'RESOLVED'},{'DELIVERED_REFERENCE':'fake'}])
def test_requester_cannot_mutate_team_fields(changes):
    s=FakeDesk()
    with pytest.raises(ValueError):
        s.change_ticket('id',1,'bu','Business User',changes=changes,entry_type='STATUS_UPDATE')
    assert not any(sql.startswith('UPDATE') for sql,_ in s.statements)


def test_stale_comment_is_rejected():
    s=FakeDesk()
    with pytest.raises(ValueError,match='another session'):
        s.change_ticket('id',0,'bu','Business User',message='hello')


def test_clarification_cannot_be_bypassed_or_hidden():
    s=FakeDesk()
    for kwargs in [dict(changes={'STATUS':'WAITING_FOR_BU'},entry_type='STATUS_UPDATE'),
                   dict(entry_type='CLARIFICATION_REQUEST',message='question',internal=True)]:
        with pytest.raises(ValueError):
            s.change_ticket('id',1,'engineer','Data Team',**kwargs)
    assert not any(sql.startswith('UPDATE') for sql,_ in s.statements)


def test_other_requester_cannot_read_history():
    with pytest.raises(ValueError):
        FakeDesk().activity('id','someone.else')
