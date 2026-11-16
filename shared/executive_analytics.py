"""Management views over the existing reconciled financial aggregation."""
import pandas as pd

from .business_logic import finance_query

TREND_METRICS = {
    'GWP Actual vs Plan': ('GWP', 'PLAN_GWP', 'currency'),
    'NEP Actual vs Plan': ('NEP', 'PLAN_NEP', 'currency'),
    'Net Incurred Claims': ('NET_INCURRED_CLAIMS', None, 'currency'),
    'Net Loss Ratio': ('LOSS_RATIO', None, 'percent'),
}


def analytics_query(start,end,line='All',channel='All'):
    """Add shares after aggregation; original financial definitions stay intact."""
    base,params=finance_query(start,end,line,channel)
    sql=f"""WITH financial AS ({base})
    SELECT financial.*,
      IFF(LEVEL IN ('LINE','CHANNEL')
          AND COUNT_IF(GWP IS NULL OR GWP<0) OVER(PARTITION BY LEVEL)=0,
          GWP/NULLIF(SUM(GWP) OVER(PARTITION BY LEVEL),0),NULL) GWP_SHARE,
      IFF(LEVEL IN ('LINE','CHANNEL')
          AND COUNT_IF(NEP IS NULL OR NEP<0) OVER(PARTITION BY LEVEL)=0,
          NEP/NULLIF(SUM(NEP) OVER(PARTITION BY LEVEL),0),NULL) NEP_SHARE
    FROM financial
    ORDER BY LEVEL,ACCOUNTING_MONTH,LINE_OF_BUSINESS,DISTRIBUTION_CHANNEL"""
    return sql,params


def trend_frame(data,measure):
    actual,plan,kind=TREND_METRICS[measure]
    monthly=data.loc[data.LEVEL.eq('MONTH')].sort_values('ACCOUNTING_MONTH')
    columns=[actual]+([plan] if plan else [])
    renamed={actual:'Actual'} | ({plan:'Plan'} if plan else {})
    frame=monthly[['ACCOUNTING_MONTH']+columns].rename(columns=renamed).melt(
        'ACCOUNTING_MONTH',var_name='Series',value_name='Value')
    return frame,kind


def ranked_variance(data,level,metric):
    if level not in ('LINE','CHANNEL') or metric not in ('GWP','NEP'):
        raise ValueError('Unsupported variance view')
    rows=data.loc[data.LEVEL.eq(level)].copy()
    valid=(rows[metric+'_VARIANCE'].notna()
           & pd.to_numeric(rows.MISSING_ACTUAL,errors='coerce').eq(0)
           & pd.to_numeric(rows.MISSING_PLAN,errors='coerce').eq(0)
           & pd.to_numeric(rows.KEY_COUNT,errors='coerce').gt(0))
    return rows.loc[valid].sort_values(metric+'_VARIANCE'),int((~valid).sum())


def portfolio_frame(data,level,metric):
    if level not in ('LINE','CHANNEL') or metric not in ('GWP','NEP'):
        raise ValueError('Unsupported portfolio view')
    rows=data.loc[data.LEVEL.eq(level)].copy()
    if rows.empty or rows[metric+'_SHARE'].isna().any():
        return rows.iloc[:0]
    return rows.sort_values(metric,ascending=False)


CHANNEL_COLUMNS=['DISTRIBUTION_CHANNEL','GWP','PLAN_GWP','GWP_VARIANCE',
                 'GWP_VARIANCE_PCT','NEP','NET_INCURRED_CLAIMS','LOSS_RATIO']


def channel_scorecard(data):
    rows=data.loc[data.LEVEL.eq('CHANNEL'),CHANNEL_COLUMNS].copy()
    for field in CHANNEL_COLUMNS[1:]:
        rows[field]=pd.to_numeric(rows[field],errors='coerce')
    return rows.sort_values('GWP',ascending=False,na_position='last')
