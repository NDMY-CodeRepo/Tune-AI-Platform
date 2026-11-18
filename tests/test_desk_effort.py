"""Stateful service tests for the approval gate, revision identity and rollback."""
from copy import deepcopy
from datetime import datetime, timezone
import re
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from shared.snowflake_service import SnowflakeService
from shared.desk_approval import valid_effort_approval


class MemoryDesk(SnowflakeService):
    """Storage-only double; all workflow decisions execute the real service."""
    def __init__(self):
        super().__init__(None)
        self.row=dict(TICKET_ID='id',TICKET_NUMBER=1,REQUESTER='bu',VERSION=1,STATUS='NEW',
            ASSIGNED_TO=None,CONFIRMED_PRIORITY=None,RESOLUTION_NOTES=None,EFFORT_ESTIMATE=None,
            ASSESSMENT_NOTES=None,EFFORT_ASSESSMENT_VERSION=None,ASSESSED_BY=None,ASSESSED_AT=None,
            APPROVAL_DECISION=None,APPROVAL_ASSESSMENT_VERSION=None,APPROVAL_DECIDED_BY=None,
            APPROVAL_DECIDED_AT=None,APPROVAL_COMMENTS=None)
        self.history=[];self.backup=None;self.fail_activity=False
    def query(self,sql,params=None):
        if sql=='BEGIN TRANSACTION':
            self.backup=deepcopy((self.row,self.history))
        elif sql=='ROLLBACK':
            self.row,self.history=self.backup
        elif sql=='COMMIT':
            self.backup=None
        elif sql.startswith('SELECT *'):
            if 'AND REQUESTER=?' in sql and params[-1]!=self.row['REQUESTER']:
                return pd.DataFrame()
            return pd.DataFrame([deepcopy(self.row)])
        elif sql.startswith('UPDATE'):
            if params[-2:]!=[self.row['VERSION'],self.row['STATUS']]:
                return pd.DataFrame([{'rows':0}])
            index=0
            for assignment in sql.split(' SET ',1)[1].split(' WHERE ',1)[0].split(','):
                key,rhs=assignment.strip().split('=',1)
                if rhs=='?':
                    value=params[index];index+=1
                    if key in ('EFFORT_ASSESSMENT_VERSION','APPROVAL_ASSESSMENT_VERSION') and value is not None:
                        value=int(value)
                    self.row[key]=value
                elif rhs=='VERSION+1':
                    self.row[key]+=1
            return pd.DataFrame([{'rows':1}])
        return pd.DataFrame([{'rows':1}])
    def _activity(self,tid,actor,role,kind,message,internal=False):
        if self.fail_activity:
            raise RuntimeError('activity failed')
        self.history.append(dict(kind=kind,actor=actor,role=role,message=message,internal=internal))


def change(s,role='Data Team',**kwargs):
    s.change_ticket('id',s.row['VERSION'],'engineer' if role=='Data Team' else 'bu',role,entry_type='STATUS_UPDATE',**kwargs)


def triage(s):
    change(s,changes={'STATUS':'TRIAGED','ASSIGNED_TO':'engineer','CONFIRMED_PRIORITY':'HIGH'})


def submit(s):
    change(s,changes={'EFFORT_ESTIMATE':'M','ASSESSMENT_NOTES':'Data mapping, development and validation.'},effort_action='SUBMIT')


def approve(s):
    change(s,'Business User',effort_action='APPROVE',assessment_version=s.row['EFFORT_ASSESSMENT_VERSION'],confirmed=True)


def assessed():
    s=MemoryDesk();triage(s);submit(s);return s


def approved():
    s=assessed();approve(s);return s


def test_assessment_approval_start_clarification_resolve_close():
    s=assessed()
    assert s.row['STATUS']=='AWAITING_BU_APPROVAL' and s.row['EFFORT_ESTIMATE']=='M'
    assert s.row['ASSESSED_BY']=='engineer' and s.row['ASSESSED_AT']
    assert {'EFFORT_ASSESSED','EFFORT_SUBMITTED','APPROVAL_REQUESTED'}<={x['kind'] for x in s.history}
    approve(s);assert valid_effort_approval(s.row) and s.row['STATUS']=='APPROVED'
    change(s,changes={'STATUS':'IN_PROGRESS'})
    s.change_ticket('id',s.row['VERSION'],'engineer','Data Team',entry_type='CLARIFICATION_REQUEST',message='Which reporting month?')
    assert s.row['STATUS']=='WAITING_FOR_BU'
    s.change_ticket('id',s.row['VERSION'],'bu','Business User',entry_type='CLARIFICATION_RESPONSE',message='October',resume=True)
    assert s.row['STATUS']=='IN_PROGRESS'
    change(s,changes={'STATUS':'RESOLVED','RESOLUTION_NOTES':'Completed'})
    change(s,'Business User',changes={'STATUS':'CLOSED'})
    assert s.row['STATUS']=='CLOSED'


@pytest.mark.parametrize('status',['TRIAGED','APPROVED','AWAITING_BU_APPROVAL','WAITING_FOR_BU','RESOLVED'])
def test_unapproved_start_or_resume_is_rejected_even_for_legacy_rows(status):
    s=MemoryDesk();s.row.update(STATUS=status,ASSIGNED_TO='engineer',CONFIRMED_PRIORITY='HIGH',RESOLUTION_NOTES='old resolution')
    with pytest.raises(ValueError,match='approval'):
        change(s,changes={'STATUS':'IN_PROGRESS'})
    assert s.row['STATUS']==status and s.row['VERSION']==1


@pytest.mark.parametrize('role',['Data Team','Business User'])
def test_raw_status_cannot_forge_approval(role):
    s=assessed()
    with pytest.raises(ValueError):
        change(s,role,changes={'STATUS':'APPROVED'})
    assert s.row['STATUS']=='AWAITING_BU_APPROVAL'


def test_rejection_reason_confirmation_and_resubmission():
    s=assessed();before=deepcopy(s.row)
    for kwargs in [dict(effort_action='REJECT',confirmed=True),dict(effort_action='APPROVE',confirmed=False)]:
        with pytest.raises(ValueError):
            change(s,'Business User',assessment_version=s.row['EFFORT_ASSESSMENT_VERSION'],**kwargs)
        assert s.row==before
    change(s,'Business User',effort_action='REJECT',assessment_version=s.row['EFFORT_ASSESSMENT_VERSION'],confirmed=True,message='Please reduce scope.')
    assert s.row['STATUS']=='REJECTED' and s.row['APPROVAL_COMMENTS']=='Please reduce scope.'
    assert s.history[-1]['kind']=='EFFORT_REJECTED' and s.history[-1]['actor']=='bu'
    with pytest.raises(ValueError):change(s,changes={'STATUS':'IN_PROGRESS'})
    with pytest.raises(ValueError):change(s,effort_action='SUBMIT')
    with pytest.raises(ValueError):change(s,changes={'STATUS':'TRIAGED'})
    change(s,effort_action='REASSESS');submit(s);approve(s)
    change(s,changes={'STATUS':'IN_PROGRESS'})
    assert s.row['STATUS']=='IN_PROGRESS'


@pytest.mark.parametrize('field,value',[('EFFORT_ESTIMATE','L'),('ASSESSMENT_NOTES','Revised scope and validation.')])
@pytest.mark.parametrize('started',[False,True])
def test_revised_size_or_notes_invalidates_approval_and_returns_to_triage(field,value,started):
    s=approved()
    if started:change(s,changes={'STATUS':'IN_PROGRESS'})
    old_revision=s.row['EFFORT_ASSESSMENT_VERSION']
    change(s,changes={field:value})
    assert s.row['STATUS']=='TRIAGED' and not valid_effort_approval(s.row)
    assert s.row['EFFORT_ASSESSMENT_VERSION']>old_revision
    assert all(s.row[k] is None for k in ['APPROVAL_DECISION','APPROVAL_ASSESSMENT_VERSION','APPROVAL_DECIDED_BY','APPROVAL_DECIDED_AT','APPROVAL_COMMENTS'])
    assert any(x['kind']=='EFFORT_REVISED' for x in s.history)
    with pytest.raises(ValueError):change(s,changes={'STATUS':'IN_PROGRESS'})


def test_stale_assessment_cannot_be_approved_even_with_current_ticket_version():
    s=assessed();old=s.row['EFFORT_ASSESSMENT_VERSION']
    change(s,changes={'EFFORT_ESTIMATE':'L'});change(s,effort_action='SUBMIT')
    with pytest.raises(ValueError,match='assessment changed'):
        change(s,'Business User',effort_action='APPROVE',assessment_version=old,confirmed=True)
    assert s.row['STATUS']=='AWAITING_BU_APPROVAL'
    approve(s);assert valid_effort_approval(s.row)


def test_same_effort_value_preserves_approval_and_other_updates_do_not_invalidate_it():
    s=approved();version=s.row['EFFORT_ASSESSMENT_VERSION']
    change(s,changes={'EFFORT_ESTIMATE':'M','TARGET_DATE':'2026-12-01'})
    assert s.row['EFFORT_ASSESSMENT_VERSION']==version and valid_effort_approval(s.row)


def test_cannot_change_effort_and_start_work_in_one_save():
    s=approved()
    with pytest.raises(ValueError):change(s,changes={'EFFORT_ESTIMATE':'L','STATUS':'IN_PROGRESS'})
    assert s.row['STATUS']=='APPROVED' and s.row['EFFORT_ESTIMATE']=='M'


@pytest.mark.parametrize('changes',[{'EFFORT_ESTIMATE':'S'},{'ASSESSMENT_NOTES':'Changed'}, {'APPROVAL_DECISION':'APPROVED'}, {'APPROVAL_ASSESSMENT_VERSION':1},{'ASSESSED_BY':'forged'}])
def test_requester_cannot_edit_assessment_or_forge_approval_fields(changes):
    s=assessed()
    with pytest.raises(ValueError):change(s,'Business User',changes=changes)
    assert s.row['STATUS']=='AWAITING_BU_APPROVAL'


def test_team_cannot_decide_and_other_requester_cannot_approve():
    s=assessed()
    with pytest.raises(ValueError):change(s,effort_action='APPROVE',assessment_version=1,confirmed=True)
    with pytest.raises(ValueError):
        s.change_ticket('id',s.row['VERSION'],'someone.else','Business User',effort_action='APPROVE',assessment_version=1,confirmed=True)


def test_assessment_and_decision_failures_rollback_row_and_audit():
    s=assessed();before=deepcopy((s.row,s.history));s.fail_activity=True
    with pytest.raises(RuntimeError):approve(s)
    assert (s.row,s.history)==before


def test_legacy_in_progress_row_can_still_receive_comments_and_resolve():
    s=MemoryDesk();s.row.update(STATUS='IN_PROGRESS',ASSIGNED_TO='engineer',CONFIRMED_PRIORITY='HIGH')
    change(s,message='Preserved legacy work update')
    change(s,changes={'STATUS':'RESOLVED','RESOLUTION_NOTES':'Legacy work completed'})
    assert s.row['STATUS']=='RESOLVED' and not valid_effort_approval(s.row)


def test_http_requires_explicit_confirmation_and_exact_assessment_revision():
    s=assessed();client=TestClient(app)
    body=dict(actor='bu',role='Business User',version=s.row['VERSION'],effort_action='APPROVE',entry_type='STATUS_UPDATE',assessment_version=1)
    with patch('apps.api.desk.get_service',return_value=s):
        assert client.post('/api/desk/tickets/id/updates',json=body).status_code==422
        assert client.post('/api/desk/tickets/id/updates',json={**body,'confirmed':True,'assessment_version':2}).status_code==422
        assert client.post('/api/desk/tickets/id/updates',json={**body,'confirmed':True,'changes':{'APPROVAL_DECISION':'APPROVED'}}).status_code==422
    assert s.row['STATUS']=='AWAITING_BU_APPROVAL'
