"""Source-recorded product opportunities; reuse the validated NBO ordering.

Motor/Travel are the only known holding flags. For other product names we can
report a source candidate, but cannot establish whether it is already held.
The legacy Motor-to-Travel predicate and APIs remain available unchanged.
"""
from .business_logic import GOLD, CANDIDATE_WHERE, customer_query, customer_evidence

PRODUCT_SQL = 'TRIM(NEXT_BEST_PRODUCT)'
HOLDING_SQL = """CASE
WHEN HOLDS_MOTOR='Yes' AND HOLDS_TRAVEL='Yes' THEN 'Motor + Travel'
WHEN HOLDS_MOTOR='Yes' AND HOLDS_TRAVEL='No' THEN 'Motor'
WHEN HOLDS_MOTOR='No' AND HOLDS_TRAVEL='Yes' THEN 'Travel'
WHEN HOLDS_MOTOR='No' AND HOLDS_TRAVEL='No' THEN 'No Motor / Travel recorded'
ELSE 'Holdings unavailable' END"""
OPPORTUNITY_WHERE = f"""MARKETING_CONSENT='Yes'
AND {PRODUCT_SQL} IS NOT NULL
AND LOWER({PRODUCT_SQL}) NOT IN ('','none','null','n/a','no recommendation')
AND (LOWER({PRODUCT_SQL}) <> 'motor' OR HOLDS_MOTOR='No')
AND (LOWER({PRODUCT_SQL}) <> 'travel' OR HOLDS_TRAVEL='No')"""


def opportunity_query(risk='All', value='All', channel='All', holding='All', product='All'):
    sql, params = customer_query('NBO', risk, value, channel)
    where = OPPORTUNITY_WHERE
    extra = []
    for expression, selected in [(HOLDING_SQL, holding), (PRODUCT_SQL, product)]:
        if selected != 'All':
            where += f' AND ({expression})=?'
            extra.append(selected)
    # The replacement predicate precedes the legacy risk/value/channel clauses.
    return sql.replace(CANDIDATE_WHERE, '('+where+')'), extra+params


def candidate_product(row):
    value = row.get('NEXT_BEST_PRODUCT')
    if not isinstance(value, str) or value.strip().lower() in ('','none','null','n/a','no recommendation'):
        return None
    product = value.strip()
    if row.get('MARKETING_CONSENT') != 'Yes':
        return None
    if product.lower() in ('motor','travel') and row.get('HOLDS_'+product.upper()) != 'No':
        return None
    return product


def product_evidence(row):
    product = candidate_product(row)
    if product is None:
        raise ValueError('No consented source candidate')
    _, facts, _ = customer_evidence(row, 'NBA')
    held = [name for name in ('Motor','Travel') if row.get('HOLDS_'+name.upper())=='Yes']
    unknown = [name for name in ('Motor','Travel') if row.get('HOLDS_'+name.upper()) not in ('Yes','No')]
    holdings = ', '.join(held) or 'none recorded'
    if unknown:
        holdings += '; holding information unavailable for '+', '.join(unknown)
    reason = (f"Recorded Motor/Travel holdings: {holdings}. "
              f"Marketing consent is Yes; the existing next-best-product field is {product}.")
    if product.lower() not in ('motor','travel'):
        reason += ' Holdings for this candidate product are not available in these attributes; confirm them during review.'
    action = (f'Review retention needs first, then consider a {product} discussion.'
              if row['RETENTION_RISK_BAND']=='High' else
              f"Prepare a human-reviewed {product} needs discussion through {row['PREFERRED_CHANNEL']}.")
    finding = f'{product} cross-sell candidate for review; eligibility, suitability and propensity are not established.'
    return finding, [reason]+facts, action


class ProductOpportunities:
    def opportunity_customers(self, risk='All', value='All', channel='All', holding='All', product='All'):
        sql, params = opportunity_query(risk,value,channel,holding,product)
        return self.query(sql,params)

    def opportunity_overview(self):
        return self.query(f"""SELECT RETENTION_RISK_BAND,LIFETIME_VALUE_BAND,PREFERRED_CHANNEL,
        {HOLDING_SQL} AS EXISTING_HOLDING,{PRODUCT_SQL} AS CANDIDATE_PRODUCT,
        COUNT(*) CUSTOMERS FROM {GOLD}.CUSTOMER_360_WIDE_MART
        WHERE {OPPORTUNITY_WHERE} GROUP BY ALL""")
