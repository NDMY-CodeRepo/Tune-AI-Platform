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
a.sidebar.radio[0].set_value('Next Best Action').run(); clean(a)
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
a.sidebar.radio[0].set_value('Executive Intelligence').run(); clean(a)
a.button(key='EXEC').click().run(); clean(a)
results['Executive'] = {'status':'PASS','actual_plan_source_reconciliation':'PASS',
    'grouped_totals':'PASS','semantic_definition':'PASS','ui':'PASS',
    '2026_YTD_GWP':str(total.GWP),'2026_YTD_PLAN_GWP':str(total.PLAN_GWP),
    'claims_plan_comparability':'UNCONFIRMED: no documented gross/net definition'}

# Real Snowflake create → assign → resolve → business-user visibility through the UI.
a = AppTest.from_file(str(ROOT/'apps/data-service-desk/app.py'),default_timeout=90).run(); clean(a)
assert a.sidebar.radio[0].options == ['Business User Portal','Data Team Workspace']
def select(label): return next(x for x in a.selectbox if x.label == label)
def text(label): return next(x for x in a.text_input if x.label == label)
def area(label): return next(x for x in a.text_area if x.label == label)
def button(label): return next(x for x in a.button if x.label == label)
text('Demo requester identity').set_value('validation.motor')
button('New Data Request').click().run()
text('Request title').set_value('[Validation] Motor claims breakdown report')
area('Description').set_value('Demo rehearsal: request monthly Motor claims paid breakdown by distribution channel.')
area('Business justification').set_value('Validate the executive demo ticket workflow. Synthetic demo request; no external delivery.')
button('Submit request').click().run(); clean(a)
ticket_id = a.session_state['last_ticket']
assert s.tickets(requester='validation.motor').TICKET_ID.eq(ticket_id).any()
a.sidebar.radio[0].set_value('Data Team Workspace').run(); clean(a)
select('Open request').set_value(ticket_id).run()
text('Assigned owner').set_value('demo.engineer')
select('Update status').set_value('IN_PROGRESS')
area('Work progress').set_value('Validated source fields and agreed report grain.')
button('Save ticket update').click().run(); clean(a)
select('Update status').set_value('RESOLVED')
area('Resolution notes').set_value('Demo workflow validated. Monthly Motor claims breakdown can use GI_ENTERPRISE_WIDE_MART at accounting-month/channel grain. No report delivered by this test.')
button('Save ticket update').click().run(); clean(a)
a.sidebar.radio[0].set_value('Business User Portal').run(); clean(a)
assert any('Demo workflow validated.' in x.value for x in a.markdown)
stored = s.tickets(requester='validation.motor').iloc[0]
assert stored.STATUS == 'RESOLVED' and stored.ASSIGNED_TO == 'demo.engineer'
try:
    s.update_ticket(ticket_id,1,'NEW','IN_PROGRESS','other.engineer','','')
    raise AssertionError('Stale update was accepted')
except ValueError as exc:
    assert 'another session' in str(exc)
results['ServiceDesk'] = {'status':'PASS','ticket_id':ticket_id,'create_assign_resolve_business_view':'PASS','stale_update_rejected':'PASS'}

# Cortex failure must show a deterministic brief, not remove core screens.
with patch.object(SnowflakeService,'explain',side_effect=RuntimeError('simulated outage')):
    a = app()
    a.sidebar.radio[0].set_value('Next Best Offer').run(); clean(a)
    a.toggle[0].set_value(True).run()
    a.button(key='NBO').click().run(); clean(a)
    assert any('Cortex unavailable' in x.value for x in a.caption)
results['CortexOutage'] = 'PASS: deterministic brief and customer screen available'
Path('validation/acceptance.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
