"""Final read-only checks; no tickets created here."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from business_logic import GOLD, customer_evidence
from snowflake_service import get_service, read

ROOT = Path(__file__).resolve().parents[1]
s = get_service()
identity = s.query('SELECT CURRENT_ROLE() ROLE,CURRENT_WAREHOUSE() WAREHOUSE').iloc[0].to_dict()
missing = s.query(f"SELECT CUSTOMER_ID, LIFETIME_VALUE,LIFETIME_VALUE_BAND,RETENTION_RISK_BAND,RETENTION_RISK_SCORE,NEXT_RENEWAL_MONTH,PREFERRED_CHANNEL,NULL UPCOMING,'Retention review' ACTION FROM {GOLD}.CUSTOMER_360_WIDE_MART WHERE NEXT_RENEWAL_MONTH IS NULL LIMIT 1").iloc[0].to_dict()
assert 'unavailable' in customer_evidence(missing,'NBA')[1][-1]
a = AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
assert not a.error and not a.exception
a.sidebar.radio[0].set_value('Next Best Action').run()
a.selectbox(key='NBArisk').set_value('Low').run()
a.toggle[0].set_value(False).run()
a.button(key='NBA').click().run()
assert not a.error and not a.exception
a.sidebar.radio[0].set_value('Executive Intelligence').run()
assert not a.error and not a.exception

before = json.loads((ROOT/'validation/runtime_inspection.json').read_text(encoding='utf-8-sig'))[-1]
after = s.query(f"""SELECT 'DERIVED_METRIC' OBJECT_NAME,COUNT(*) N,HASH_AGG(*) CONTENT_HASH FROM {GOLD}.DERIVED_METRIC
UNION ALL SELECT 'FIELD_DISPLAY',COUNT(*),HASH_AGG(*) FROM {GOLD}.FIELD_DISPLAY
UNION ALL SELECT 'MART_REGISTRY',COUNT(*),HASH_AGG(*) FROM {GOLD}.MART_REGISTRY""").to_dict('records')
assert sorted(before,key=lambda r:r['OBJECT_NAME']) == sorted(after,key=lambda r:r['OBJECT_NAME'])
schema_before = json.loads((ROOT/'validation/schema_inspection.json').read_text(encoding='utf-8-sig'))[1]
schema_after = s.query("SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE FROM TUNE_BI_DB.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='GOLD' ORDER BY TABLE_NAME,ORDINAL_POSITION").to_dict('records')
assert schema_before == schema_after

read.clear()
with patch('snowflake_service.get_service',side_effect=RuntimeError('simulated connection outage')):
    outage = AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert outage.error and not outage.exception and not outage.metric
    assert 'No sample figures' in outage.error[0].value

result = {'status':'PASS','session':identity,'NBA_missing_renewal':'PASS',
          'final_application_screens':'PASS','connection_outage_no_substituted_figures':'PASS',
          'GOLD_column_metadata_unchanged':'PASS','semantic_content_hashes_unchanged':'PASS',
          'semantic_fingerprints':after}
(ROOT/'validation/final_checks.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
