"""Product-agnostic presentation uses recorded candidates, never inferred offers."""
from unittest.mock import patch
import pandas as pd
import pytest
from shared.business_logic import customer_query, CANDIDATE_WHERE, customer_evidence
from shared.product_opportunities import opportunity_query, candidate_product, product_evidence
from shared.customer_presentation import unified_profile
from tests.test_customer_consolidation import customer


@pytest.mark.parametrize('product',['Motor','Travel','Fire','Personal Accident','Source product'])
def test_candidate_comes_from_source_and_retention_stays_first(product):
    row=customer();row.update(NEXT_BEST_PRODUCT=product,HOLDS_MOTOR='No')
    assert candidate_product(row)==product
    finding,facts,action=product_evidence(row)
    assert product in finding and product in facts[0]
    assert action.startswith('Review retention needs first')
    profile=unified_profile(row,True,product_agnostic=True)
    assert profile['retention']['facts']==customer_evidence(row,'NBA')[1]
    assert profile['combined']['action'].startswith(profile['retention']['action'])
    if product not in ('Motor','Travel'):
        assert 'Holdings for this candidate product are not available' in facts[0]


@pytest.mark.parametrize('changes',[
    {'NEXT_BEST_PRODUCT':None},{'NEXT_BEST_PRODUCT':'  '},{'NEXT_BEST_PRODUCT':'None'},
    {'NEXT_BEST_PRODUCT':' n/a '},{'NEXT_BEST_PRODUCT':'no recommendation'},
    {'MARKETING_CONSENT':'No'},{'MARKETING_CONSENT':None},
    {'NEXT_BEST_PRODUCT':'Motor','HOLDS_MOTOR':'Yes'},
    {'NEXT_BEST_PRODUCT':'Travel','HOLDS_TRAVEL':'Yes'},
    {'NEXT_BEST_PRODUCT':'Travel','HOLDS_TRAVEL':None},
])
def test_absent_unconsented_and_already_held_products_never_become_offers(changes):
    row=customer();row.update(changes)
    assert candidate_product(row) is None
    with pytest.raises(ValueError):product_evidence(row)


def test_product_filters_are_bound_and_nbo_order_is_reused_exactly():
    sql,params=opportunity_query('High','Top','Agency','Motor',"Travel';--")
    legacy,_=customer_query('NBO')
    assert sql[sql.index('ORDER BY'):]==legacy[legacy.index('ORDER BY'):]
    assert params==['Motor',"Travel';--",'High','Top','Agency',200]
    assert "Travel';--" not in sql
    assert 'COUNT(*) OVER()' in sql and "MARKETING_CONSENT='Yes'" in sql
    assert CANDIDATE_WHERE in legacy


def test_generalized_api_uses_full_aggregates_and_filter_scope_for_briefs():
    from fastapi.testclient import TestClient
    from apps.api.main import app
    row=customer();row.update(NEXT_BEST_PRODUCT='Fire',HOLDS_TRAVEL='Yes',FILTERED_TOTAL=1)
    overview=pd.DataFrame([
        dict(RETENTION_RISK_BAND='High',LIFETIME_VALUE_BAND='Top',PREFERRED_CHANNEL='Agency',EXISTING_HOLDING='Motor + Travel',CANDIDATE_PRODUCT='Fire',CUSTOMERS=6),
        dict(RETENTION_RISK_BAND='Low',LIFETIME_VALUE_BAND='High',PREFERRED_CHANNEL='Agency',EXISTING_HOLDING='Motor',CANDIDATE_PRODUCT='Travel',CUSTOMERS=20)])
    def read(kind,*args):
        if kind=='health':return dict(ROW_COUNT=100,CUSTOMERS=100,SNAPSHOT_MIN='2026-10-31',SNAPSHOT_MAX='2026-10-31')
        if kind=='opportunity_overview':return overview
        if kind=='opportunity_customers':
            assert args==('All','All','All','Motor + Travel','Fire')
            return pd.DataFrame([row])
        raise AssertionError((kind,args))
    with patch('apps.api.main.read',side_effect=read):
        client=TestClient(app)
        response=client.get('/api/customer-intelligence',params={'view':'CROSS_SELL','holding':'Motor + Travel','product':'Fire'})
        assert response.status_code==200
        data=response.json()
        assert data['counts']['total']==26 and data['filtered_total']==1
        assert data['options']['product']==['Fire'] and data['options']['holding']==['Motor + Travel']
        assert data['rows'][0]['CANDIDATE_PRODUCT']=='Fire'
        assert data['profiles']['C1']['product']=='Fire'
        body=dict(view='CROSS_SELL',customer_id='C1',holding='Motor + Travel',product='Fire',ai=False)
        result=client.post('/api/customer-intelligence/brief',json=body)
        assert result.status_code==200 and 'Fire' in result.json()['action']
        with patch('apps.api.main.get_service') as service:
            service.return_value.explain.return_value=[999]
            body['ai']=True
            fallback=client.post('/api/customer-intelligence/brief',json=body)
            assert 'response rejected' in fallback.json()['source']
            assert fallback.json()['facts']==result.json()['facts']
        body['customer_id']='not-listed'
        assert client.post('/api/customer-intelligence/brief',json=body).status_code==404
