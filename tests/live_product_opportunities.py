"""Read-only live acceptance; run as python -m tests.live_product_opportunities.

Uses the real API in process. Starts no servers and writes no Snowflake objects.
Only aggregate counts, not customer identifiers, are written to the report.
"""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from apps.api.main import app
from shared.snowflake_service import get_service
from shared.business_logic import CANDIDATE_WHERE, customer_evidence
from shared.product_opportunities import candidate_product

s=get_service(); client=TestClient(app)
source=s.query('''SELECT HOLDS_MOTOR,HOLDS_TRAVEL,NEXT_BEST_PRODUCT,MARKETING_CONSENT,
COUNT(*) CUSTOMERS FROM TUNE_BI_DB.GOLD.CUSTOMER_360_WIDE_MART GROUP BY ALL''')
expected={}
for _,r in source.iterrows():
    if not candidate_product(r.to_dict()):continue
    holding=('Motor + Travel' if r.HOLDS_MOTOR=='Yes' and r.HOLDS_TRAVEL=='Yes' else
             'Motor' if r.HOLDS_MOTOR=='Yes' else 'Travel' if r.HOLDS_TRAVEL=='Yes' else
             'No Motor / Travel recorded')
    key=(holding,r.NEXT_BEST_PRODUCT.strip())
    expected[key]=expected.get(key,0)+int(r.CUSTOMERS)

def get(**params):
    response=client.get('/api/customer-intelligence',params={'view':'CROSS_SELL',**params})
    assert response.status_code==200,response.text
    return response.json()

all_data=get()
assert all_data['counts']['total']==sum(expected.values())
assert len({r['CUSTOMER_ID'] for r in all_data['rows']})==len(all_data['rows'])
results=[];cortex=None
for (holding,product),count in sorted(expected.items()):
    data=get(holding=holding,product=product)
    assert data['filtered_total']==count
    assert data['options']['product']==sorted({p for (h,p) in expected if h==holding})
    for r in data['rows']:
        assert r['CANDIDATE_PRODUCT']==product and candidate_product(r)==product
        assert data['profiles'][r['CUSTOMER_ID']]['retention']['facts']==customer_evidence(r,'NBA')[1]
        if r['RETENTION_RISK_BAND']=='High':
            assert data['profiles'][r['CUSTOMER_ID']]['offer']['action'].startswith('Review retention needs first')
    selected=data['rows'][0]['CUSTOMER_ID']
    body={'view':'CROSS_SELL','holding':holding,'product':product,'customer_id':selected,'ai':False}
    brief=client.post('/api/customer-intelligence/brief',json=body)
    assert brief.status_code==200 and product in brief.json()['action']
    if cortex is None:
        body['ai']=True
        explanation=client.post('/api/customer-intelligence/brief',json=body)
        assert explanation.status_code==200
        assert explanation.json()['facts']==brief.json()['facts']
        assert all(0<=i<len(explanation.json()['facts']) for i in explanation.json()['ids'])
        cortex=explanation.json()['source']
    results.append({'holding':holding,'candidate_product':product,'customers':count,'status':'PASS'})

# The original Motor-to-Travel subset still reconciles including order and risk/value filters.
for risk,value in [('All','All'),('High','Top')]:
    generalized=get(holding='Motor',product='Travel',risk=risk,value=value)
    legacy=client.get('/api/customers/NBO',params={'risk':risk,'value':value}).json()
    assert generalized['counts']['total']==sum(expected.values())
    assert generalized['filtered_total']==legacy['filtered_total']
    assert [r['CUSTOMER_ID'] for r in generalized['rows']]==[r['CUSTOMER_ID'] for r in legacy['rows']]
original_count=int(s.query(f'SELECT COUNT(*) N FROM TUNE_BI_DB.GOLD.CUSTOMER_360_WIDE_MART WHERE {CANDIDATE_WHERE}').iloc[0].N)
assert expected[('Motor','Travel')]==original_count
assert get(holding='Motor',product="Travel';--")['filtered_total']==0
for view in ('PRIORITIES','RETENTION'):
    data=client.get('/api/customer-intelligence',params={'view':view}).json()
    original=client.get('/api/customers/NBA').json()
    assert data['counts']==original['counts']
    assert [r['CUSTOMER_ID'] for r in data['rows']]==[r['CUSTOMER_ID'] for r in original['rows']]

report={'status':'PASS','total_candidates':sum(expected.values()),'relationships':results,
        'legacy_motor_to_travel':original_count,'legacy_order_and_filtered_subset':'PASS',
        'retention_order_counts_and_rules':'PASS','cortex':cortex,
        'snowflake_writes':'NONE','browser':'NOT VERIFIED'}
Path('validation/product_opportunities_live.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
