"""Final read-only reconciliation and filter/AI API checks; not browser QA."""
import json
from decimal import Decimal
from pathlib import Path
import urllib.request
from urllib.parse import urlencode

from shared.business_logic import GOLD
from shared.snowflake_service import get_service

BASE='http://127.0.0.1:8000'
ROOT=Path(__file__).resolve().parents[1]
results={}


def request(path,body=None):
    req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),
                               headers={} if body is None else {'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as response:
        assert response.status==200
        return json.load(response)


def dec(value):
    return Decimal(str(value))


request('/api/refresh',{})
s=get_service()
scope={'start':'2026-01-01','end':'2026-10-01','line':'All','channel':'All'}
for line,channel in [('All','All'),('Motor','Agency'),('Travel','Direct Online')]:
    current=scope|{'line':line,'channel':channel}
    payload=request('/api/finance?'+urlencode(current))
    total=next(row for row in payload['rows'] if row['LEVEL']=='TOTAL')
    where="ACCOUNTING_MONTH BETWEEN ? AND ? AND LINE_OF_BUSINESS IN ('Motor','Travel')"
    params=[scope['start'],scope['end']]
    for field,value in [('LINE_OF_BUSINESS',line),('DISTRIBUTION_CHANNEL',channel)]:
        if value!='All': where+=' AND '+field+'=?';params.append(value)
    actual=s.query(f'SELECT SUM(GROSS_WRITTEN_PREMIUM) GWP,COUNT(*) N FROM {GOLD}.GI_ENTERPRISE_WIDE_MART WHERE {where}',params).iloc[0]
    plan=s.query(f'SELECT SUM(PLAN_GROSS_WRITTEN_PREMIUM) GWP,COUNT(*) N FROM {GOLD}.GI_PLAN_MONTHLY WHERE {where}',params).iloc[0]
    assert dec(total['GWP'])==actual.GWP and dec(total['PLAN_GWP'])==plan.GWP
    assert dec(total['GWP_VARIANCE'])==actual.GWP-plan.GWP
    brief=request('/api/explain',{'module':'EXEC','scope':current,'ai':line=='Motor'})
    assert brief['facts']==payload['brief']['facts']
    assert all(type(i) is int and 0<=i<len(brief['facts']) for i in brief['ids'])
    assert 'causes' not in brief['finding']
    results[line+'/'+channel]={'GWP':str(actual.GWP),'PLAN_GWP':str(plan.GWP),
                            'variance':str(actual.GWP-plan.GWP),'actual_rows':int(actual.N),
                            'plan_rows':int(plan.N),'brief_source':brief['source']}
    if line=='All':
        baseline=json.loads((ROOT/'validation/data_inspection.json').read_text(encoding='utf-8-sig'))
        history={}
        for table,column,index in [('GI_ENTERPRISE_WIDE_MART','GROSS_WRITTEN_PREMIUM',6),('GI_PLAN_MONTHLY','PLAN_GROSS_WRITTEN_PREMIUM',7)]:
            live=s.query(f'SELECT ACCOUNTING_MONTH,LINE_OF_BUSINESS,COUNT(*) N,SUM({column}) GWP FROM {GOLD}.{table} WHERE {where} GROUP BY ACCOUNTING_MONTH,LINE_OF_BUSINESS',params)
            old={(r['ACCOUNTING_MONTH'][:10],r['LINE_OF_BUSINESS']):r for r in baseline[index]}
            differences=[];prior=Decimal(0);now=Decimal(0)
            for _,row in live.iterrows():
                key=(str(row.ACCOUNTING_MONTH)[:10],row.LINE_OF_BUSINESS);saved=old[key]
                prior+=dec(saved['GWP']);now+=row.GWP
                if row.GWP!=dec(saved['GWP']):
                    differences.append({'month':key[0],'line':key[1],'prior':str(saved['GWP']),
                        'current':str(row.GWP),'difference':str(row.GWP-dec(saved['GWP'])),
                        'prior_rows':saved['N'],'current_rows':int(row.N)})
            history[table]={'prior_total':str(prior),'current_total':str(now),
                            'source_delta':str(now-prior),'differences':differences}
        latest=json.loads((ROOT/'validation/gwp_investigation.json').read_text(encoding='utf-8'))
        history['matches_recent_reconciliation']=(str(actual.GWP)==latest['direct_GWP'] and str(plan.GWP)==latest['current_PLAN_GWP'])
        history['conclusion']='Direct source sums and API agree for identical filters. Any earlier differences are saved source-aggregate differences, not display rounding; this check cannot identify who changed records or why.'
        results['snapshot_investigation']=history

results['mutations']='NONE: independent SELECT aggregates and existing cache/AI APIs only; no GOLD or financial formula changes'
(ROOT/'validation/executive_final_reconciliation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
