"""Live HTTP + Snowflake read-only acceptance. No browser rendering claim."""
import json
import re
import urllib.request
from pathlib import Path

from shared.business_logic import GOLD,CANDIDATE_WHERE,customer_evidence
from shared.snowflake_service import get_service

BASE='http://127.0.0.1:8000'
results={}


def request(path,body=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type':'application/json'} if body is not None else {})
    with urllib.request.urlopen(req,timeout=150) as response:
        assert response.status==200
        return json.load(response)


assert request('/api/health')['status']=='ok'
with urllib.request.urlopen(BASE) as response:
    html=response.read().decode()
    for asset in re.findall(r'(?:src|href)="(/assets/[^"]+)"',html):
        with urllib.request.urlopen(BASE+asset) as bundled:
            assert bundled.status==200
with urllib.request.urlopen(BASE+'/tune-logo.png') as logo:
    assert logo.headers['Content-Type']=='image/png'
results['frontend']='PASS: HTML, built JS/CSS and logo served same-origin; not a browser execution test'
options=request('/api/finance/options')
months=options['months'];end=months[-1];start=next(m for m in months if m[:4]==end[:4])
s=get_service()
for line,channel in [('All','All'),('Motor','Agency')]:
    params=f'start={start}&end={end}&line={line}&channel={channel}'
    response=request('/api/finance?'+params)
    expected=json.loads(s.finance(start,end,line,channel,analytics=True).to_json(orient='records',date_format='iso'))
    assert response['rows']==expected
    brief=request('/api/explain',{'module':'EXEC','scope':{'start':start,'end':end,'line':line,'channel':channel},'ai':False})
    assert all(0<=i<len(brief['facts']) for i in brief['ids'])
    results[f'finance {line}/{channel}']='PASS: all API numeric/null/date records equal the existing validated Python query; deterministic brief works'
for mode in ['NBA','NBO']:
    response=request('/api/customers/'+mode)
    source=s.customers(mode)
    assert response['rows']==json.loads(source.to_json(orient='records',date_format='iso'))
    row=source.iloc[0].to_dict()
    finding,facts,action=customer_evidence(row,mode)
    profile=response['profiles'][row['CUSTOMER_ID']]
    assert profile['facts']==facts and profile['action']==action and profile['finding']==finding
    brief=request('/api/explain',{'module':mode,'customer_id':row['CUSTOMER_ID'],'ai':mode=='NBO'})
    assert brief['facts']==facts and all(type(i) is int and 0<=i<len(facts) for i in brief['ids'])
    assert len(brief['ids'])<=3
    filtered=request('/api/customers/'+mode+'?risk=High&value=Top')
    assert all(r['RETENTION_RISK_BAND']=='High' and r['LIFETIME_VALUE_BAND']=='Top' for r in filtered['rows'])
    results[mode]={'status':'PASS: live worklist, profile/evidence reuse, filters and server-generated brief',
                   'total':response['counts']['total'],'brief_source':brief['source']}
    if mode=='NBO':
        count=int(s.query(f'SELECT COUNT(DISTINCT CUSTOMER_ID) N FROM {GOLD}.CUSTOMER_360_WIDE_MART WHERE {CANDIDATE_WHERE}').iloc[0].N)
        assert response['counts']['total']==count
        results['NBO']['direct_sql_candidates']=count
    else:
        assert response['counts']['priority']==s.retention_priorities()['PRIORITY_CUSTOMERS']
assert request('/api/refresh',{})['status']=='refreshed'
results['refresh']='PASS: read-only cache invalidation'
results['mutations']='NONE: no database migration, writes, DDL or GOLD changes'
Path('validation/react_live_acceptance.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
