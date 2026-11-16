"""Live acceptance tests. Creates one clearly labelled persistent demo ticket."""
import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from shared.business_logic import ACTION_SQL, GOLD, LOSS_RATIO, NET_INCURRED
from shared.snowflake_service import get_service, read, SnowflakeService

ROOT = Path(__file__).resolve().parents[1]
s = get_service()
results = {}


def app():
    result = AppTest.from_file(str(ROOT/'apps/ai-intelligence/app.py'),default_timeout=90).run()
    assert not result.exception and not result.error
    return result


def clean(a):
    assert not a.exception, a.exception
    assert not a.error, [x.value for x in a.error]


nba = s.customers('NBA')
assert not nba.empty
test_rules = s.query(f"""SELECT {ACTION_SQL} ACTION,EXPECTED FROM (
    SELECT column1 RETENTION_RISK_BAND,column2 LIFETIME_VALUE_BAND,
    TO_DATE(column3) NEXT_RENEWAL_MONTH,TO_DATE('2026-10-31') SNAPSHOT_DATE,column4 EXPECTED
    FROM VALUES
    ('High','Top','2026-11-01','Priority retention review'),
    ('High','High','2027-01-01','Priority retention review'),
    ('High','Top','2027-02-01','Retention review'),
    ('High','Low','2026-11-01','Retention review'),
    ('Medium','High','2027-01-01','Proactive renewal engagement'),
    ('Medium','Top','2027-02-01','Monitor retention needs'),
    ('Low','Top','2026-11-01','Standard relationship maintenance'),
    ('High','Top','2026-10-01','Retention review'))""")
assert test_rules.ACTION.eq(test_rules.EXPECTED).all()
a = app()
a.button(key='nav-nba').click().run(); clean(a)
assert a.metric[0].value == '179,725'
a.selectbox(key='NBArisk').set_value('High').run()
a.selectbox(key='NBAvalue').set_value('Top').run(); clean(a)
a.toggle[0].set_value(False).run()
a.button(key='NBA').click().run(); clean(a)
results['NBA'] = 'PASS: live screen, filters, deterministic explanation and 8 SQL rule/window cases'

data = s.finance('2026-01-01','2026-10-01')
total = data.loc[data.LEVEL.eq('TOTAL')].iloc[0]
source = s.query(f"""SELECT SUM(GROSS_WRITTEN_PREMIUM) GWP,SUM(NET_EARNED_PREMIUM) NEP,
{NET_INCURRED} NET_INCURRED_CLAIMS,{LOSS_RATIO} LOSS_RATIO FROM {GOLD}.GI_ENTERPRISE_WIDE_MART
WHERE ACCOUNTING_MONTH BETWEEN '2026-01-01' AND '2026-10-01' AND LINE_OF_BUSINESS IN ('Motor','Travel')""").iloc[0]
plan = s.query(f"""SELECT SUM(PLAN_GROSS_WRITTEN_PREMIUM) GWP,SUM(PLAN_NET_EARNED_PREMIUM) NEP
FROM {GOLD}.GI_PLAN_MONTHLY WHERE ACCOUNTING_MONTH BETWEEN '2026-01-01' AND '2026-10-01'
AND LINE_OF_BUSINESS IN ('Motor','Travel')""").iloc[0]
for key in ['GWP','NEP','NET_INCURRED_CLAIMS','LOSS_RATIO']:
    assert abs(Decimal(str(total[key]))-Decimal(str(source[key]))) < Decimal('0.000001'), key
assert total.PLAN_GWP == plan.GWP and total.PLAN_NEP == plan.NEP
assert total.GWP_VARIANCE == total.GWP-total.PLAN_GWP
assert total.NEP_VARIANCE == total.NEP-total.PLAN_NEP
assert total.MISSING_ACTUAL == 0 and total.MISSING_PLAN == 0
for level in ['MONTH','LINE','CHANNEL']:
    assert data.loc[data.LEVEL.eq(level),'GWP'].sum() == total.GWP
    assert data.loc[data.LEVEL.eq(level),'PLAN_GWP'].sum() == total.PLAN_GWP
a.button(key='nav-exec').click().run(); clean(a)
a.button(key='EXEC').click().run(); clean(a)
results['Executive'] = {'status':'PASS','actual_plan_source_reconciliation':'PASS',
    'grouped_totals':'PASS','semantic_definition':'PASS','ui':'PASS',
    '2026_YTD_GWP':str(total.GWP),'2026_YTD_PLAN_GWP':str(total.PLAN_GWP),
    'claims_plan_comparability':'UNCONFIRMED: no documented gross/net definition'}

# Full Service Desk workflow lives in its focused acceptance helper.
from tests.live_desk import run as run_desk_acceptance
results['ServiceDesk'] = run_desk_acceptance()

# Cortex failure must show a deterministic brief, not remove core screens.
with patch.object(SnowflakeService,'explain',side_effect=RuntimeError('simulated outage')):
    a = app()
    a.button(key='nav-nbo').click().run(); clean(a)
    a.toggle[0].set_value(True).run()
    a.button(key='NBO').click().run(); clean(a)
    assert any('Cortex unavailable' in x.value for x in a.caption)
results['CortexOutage'] = 'PASS: deterministic brief and customer screen available'
Path('validation/acceptance.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
