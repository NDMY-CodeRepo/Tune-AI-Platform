"""Compact presentation uses SQL results and preserves Cortex evidence IDs."""
from decimal import Decimal

import pandas as pd
import pytest

from shared.executive_ui import compact_evidence, _delta_sentence


def test_short_evidence_keeps_full_fact_id_order():
    # Illustrative test values only, never application results.
    total=pd.Series({'GWP_VARIANCE':Decimal('-100000'),'GWP_VARIANCE_PCT':Decimal('-.05'),
                     'NEP_VARIANCE':Decimal('-50000'),'NEP_VARIANCE_PCT':Decimal('-.04'),
                     'LOSS_RATIO':Decimal('.58')})
    data=pd.DataFrame([
        {'LEVEL':'LINE','LINE_OF_BUSINESS':'Travel','GWP_VARIANCE':Decimal('-10000'),'GWP_VARIANCE_PCT':Decimal('-.02')},
        {'LEVEL':'LINE','LINE_OF_BUSINESS':'Motor','GWP_VARIANCE':Decimal('-90000'),'GWP_VARIANCE_PCT':Decimal('-.10')},
        {'LEVEL':'CHANNEL','DISTRIBUTION_CHANNEL':'Agency','GWP_VARIANCE':Decimal('-80000')},
    ])
    short=compact_evidence(data,total)
    assert len(short)==6
    assert short[3]=='Motor: RM 90K below plan (10.0%).'
    assert short[4]=='Travel: RM 10K below plan (2.0%).'
    assert short[5]=='Agency: RM 80K below plan.'
    assert all(len(sentence)<80 for sentence in short)


@pytest.mark.parametrize('value,ratio,expected',[
    (None,None,'GWP: comparison unavailable.'),
    (0,None,'GWP: in line with plan.'),
    (100000,None,'GWP: RM 100K above plan.'),
    (-100000,None,'GWP: RM 100K below plan.'),
])
def test_missing_or_zero_plan_does_not_create_a_percentage(value,ratio,expected):
    assert _delta_sentence('GWP',value,ratio)==expected
