"""Read-only SQL fixtures: missing coverage, zero denominators and null facts."""
import json
from pathlib import Path
import pandas as pd
from business_logic import GOLD, finance_query
from snowflake_service import get_service

actual = """(SELECT TO_DATE(column1) ACCOUNTING_MONTH,'MY' ENTITY_CODE,'Motor' LINE_OF_BUSINESS,
'Agency' DISTRIBUTION_CHANNEL,column2 GROSS_WRITTEN_PREMIUM,0 NET_EARNED_PREMIUM,
10 GROSS_CLAIMS_PAID,2 OS_RESERVE_MOVEMENT,1 IBNR_MOVEMENT,3 REINSURANCE_RECOVERIES
FROM VALUES ('2026-01-01',100),('2026-02-01',200))"""
plan = """(SELECT TO_DATE(column1) ACCOUNTING_MONTH,'MY' ENTITY_CODE,'Motor' LINE_OF_BUSINESS,
'Agency' DISTRIBUTION_CHANNEL,column2 PLAN_GROSS_WRITTEN_PREMIUM,0 PLAN_NET_EARNED_PREMIUM,
15 PLAN_INCURRED_CLAIMS FROM VALUES ('2026-01-01',0),('2026-03-01',60))"""
sql,params = finance_query('2026-01-01','2026-03-01')
fixture = sql.replace(GOLD+'.GI_ENTERPRISE_WIDE_MART',actual).replace(GOLD+'.GI_PLAN_MONTHLY',plan)
s = get_service()
data = s.query(fixture,params)
total = data.loc[data.LEVEL.eq('TOTAL')].iloc[0]
assert total.GWP == 300 and total.PLAN_GWP == 60
assert total.MISSING_ACTUAL == 1 and total.MISSING_PLAN == 1
assert pd.isna(total.GWP_VARIANCE) and pd.isna(total.GWP_VARIANCE_PCT)
assert pd.isna(total.LOSS_RATIO)
jan = data.loc[data.LEVEL.eq('MONTH') & data.ACCOUNTING_MONTH.astype(str).eq('2026-01-01')].iloc[0]
assert jan.GWP_VARIANCE == 100 and pd.isna(jan.GWP_VARIANCE_PCT)
null_fixture = fixture.replace("('2026-02-01',200)","('2026-02-01',NULL)")
nulls = s.query(null_fixture,params)
assert pd.isna(nulls.loc[nulls.LEVEL.eq('TOTAL')].iloc[0].GWP)
Path('validation/financial_edges.json').write_text(json.dumps({'status':'PASS',
'missing_actual_and_plan':'PASS','zero_plan_percentage':'PASS','zero_earned_premium_ratio':'PASS',
'null_source_amount_not_silently_omitted':'PASS','mutations':'NONE: inline SQL fixtures only'},indent=2))
print('Financial SQL edge cases PASS')
