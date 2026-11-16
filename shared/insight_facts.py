"""Shared verified financial narrative; reused by Streamlit and the local API."""
import pandas as pd

def amount(value):
    return 'Unavailable' if pd.isna(value) else f'RM {float(value):,.2f}'


def percentage(value):
    return 'Unavailable' if pd.isna(value) else f'{float(value):,.1%}'


def financial_narrative(data,total):
    facts = [f'Gross written premium is {amount(total.GWP)} against plan {amount(total.PLAN_GWP)}; variance {amount(total.GWP_VARIANCE)} ({percentage(total.GWP_VARIANCE_PCT)}).',
             f'Net earned premium is {amount(total.NEP)} against plan {amount(total.PLAN_NEP)}; variance {amount(total.NEP_VARIANCE)} ({percentage(total.NEP_VARIANCE_PCT)}).',
             f'Net incurred claims are {amount(total.NET_INCURRED_CLAIMS)}; net loss ratio is {percentage(total.LOSS_RATIO)}.']
    lines = data.loc[data.LEVEL.eq('LINE')].sort_values('GWP_VARIANCE',na_position='last')
    for _,r in lines.iterrows():
        facts.append(f"{r.LINE_OF_BUSINESS}: GWP variance {amount(r.GWP_VARIANCE)} ({percentage(r.GWP_VARIANCE_PCT)}).")
    channels = data.loc[data.LEVEL.eq('CHANNEL')].sort_values('GWP_VARIANCE',na_position='last')
    if not channels.empty and pd.notna(channels.iloc[0].GWP_VARIANCE):
        r = channels.iloc[0]
        facts.append(f"{r.DISTRIBUTION_CHANNEL} has the lowest selected channel GWP variance: {amount(r.GWP_VARIANCE)}.")
    valid_lines = lines.dropna(subset=['GWP_VARIANCE'])
    if valid_lines.empty:
        recommendation = 'Comparable performance is unavailable for this selection. Review source coverage.'
    else:
        worst = valid_lines.iloc[0]
        recommendation = (f'{worst.LINE_OF_BUSINESS} has the largest GWP shortfall versus plan in this selection.'
                          if worst.GWP_VARIANCE < 0 else 'All selected business lines meet or exceed GWP plan.')
    return recommendation,facts


