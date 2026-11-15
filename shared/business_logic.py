"""Transparent demo rules and static, reviewed financial definitions."""
import json
import pandas as pd

GOLD = "TUNE_BI_DB.GOLD"
CANDIDATE_WHERE = "HOLDS_MOTOR='Yes' AND HOLDS_TRAVEL='No' AND NEXT_BEST_PRODUCT='Travel' AND MARKETING_CONSENT='Yes'"
NET_INCURRED = "SUM(GROSS_CLAIMS_PAID) + SUM(OS_RESERVE_MOVEMENT) + SUM(IBNR_MOVEMENT) - SUM(REINSURANCE_RECOVERIES)"
LOSS_RATIO = f"({NET_INCURRED}) / NULLIF(SUM(NET_EARNED_PREMIUM), 0)"
CUSTOMER_FIELDS = """CUSTOMER_ID, RETENTION_RISK_SCORE, RETENTION_RISK_BAND,
LIFETIME_VALUE, LIFETIME_VALUE_BAND, NEXT_RENEWAL_MONTH, PREFERRED_CHANNEL,
ACTIVE_POLICY_COUNT, HOLDS_MOTOR, HOLDS_TRAVEL, MARKETING_CONSENT, NEXT_BEST_PRODUCT,
SNAPSHOT_DATE"""
RENEWAL_SQL = """NEXT_RENEWAL_MONTH >= DATEADD(month,1,DATE_TRUNC('month',SNAPSHOT_DATE))
AND NEXT_RENEWAL_MONTH < DATEADD(month,4,DATE_TRUNC('month',SNAPSHOT_DATE))"""
ACTION_SQL = f"""CASE
WHEN RETENTION_RISK_BAND='High' AND LIFETIME_VALUE_BAND IN ('High','Top') AND ({RENEWAL_SQL}) THEN 'Priority retention review'
WHEN RETENTION_RISK_BAND='High' THEN 'Retention review'
WHEN RETENTION_RISK_BAND='Medium' AND ({RENEWAL_SQL}) THEN 'Proactive renewal engagement'
WHEN RETENTION_RISK_BAND='Medium' THEN 'Monitor retention needs'
WHEN RETENTION_RISK_BAND='Low' THEN 'Standard relationship maintenance'
ELSE 'Review missing risk information' END"""


def customer_query(mode, risk='All', value='All', channel='All', limit=200):
    if mode not in ('NBO', 'NBA'):
        raise ValueError('Unknown customer module')
    where = [CANDIDATE_WHERE if mode == 'NBO' else '1=1']
    params = []
    for col, val in [('RETENTION_RISK_BAND', risk), ('LIFETIME_VALUE_BAND', value), ('PREFERRED_CHANNEL', channel)]:
        if val != 'All':
            where.append(f'{col}=?')
            params.append(val)
    # NBO: retain high-risk relationships before pursuing a sales discussion.
    order = ("CASE RETENTION_RISK_BAND WHEN 'Low' THEN 0 WHEN 'Medium' THEN 1 WHEN 'High' THEN 2 ELSE 3 END, "
             "LIFETIME_VALUE DESC NULLS LAST, UPCOMING DESC, NEXT_RENEWAL_MONTH ASC NULLS LAST, CUSTOMER_ID") if mode == 'NBO' else (
             "CASE ACTION WHEN 'Priority retention review' THEN 0 WHEN 'Retention review' THEN 1 "
             "WHEN 'Proactive renewal engagement' THEN 2 WHEN 'Monitor retention needs' THEN 3 "
             "WHEN 'Standard relationship maintenance' THEN 4 ELSE 5 END, "
             "LIFETIME_VALUE DESC NULLS LAST, RETENTION_RISK_SCORE DESC NULLS LAST, CUSTOMER_ID")
    params.append(int(limit))
    return f"""SELECT {CUSTOMER_FIELDS}, ({RENEWAL_SQL}) AS UPCOMING,
    {ACTION_SQL} AS ACTION, COUNT(*) OVER() AS FILTERED_TOTAL
    FROM {GOLD}.CUSTOMER_360_WIDE_MART WHERE {' AND '.join(where)}
    ORDER BY {order} LIMIT ?""", params


def customer_evidence(row, mode):
    renewal = 'Unavailable in source' if pd.isna(row['NEXT_RENEWAL_MONTH']) else str(row['NEXT_RENEWAL_MONTH'])[:7]
    facts = [
        f"Customer value is MYR {float(row['LIFETIME_VALUE']):,.2f} ({row['LIFETIME_VALUE_BAND']} band).",
        f"Retention risk is {row['RETENTION_RISK_BAND']}; source score {row['RETENTION_RISK_SCORE']}.",
        f"Next renewal month: {renewal}. Preferred channel: {row['PREFERRED_CHANNEL']}.",
    ]
    if mode == 'NBO':
        facts.insert(0, 'Holds Motor, does not hold Travel, has marketing consent, and the existing next-best-product field is Travel.')
        action = ('Review retention needs first, then consider a Travel discussion.' if row['RETENTION_RISK_BAND'] == 'High'
                  else f"Prepare a human-reviewed Travel needs discussion through {row['PREFERRED_CHANNEL']}.")
        recommendation = 'Travel cross-sell candidate for review; eligibility, suitability and propensity are not established.'
    else:
        action = row['ACTION'] + '. Confirm renewal needs and the appropriate permitted contact route before any engagement.'
        recommendation = row['ACTION'] + ' — determined by the displayed business rules.'
    if pd.isna(row['UPCOMING']):
        facts.append('Renewal timing is unavailable in the source; confirm it before planning renewal engagement.')
    else:
        facts.append('Renewal is within the next three full calendar months after the customer snapshot.' if row['UPCOMING']
                     else 'Renewal is outside the next three full calendar months after the customer snapshot.')
    return recommendation, facts, action


def validate_ai_selection(raw, count):
    """Only approved fact identifiers can reach the UI; generated claims cannot."""
    value = json.loads(raw) if isinstance(raw, str) else raw
    ids = value.get('evidence_ids') if isinstance(value, dict) else None
    if not isinstance(ids, list) or not 1 <= len(ids) <= count:
        raise ValueError('Invalid evidence selection')
    if any(type(i) is not int or not 0 <= i < count for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Unsupported evidence')
    return ids


def finance_query(start, end, line='All', channel='All'):
    where = ['ACCOUNTING_MONTH BETWEEN ? AND ?', "LINE_OF_BUSINESS IN ('Motor','Travel')"]
    params = [str(start), str(end)]
    for col, val in [('LINE_OF_BUSINESS', line), ('DISTRIBUTION_CHANNEL', channel)]:
        if val != 'All':
            where.append(f'{col}=?')
            params.append(val)
    filters = ' AND '.join(where)
    # Each side is independently aggregated at identical business keys before joining.
    sql = f"""WITH actual AS (
      SELECT ACCOUNTING_MONTH,ENTITY_CODE,LINE_OF_BUSINESS,DISTRIBUTION_CHANNEL,
      IFF(COUNT_IF(GROSS_WRITTEN_PREMIUM IS NULL)=0,SUM(GROSS_WRITTEN_PREMIUM),NULL) A_GWP,
      IFF(COUNT_IF(NET_EARNED_PREMIUM IS NULL)=0,SUM(NET_EARNED_PREMIUM),NULL) A_NEP,
      IFF(COUNT_IF(GROSS_CLAIMS_PAID IS NULL)=0,SUM(GROSS_CLAIMS_PAID),NULL) CLAIMS_PAID,
      IFF(COUNT_IF(GROSS_CLAIMS_PAID IS NULL OR OS_RESERVE_MOVEMENT IS NULL OR IBNR_MOVEMENT IS NULL OR REINSURANCE_RECOVERIES IS NULL)=0,{NET_INCURRED},NULL) NET_CLAIMS,
      IFF(COUNT_IF(GROSS_CLAIMS_PAID IS NULL OR OS_RESERVE_MOVEMENT IS NULL OR IBNR_MOVEMENT IS NULL)=0,SUM(GROSS_CLAIMS_PAID)+SUM(OS_RESERVE_MOVEMENT)+SUM(IBNR_MOVEMENT),NULL) GROSS_CLAIMS,
      1 A_PRESENT FROM {GOLD}.GI_ENTERPRISE_WIDE_MART WHERE {filters} GROUP BY ALL
    ), plan AS (
      SELECT ACCOUNTING_MONTH,ENTITY_CODE,LINE_OF_BUSINESS,DISTRIBUTION_CHANNEL,
      IFF(COUNT_IF(PLAN_GROSS_WRITTEN_PREMIUM IS NULL)=0,SUM(PLAN_GROSS_WRITTEN_PREMIUM),NULL) P_GWP,
      IFF(COUNT_IF(PLAN_NET_EARNED_PREMIUM IS NULL)=0,SUM(PLAN_NET_EARNED_PREMIUM),NULL) P_NEP,
      IFF(COUNT_IF(PLAN_INCURRED_CLAIMS IS NULL)=0,SUM(PLAN_INCURRED_CLAIMS),NULL) P_CLAIMS, 1 P_PRESENT
      FROM {GOLD}.GI_PLAN_MONTHLY WHERE {filters} GROUP BY ALL
    ), aligned AS (
      SELECT COALESCE(a.ACCOUNTING_MONTH,p.ACCOUNTING_MONTH) ACCOUNTING_MONTH,
      COALESCE(a.LINE_OF_BUSINESS,p.LINE_OF_BUSINESS) LINE_OF_BUSINESS,
      COALESCE(a.DISTRIBUTION_CHANNEL,p.DISTRIBUTION_CHANNEL) DISTRIBUTION_CHANNEL,
      A_GWP,A_NEP,CLAIMS_PAID,NET_CLAIMS,GROSS_CLAIMS,P_GWP,P_NEP,P_CLAIMS,A_PRESENT,P_PRESENT
      FROM actual a FULL OUTER JOIN plan p ON a.ACCOUNTING_MONTH=p.ACCOUNTING_MONTH
      AND a.ENTITY_CODE=p.ENTITY_CODE AND a.LINE_OF_BUSINESS=p.LINE_OF_BUSINESS
      AND a.DISTRIBUTION_CHANNEL=p.DISTRIBUTION_CHANNEL
    ) SELECT CASE WHEN GROUPING(ACCOUNTING_MONTH)=0 THEN 'MONTH'
      WHEN GROUPING(LINE_OF_BUSINESS)=0 THEN 'LINE'
      WHEN GROUPING(DISTRIBUTION_CHANNEL)=0 THEN 'CHANNEL' ELSE 'TOTAL' END LEVEL,
      ACCOUNTING_MONTH,LINE_OF_BUSINESS,DISTRIBUTION_CHANNEL,
      COUNT(*) KEY_COUNT,COUNT_IF(A_PRESENT IS NULL) MISSING_ACTUAL,
      COUNT_IF(P_PRESENT IS NULL) MISSING_PLAN,
      IFF(COUNT_IF(A_PRESENT=1 AND A_GWP IS NULL)=0,SUM(A_GWP),NULL) GWP,
      IFF(COUNT_IF(P_PRESENT=1 AND P_GWP IS NULL)=0,SUM(P_GWP),NULL) PLAN_GWP,
      IFF(COUNT_IF(A_PRESENT=1 AND A_NEP IS NULL)=0,SUM(A_NEP),NULL) NEP,
      IFF(COUNT_IF(P_PRESENT=1 AND P_NEP IS NULL)=0,SUM(P_NEP),NULL) PLAN_NEP,
      IFF(COUNT_IF(A_PRESENT=1 AND CLAIMS_PAID IS NULL)=0,SUM(CLAIMS_PAID),NULL) CLAIMS_PAID,
      IFF(COUNT_IF(A_PRESENT=1 AND NET_CLAIMS IS NULL)=0,SUM(NET_CLAIMS),NULL) NET_INCURRED_CLAIMS,
      IFF(COUNT_IF(A_PRESENT=1 AND GROSS_CLAIMS IS NULL)=0,SUM(GROSS_CLAIMS),NULL) GROSS_INCURRED_CLAIMS,
      IFF(COUNT_IF(P_PRESENT=1 AND P_CLAIMS IS NULL)=0,SUM(P_CLAIMS),NULL) PLAN_INCURRED_CLAIMS,
      IFF(COUNT_IF(A_PRESENT=1 AND (NET_CLAIMS IS NULL OR A_NEP IS NULL))=0,SUM(NET_CLAIMS)/NULLIF(SUM(A_NEP),0),NULL) LOSS_RATIO,
      IFF(COUNT_IF(A_GWP IS NULL OR P_GWP IS NULL)=0,SUM(A_GWP)-SUM(P_GWP),NULL) GWP_VARIANCE,
      IFF(COUNT_IF(A_GWP IS NULL OR P_GWP IS NULL)=0,(SUM(A_GWP)-SUM(P_GWP))/NULLIF(SUM(P_GWP),0),NULL) GWP_VARIANCE_PCT,
      IFF(COUNT_IF(A_NEP IS NULL OR P_NEP IS NULL)=0,SUM(A_NEP)-SUM(P_NEP),NULL) NEP_VARIANCE,
      IFF(COUNT_IF(A_NEP IS NULL OR P_NEP IS NULL)=0,(SUM(A_NEP)-SUM(P_NEP))/NULLIF(SUM(P_NEP),0),NULL) NEP_VARIANCE_PCT
      FROM aligned GROUP BY GROUPING SETS ((),(ACCOUNTING_MONTH),(LINE_OF_BUSINESS),(DISTRIBUTION_CHANNEL))
      ORDER BY LEVEL,ACCOUNTING_MONTH,LINE_OF_BUSINESS,DISTRIBUTION_CHANNEL"""
    return sql, params + params


CATEGORIES = ['REPORT_REQUEST','DATA_EXTRACT','DATA_ISSUE','ACCESS_REQUEST','OTHER']
PRIORITIES = ['LOW','MEDIUM','HIGH']
STATUSES = ['NEW','IN_PROGRESS','RESOLVED','CLOSED']
TRANSITIONS = {'NEW': ['NEW','IN_PROGRESS'], 'IN_PROGRESS':['IN_PROGRESS','RESOLVED'],
               'RESOLVED':['RESOLVED','IN_PROGRESS','CLOSED'], 'CLOSED':['CLOSED']}


def validate_ticket_change(old_status, status, owner, notes):
    if status not in TRANSITIONS.get(old_status, []):
        raise ValueError('Follow the workflow: New → In progress → Resolved → Closed.')
    if status != 'NEW' and not owner.strip():
        raise ValueError('Assign an owner before starting work.')
    if status in ('RESOLVED','CLOSED') and not notes.strip():
        raise ValueError('Resolution notes are required before resolving or closing a request.')
