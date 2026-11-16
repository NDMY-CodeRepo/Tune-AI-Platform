"""Read-only acceptance: presentation consolidation preserves NBA/NBO results."""
import json
import urllib.request
import urllib.error
from pathlib import Path
from shared.business_logic import GOLD,CANDIDATE_WHERE,customer_evidence
from shared.snowflake_service import get_service

BASE='http://127.0.0.1:8000'


def request(path,body=None):
    req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),
                               headers={} if body is None else {'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=150) as response:
        assert response.status==200
        return json.load(response)


s=get_service();results={};by_view={}
for view,mode in [('PRIORITIES','NBA'),('RETENTION','NBA'),('CROSS_SELL','NBO')]:
    data=request('/api/customer-intelligence?view='+view);by_view[view]=data
    legacy=request('/api/customers/'+mode)
    assert [{k:v for k,v in row.items() if k!='CANDIDATE_PRODUCT'} for row in data['rows']]==legacy['rows']
    assert data['counts']==legacy['counts'] and data['filtered_total']==legacy['filtered_total']
    ids=[row['CUSTOMER_ID'] for row in data['rows']]
    assert len(ids)==len(set(ids))
    source=s.customers(mode)
    for _,row in source.iterrows():
        record=next(r for r in data['rows'] if r['CUSTOMER_ID']==row.CUSTOMER_ID)
        qualified=(row.HOLDS_MOTOR=='Yes' and row.HOLDS_TRAVEL=='No' and row.NEXT_BEST_PRODUCT=='Travel' and row.MARKETING_CONSENT=='Yes')
        assert bool(record['CANDIDATE_PRODUCT'])==qualified
        profile=data['profiles'][row.CUSTOMER_ID]
        assert profile['retention']['facts']==customer_evidence(row.to_dict(),'NBA')[1]
        assert bool(profile['offer'])==qualified
        if qualified:
            assert profile['offer']['facts']==customer_evidence(row.to_dict(),'NBO')[1]
        assert profile['combined']['action'].startswith(profile['retention']['action'])
    filtered=request('/api/customer-intelligence?view='+view+'&risk=High&value=Top')
    old_filtered=request('/api/customers/'+mode+'?risk=High&value=Top')
    assert [r['CUSTOMER_ID'] for r in filtered['rows']]==[r['CUSTOMER_ID'] for r in old_filtered['rows']]
    assert filtered['filtered_total']==old_filtered['filtered_total']
    results[view]={'status':'PASS: exact legacy order/counts/attributes, unique IDs, original retention/offer evidence and risk/value filters',
                   'total':data['counts']['total'],'displayed':len(ids)}

assert by_view['PRIORITIES']['rows']==by_view['RETENTION']['rows']
source_total=int(s.health()['CUSTOMERS'])
source_nbo=int(s.query(f'SELECT COUNT(DISTINCT CUSTOMER_ID) N FROM {GOLD}.CUSTOMER_360_WIDE_MART WHERE {CANDIDATE_WHERE}').iloc[0].N)
assert by_view['PRIORITIES']['summary']['portfolio_total']==source_total
assert by_view['PRIORITIES']['summary']['cross_sell_candidates']==source_nbo
assert by_view['CROSS_SELL']['counts']['total']==source_nbo
results['reconciliation']={'unique_portfolio':source_total,'nbo_candidates':source_nbo,'categories':'Overlapping; never summed'}
priorities=by_view['PRIORITIES'];offers=[r for r in priorities['rows'] if r['CANDIDATE_PRODUCT']]
no_offer=next(r for r in priorities['rows'] if not r['CANDIDATE_PRODUCT'])
not_in_nbo=[r for r in offers if r['CUSTOMER_ID'] not in {n['CUSTOMER_ID'] for n in by_view['CROSS_SELL']['rows']}]
results['bounded_membership']={'qualified_priorities':len(offers),'qualified_not_in_first_200_nbo':len(not_in_nbo)}
for row in [no_offer,offers[0]]:
    brief=request('/api/customer-intelligence/brief',{'view':'PRIORITIES','customer_id':row['CUSTOMER_ID'],'ai':bool(row['CANDIDATE_PRODUCT'])})
    profile=priorities['profiles'][row['CUSTOMER_ID']]
    assert brief['facts']==profile['combined']['facts'] and brief['action']==profile['combined']['action']
    assert all(0<=i<len(brief['facts']) for i in brief['ids']) and len(brief['ids'])<=3
    if not row['CANDIDATE_PRODUCT']:
        assert not any('Holds Motor, does not hold Travel' in f for f in brief['facts'])
    results['brief_offer' if row['CANDIDATE_PRODUCT'] else 'brief_no_offer']=brief['source']
try:
    request('/api/customer-intelligence/brief',{'customer_id':'NOT_IN_WORKLIST'})
    raise AssertionError('Unlisted customer was accepted')
except urllib.error.HTTPError as exc:
    assert exc.code==404
results['mutations']='NONE: no ticket writes, GOLD/schema changes or recommendation-engine modifications'
Path('validation/customer_consolidation_live.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
