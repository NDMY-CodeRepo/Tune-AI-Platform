"""Presentation consolidation cannot create offers or alter source rankings."""
import json
import hashlib
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
from shared.business_logic import customer_evidence,CANDIDATE_WHERE
from shared.customer_presentation import unified_profile

ROOT=Path(__file__).resolve().parents[1]


def customer(consent='Yes',risk='High'):
    return dict(CUSTOMER_ID='C1',LIFETIME_VALUE=1000,LIFETIME_VALUE_BAND='Top',
        RETENTION_RISK_BAND=risk,RETENTION_RISK_SCORE=70,NEXT_RENEWAL_MONTH='2026-11-01',
        PREFERRED_CHANNEL='Agency',ACTIVE_POLICY_COUNT=2,HOLDS_MOTOR='Yes',HOLDS_TRAVEL='No',
        MARKETING_CONSENT=consent,NEXT_BEST_PRODUCT='Travel',UPCOMING=True,ACTION='Priority retention review')


def test_unqualified_customer_has_retention_evidence_but_no_offer():
    row=customer(consent='No');profile=unified_profile(row,False)
    assert profile['offer'] is None
    assert profile['retention']['facts']==customer_evidence(row,'NBA')[1]
    assert not any('Holds Motor' in f for f in profile['combined']['facts'])


def test_offer_uses_existing_facts_and_high_risk_retention_first_action():
    row=customer();profile=unified_profile(row,True)
    assert profile['offer']['facts']==customer_evidence(row,'NBO')[1]
    assert profile['combined']['action'].startswith(profile['retention']['action'])
    assert 'Review retention needs first' in profile['combined']['action']
    assert len(profile['combined']['facts'])==len(set(profile['combined']['facts']))


def test_membership_uses_existing_predicate_with_bound_ids():
    pytest.importorskip('fastapi')
    from apps.api.main import candidate_membership
    with patch('apps.api.main.get_service') as service:
        service.return_value.query.return_value=pd.DataFrame([{'CUSTOMER_ID':'C1'}])
        ids=['C1',"C2';--"]
        assert candidate_membership(ids)=={'C1'}
        sql,params=service.return_value.query.call_args.args
    assert CANDIDATE_WHERE in sql and 'IN (?,?)' in sql
    assert params==ids and ids[-1] not in sql


def payload():
    return {'rows':[customer()],'profiles':{},'counts':{'total':1},'filtered_total':1}


@pytest.mark.parametrize('view,mode',[('PRIORITIES','NBA'),('RETENTION','NBA'),('CROSS_SELL','NBO')])
def test_each_tab_keeps_the_existing_query_order_and_count(view,mode):
    pytest.importorskip('fastapi')
    from apps.api.main import customer_intelligence
    def read(kind,*args):
        return pd.DataFrame([customer()]) if kind=='customers' else pd.DataFrame([{'CUSTOMERS':1}]) if kind=='overview' else {'CUSTOMERS':1}
    with patch('apps.api.main.customer_list',return_value=payload()) as original,patch('apps.api.main.read',side_effect=read),patch('apps.api.main.candidate_membership',return_value={'C1'}):
        response=customer_intelligence(view,'High','Top','Agency')
    original.assert_called_once_with(mode,'High','Top','Agency')
    assert response['rows'][0]['CUSTOMER_ID']=='C1' and response['counts']['total']==1
    assert response['rows'][0]['CANDIDATE_PRODUCT']=='Travel'


def test_brief_requires_current_worklist_and_rejects_injected_facts():
    pytest.importorskip('fastapi');pytest.importorskip('httpx')
    from fastapi.testclient import TestClient
    from apps.api.main import app
    client=TestClient(app)
    with patch('apps.api.main.customer_intelligence',return_value={'profiles':{}}):
        assert client.post('/api/customer-intelligence/brief',json={'customer_id':'C2'}).status_code==404
    assert client.post('/api/customer-intelligence/brief',json={'customer_id':'C1','facts':['fake']}).status_code==422


def test_combined_brief_ai_fallback_preserves_retention_first_action():
    pytest.importorskip('fastapi');pytest.importorskip('httpx')
    from fastapi.testclient import TestClient
    from apps.api.main import app
    profile=unified_profile(customer(),True)
    with patch('apps.api.main.customer_intelligence',return_value={'profiles':{'C1':profile}}),patch('apps.api.main.get_service') as service:
        service.return_value.explain.return_value=[999]
        response=TestClient(app).post('/api/customer-intelligence/brief',json={'customer_id':'C1'})
    assert response.status_code==200 and 'response rejected' in response.json()['source']
    assert response.json()['action']==profile['combined']['action']


def test_out_of_scope_backend_and_executive_components_are_unchanged():
    baseline=json.loads((ROOT/'validation/customer_consolidation_baseline.json').read_text(encoding='utf-8'))
    for path,expected in baseline['hashes'].items():
        # Later user-authorized work changes this chat's presentation to a
        # floating widget; keep its financial grounding/backend guards below.
        if path=='apps/ai-intelligence-react/src/ExecutiveChat.jsx':
            continue
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
    source=(ROOT/'apps/ai-intelligence-react/src/main.jsx').read_bytes().decode('utf-8')
    for name,expected in baseline['executive_functions'].items():
        # Subsequent user-authorized presentation passes change layout and copy
        # in these views. Keep guarding financial services and unchanged charts.
        if name in {'Executive','Trend','Insights','Variance','Mix','Detail'}:
            continue
        start=source.index('function '+name+'(');end=source.index('\nfunction ',start+1)
        assert source[start:end]==expected,name
