"""Read-only management reconciliation and Streamlit runtime checks (not browser QA)."""
import ast
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from shared.business_logic import GOLD, NET_INCURRED, LOSS_RATIO
from shared.executive_analytics import analytics_query, ranked_variance, TREND_METRICS
from shared.snowflake_service import get_service, read, SnowflakeService

ROOT=Path(__file__).resolve().parents[1]
s=get_service()
results={}


def equal(a,b,tolerance=.000001):
    assert (pd.isna(a) and pd.isna(b)) or abs(float(a)-float(b))<tolerance,(a,b)


cases=[('2026-01-01','2026-10-01','All','All'),
       ('2026-01-01','2026-10-01','Motor','Agency'),
       ('2026-03-01','2026-05-01','Travel','Direct Online'),
       ('2026-10-01','2026-10-01','All','All'),
       ('2026-01-01','2026-10-01','Motor','not-a-channel')]
for start,end,line,channel in cases:
    data=s.finance(start,end,line,channel,analytics=True)
    original=s.finance(start,end,line,channel)
    pd.testing.assert_frame_equal(data[original.columns].reset_index(drop=True),original.reset_index(drop=True))
    if data.empty:
        results[' / '.join([start,end,line,channel])]='PASS: empty selection remains empty'
        continue
    if line=='All' and channel=='All' and start=='2026-01-01':
        results['overview_snapshot']={k:str(data.loc[data.LEVEL.eq('TOTAL')].iloc[0][k]) for k in ['GWP','PLAN_GWP','NEP','NET_INCURRED_CLAIMS','LOSS_RATIO']}
    where="ACCOUNTING_MONTH BETWEEN ? AND ? AND LINE_OF_BUSINESS IN ('Motor','Travel')"
    params=[start,end]
    for field,value in [('LINE_OF_BUSINESS',line),('DISTRIBUTION_CHANNEL',channel)]:
        if value!='All':
            where+=' AND '+field+'=?'; params.append(value)
    for level,dimension in [('TOTAL',None),('MONTH','ACCOUNTING_MONTH'),('LINE','LINE_OF_BUSINESS'),('CHANNEL','DISTRIBUTION_CHANNEL')]:
        select=(dimension+',' if dimension else '')
        group=(' GROUP BY '+dimension if dimension else '')
        source=s.query(f'SELECT {select} SUM(GROSS_WRITTEN_PREMIUM) GWP,SUM(NET_EARNED_PREMIUM) NEP,'
            f'{NET_INCURRED} NET_INCURRED_CLAIMS,{LOSS_RATIO} LOSS_RATIO FROM {GOLD}.GI_ENTERPRISE_WIDE_MART WHERE {where}{group}',params)
        plan=s.query(f'SELECT {select} SUM(PLAN_GROSS_WRITTEN_PREMIUM) PLAN_GWP,SUM(PLAN_NET_EARNED_PREMIUM) PLAN_NEP '
                     f'FROM {GOLD}.GI_PLAN_MONTHLY WHERE {where}{group}',params)
        rows=data.loc[data.LEVEL.eq(level)]
        for _,row in rows.iterrows():
            actual=source if not dimension else source.loc[source[dimension].eq(row[dimension])]
            planned=plan if not dimension else plan.loc[plan[dimension].eq(row[dimension])]
            assert len(actual)==1 and len(planned)==1
            for field in ['GWP','NEP','NET_INCURRED_CLAIMS','LOSS_RATIO']:
                equal(row[field],actual.iloc[0][field])
            for metric in ['GWP','NEP']:
                equal(row['PLAN_'+metric],planned.iloc[0]['PLAN_'+metric])
                if pd.notna(row[metric+'_VARIANCE']):
                    equal(row[metric+'_VARIANCE'],row[metric]-row['PLAN_'+metric])
                if level in ('LINE','CHANNEL') and pd.notna(row[metric+'_SHARE']):
                    equal(row[metric+'_SHARE'],row[metric]/sum(source[metric]),1e-7)
        if level in ('LINE','CHANNEL') and not rows.empty:
            for metric in ['GWP','NEP']:
                if rows[metric+'_SHARE'].notna().all():
                    equal(sum(rows[metric+'_SHARE']),1,1e-7)
    results[' / '.join([start,end,line,channel])]='PASS: unchanged base results; direct source aggregates, variances, ratios and separate shares'

# Inline SQL fixtures exercise invalid shares and coverage without creating objects.
actual="""(SELECT TO_DATE(column1) ACCOUNTING_MONTH,'MY' ENTITY_CODE,'Motor' LINE_OF_BUSINESS,
'Agency' DISTRIBUTION_CHANNEL,column2 GROSS_WRITTEN_PREMIUM,0 NET_EARNED_PREMIUM,
10 GROSS_CLAIMS_PAID,2 OS_RESERVE_MOVEMENT,1 IBNR_MOVEMENT,3 REINSURANCE_RECOVERIES
FROM VALUES ('2026-01-01',100),('2026-02-01',200))"""
plan="""(SELECT TO_DATE(column1) ACCOUNTING_MONTH,'MY' ENTITY_CODE,'Motor' LINE_OF_BUSINESS,
'Agency' DISTRIBUTION_CHANNEL,column2 PLAN_GROSS_WRITTEN_PREMIUM,0 PLAN_NET_EARNED_PREMIUM,
15 PLAN_INCURRED_CLAIMS FROM VALUES ('2026-01-01',0),('2026-03-01',60))"""
sql,params=analytics_query('2026-01-01','2026-03-01')
fixture=sql.replace(GOLD+'.GI_ENTERPRISE_WIDE_MART',actual).replace(GOLD+'.GI_PLAN_MONTHLY',plan)
for name,query in [('missing coverage',fixture),('null premium',fixture.replace("('2026-02-01',200)","('2026-02-01',NULL)")),
                   ('negative premium',fixture.replace("('2026-02-01',200)","('2026-02-01',-200)"))]:
    data=s.query(query,params)
    total=data.loc[data.LEVEL.eq('TOTAL')].iloc[0]
    assert pd.isna(total.GWP_VARIANCE) and pd.isna(total.LOSS_RATIO)
    assert ranked_variance(data,'LINE','GWP')[0].empty
    rows=data.loc[data.LEVEL.isin(['LINE','CHANNEL'])]
    assert rows.NEP_SHARE.isna().all()
    if name!='missing coverage':
        assert rows.GWP_SHARE.isna().all()
results['SQL edge fixtures']='PASS: missing keys excluded; null/negative premiums, zero-denominator shares and ratios unavailable'

read.clear()
a=AppTest.from_file(str(ROOT/'apps/ai-intelligence/app.py'),default_timeout=90).run()
def clean():
    assert not a.exception, a.exception
    assert not a.error,[x.value for x in a.error]
clean()
for measure in TREND_METRICS:
    a.selectbox(key='exec-trend').set_value(measure).run(); clean()
    charts=a.get('plotly_chart')
    figure=json.loads(charts[0].proto.spec)
    assert [trace['name'] for trace in figure['data']]==(['Actual','Plan'] if 'vs Plan' in measure else ['Actual'])
for metric in ['NEP','GWP']:
    a.selectbox(key='exec-variance').set_value(metric).run(); clean()
    a.selectbox(key='exec-mix').set_value(metric).run(); clean()
with patch.object(SnowflakeService,'explain',return_value=[3,4]) as explain:
    a.button(key='EXEC').click().run(); clean()
    assert explain.call_count==1
assert any('AI-curated' in c.value for c in a.caption)
line_filter=next(x for x in a.selectbox if x.label=='Business line')
line_filter.set_value('Travel').run(); clean()
assert not any('AI-curated' in c.value for c in a.caption)  # changed filter invalidates saved insight
with patch.object(SnowflakeService,'explain',side_effect=RuntimeError('offline')):
    a.button(key='EXEC').click().run(); clean()
assert any('Cortex unavailable' in c.value for c in a.caption)
a.selectbox(key='finance_start').set_value(a.selectbox(key='finance_end').value).run(); clean()
for key in ['nav-nba','nav-nbo']:
    a.button(key=key).click().run(); clean()
results['Streamlit AppTest']='PASS: four trends, both variance/mix bases, filtered and single-month rendering, bounded AI success/fallback, NBA/NBO navigation; not browser screenshots'

baseline=json.loads((ROOT/'validation/management_dashboard_baseline.json').read_text())
tree=ast.parse((ROOT/'apps/ai-intelligence/app.py').read_text(encoding='utf-8'))
for name,expected in baseline['preserved_functions'].items():
    source_tree=ast.parse((ROOT/'shared/insight_facts.py').read_text(encoding='utf-8')) if name=='financial_narrative' else tree
    node=next(n for n in source_tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    assert ast.dump(node)==expected,name
assert hashlib.sha256((ROOT/'shared/business_logic.py').read_bytes()).hexdigest()==baseline['file_hashes']['shared/business_logic.py']
results['Preservation']='PASS: customer_page, explanation and financial_narrative AST unchanged; read-only SELECT queries only'
out=ROOT/'validation/management_analytics.json'
out.write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
