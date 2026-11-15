import pytest
from shared.business_logic import customer_query, validate_ai_selection
from shared.business_logic import validate_ticket_change, customer_evidence


def test_filters_are_bound_and_limit_is_bound():
    sql, params = customer_query('NBO', risk="High' OR 1=1 --", value='Top')
    assert "High' OR" not in sql
    assert params == ["High' OR 1=1 --", 'Top', 200]
    assert 'HOLDS_MOTOR' in sql and 'COUNT(*) OVER()' in sql


@pytest.mark.parametrize('raw', [None, {}, {'evidence_ids':[-1]}, {'evidence_ids':[99]},
                                  {'evidence_ids':[True]}, {'evidence_ids':[0,0]},
                                  {'evidence_ids':[]}, {'evidence_ids':['0']}])
def test_ai_rejects_unsupported_evidence(raw):
    with pytest.raises(ValueError):
        validate_ai_selection(raw, 4)


def test_ai_preserves_verified_evidence_order():
    assert validate_ai_selection('{"evidence_ids":[2,0]}', 4) == [2,0]


@pytest.mark.parametrize('old,new,owner,notes',[
    ('NEW','RESOLVED','eng','done'),('NEW','IN_PROGRESS','',''),
    ('IN_PROGRESS','RESOLVED','eng',''),('CLOSED','IN_PROGRESS','eng','done')])
def test_invalid_ticket_transitions(old,new,owner,notes):
    with pytest.raises(ValueError):
        validate_ticket_change(old,new,owner,notes)


def test_unknown_renewal_is_not_presented_as_outside_window():
    row = {'LIFETIME_VALUE':1000,'LIFETIME_VALUE_BAND':'High','RETENTION_RISK_BAND':'High',
           'RETENTION_RISK_SCORE':70,'NEXT_RENEWAL_MONTH':None,'PREFERRED_CHANNEL':'Agency',
           'UPCOMING':None,'ACTION':'Retention review'}
    _, facts, _ = customer_evidence(row,'NBA')
    assert 'unavailable' in facts[-1]
    assert not any('outside' in f for f in facts)
