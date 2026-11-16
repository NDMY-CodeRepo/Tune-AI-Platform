"""Management presentation guards over the existing financial aggregation."""
import pandas as pd
import pytest

from shared.business_logic import finance_query
from shared.executive_analytics import (analytics_query, trend_frame, ranked_variance,
                                        portfolio_frame, channel_scorecard)


def test_projection_reuses_financial_sql_and_bound_parameters():
    args=('2026-01-01','2026-10-01','Motor',"Agency'; DROP TABLE x; --")
    base,params=finance_query(*args)
    query,actual=analytics_query(*args)
    assert base in query and actual==params
    assert args[-1] not in query
    assert 'SUM(GWP) OVER(PARTITION BY LEVEL)' in query
    assert 'SUM(NEP) OVER(PARTITION BY LEVEL)' in query
    assert 'NULLIF' in query and 'GWP<0' in query and 'NEP<0' in query


@pytest.mark.parametrize('measure,field,kind',[
    ('Net Incurred Claims','NET_INCURRED_CLAIMS','currency'),
    ('Net Loss Ratio','LOSS_RATIO','percent'),
])
def test_actual_only_trends_reuse_monthly_sql_values(measure,field,kind):
    data=pd.DataFrame([{'LEVEL':'MONTH','ACCOUNTING_MONTH':'2026-01-01',field:.58},
                       {'LEVEL':'TOTAL','ACCOUNTING_MONTH':None,field:.99}])
    plot,actual_kind=trend_frame(data,measure)
    assert actual_kind==kind and plot.Series.tolist()==['Actual']
    assert plot.Value.tolist()==[.58]


def test_variance_excludes_incomplete_groups_and_ranks_shortfalls():
    data=pd.DataFrame([{'LEVEL':'LINE','GWP_VARIANCE':v,'MISSING_ACTUAL':0,
                        'MISSING_PLAN':missing,'KEY_COUNT':1} for v,missing in [(20,0),(-50,0),(-80,1),(None,0)]])
    rows,excluded=ranked_variance(data,'LINE','GWP')
    assert rows.GWP_VARIANCE.tolist()==[-50,20] and excluded==2
    with pytest.raises(ValueError):
        ranked_variance(data,'TOTAL','GWP')


def test_portfolio_does_not_hide_unavailable_share():
    data=pd.DataFrame([{'LEVEL':'LINE','GWP':100,'GWP_SHARE':1},
                       {'LEVEL':'LINE','GWP':None,'GWP_SHARE':None}])
    assert portfolio_frame(data,'LINE','GWP').empty


def test_scorecard_preserves_numeric_sort_and_missing_values():
    data=pd.DataFrame([dict(LEVEL='CHANNEL',DISTRIBUTION_CHANNEL='Agency',GWP='100',
        PLAN_GWP=None,GWP_VARIANCE=None,GWP_VARIANCE_PCT=None,NEP='80',
        NET_INCURRED_CLAIMS='40',LOSS_RATIO='.5')])
    rows=channel_scorecard(data)
    assert rows.GWP.iloc[0]==100 and rows.LOSS_RATIO.iloc[0]==.5
    assert pd.isna(rows.GWP_VARIANCE.iloc[0])
