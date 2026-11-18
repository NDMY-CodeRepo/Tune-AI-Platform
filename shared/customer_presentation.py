"""Combine existing NBA/NBO evidence for display, without new recommendation rules."""
from .business_logic import customer_evidence
from .product_opportunities import product_evidence


def brief(finding,facts,action):
    return {'finding':finding,'facts':facts,'action':action,
            'ids':list(range(min(3,len(facts)))),'source':'Rule-based recommendation'}


def unified_profile(row,has_offer,product_agnostic=False):
    retention=brief(*customer_evidence(row,'NBA'))
    offer=brief(*(product_evidence(row) if product_agnostic else customer_evidence(row,'NBO'))) if has_offer else None
    facts=[f"Recommended retention action: {row['ACTION']}."]+retention['facts']
    if offer:
        facts=list(dict.fromkeys(facts+offer['facts']))
    action=retention['action']+(' '+offer['action'] if offer else '')
    return {'retention':retention,'offer':offer,
            'combined':brief(retention['finding'],facts,action)}
