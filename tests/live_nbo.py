"""Explicit live read-only NBO gate. Run before implementing later modules."""
import json
from pathlib import Path
from streamlit.testing.v1 import AppTest
from shared.business_logic import GOLD, CANDIDATE_WHERE, customer_evidence
from shared.snowflake_service import get_service, read

s = get_service()
health = s.health()
assert health['ROW_COUNT'] == health['CUSTOMERS'] == 179725
direct = s.query(f'SELECT COUNT(DISTINCT CUSTOMER_ID) N FROM {GOLD}.CUSTOMER_360_WIDE_MART WHERE {CANDIDATE_WHERE}').iloc[0]['N']
overview = s.overview('NBO')
assert direct == overview.CUSTOMERS.sum() == 10566
customers = s.customers('NBO', value='High')
assert not customers.empty and customers.LIFETIME_VALUE_BAND.eq('High').all()
assert customers.HOLDS_MOTOR.eq('Yes').all() and customers.HOLDS_TRAVEL.eq('No').all()
assert customers.MARKETING_CONSENT.eq('Yes').all() and customers.NEXT_BEST_PRODUCT.eq('Travel').all()
_, facts, _ = customer_evidence(customers.iloc[0].to_dict(), 'NBO')
ids = s.explain(facts)
assert ids
app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'apps/ai-intelligence/app.py'), default_timeout=90).run()
app.sidebar.radio[0].set_value('Next Best Offer').run()
assert not app.exception, app.exception
assert not app.error, [x.value for x in app.error]
assert app.metric[0].value == '10,566'
app.selectbox(key='NBOvalue').set_value('High').run()
assert not app.error
app.button(key='NBO').click().run()
assert not app.error and not app.exception
assert any('AI-curated explanation' in x.value for x in app.caption)
app.toggle[0].set_value(False).run()
app.button(key='NBO').click().run()
assert any('Deterministic explanation' in x.value for x in app.caption)
Path('validation/nbo_gate.json').write_text(json.dumps({
    'status':'PASS','source_unique_customers':int(direct),'overview_customers':int(overview.CUSTOMERS.sum()),
    'high_value_filter':'PASS','source_attributes':'PASS','cortex_grounded_selection':'PASS',
    'streamlit_launch_filter_brief':'PASS','ai_disabled_fallback':'PASS'}, indent=2))
print('NBO gate PASS: live count, filters, source attributes, Cortex brief and AI-off fallback.')
