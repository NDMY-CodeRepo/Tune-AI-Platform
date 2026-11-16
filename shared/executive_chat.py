"""Bounded financial Q&A: Cortex selects SQL facts; it never supplies numbers/prose."""
import re
import pandas as pd
from .business_logic import validate_ai_selection
from .insight_facts import amount,percentage

METRICS={'GWP':r'\bgwp\b|gross written|premium',
         'NEP':r'\bnep\b|net earned',
         'NET_INCURRED_CLAIMS':r'claim|incurred',
         'LOSS_RATIO':r'loss ratio|\blr\b'}
MONTHS=['january','february','march','april','may','june','july','august','september','october','november','december']
SOURCES='TUNE_BI_DB.GOLD.GI_ENTERPRISE_WIDE_MART; GI_PLAN_MONTHLY; DERIVED_METRIC'


def present(value):
    return pd.notna(value)


def fact(row,metric):
    if row.LEVEL=='TOTAL': label='Selected portfolio'
    elif row.LEVEL=='MONTH': label=pd.Timestamp(row.ACCOUNTING_MONTH).strftime('%b %Y')
    else: label=str(row.LINE_OF_BUSINESS if row.LEVEL=='LINE' else row.DISTRIBUTION_CHANNEL)
    if metric in ('GWP','NEP'):
        variance=row[metric+'_VARIANCE']
        comparison=('Comparison unavailable (incomplete or invalid actual/plan coverage).' if not present(variance) else
                    f'Variance {amount(variance)} ({percentage(row[metric+"_VARIANCE_PCT"])}).')
        return f'{label}: {metric} actual {amount(row[metric])}; plan {amount(row["PLAN_"+metric])}. {comparison}'
    if metric=='LOSS_RATIO':
        return (f'{label}: net loss ratio {percentage(row.LOSS_RATIO)}; net incurred claims '
                f'{amount(row.NET_INCURRED_CLAIMS)} / net earned premium {amount(row.NEP)}. '
                'Ratio of summed values; planned loss-ratio comparison unavailable.')
    return f'{label}: net incurred claims {amount(row.NET_INCURRED_CLAIMS)}. Actuals only; plan claims gross/net basis is unconfirmed.'


def answer_question(data,scope,question,history,ai,service,available_channels=None):
    """Only returned, source-validated financial rows are eligible answer evidence."""
    q=question.strip().lower()
    response={'question':question,'scope':scope,'evidence':[],'source':'Calculated answer · AI optional',
              'supported':False,'answer':'','note':'Answers use the active dashboard filters. Observed contributions do not establish causes.'}
    def unavailable(message):
        return {**response,'answer':message}
    if data.empty:
        return unavailable('No financial data is available for these filters. Broaden the reporting scope and try again.')
    # Follow-ups inherit topic only, never caller-provided facts or numeric assertions.
    explicit=[m for m,p in METRICS.items() if re.search(p,q)]
    context=q
    followup=bool(history and re.search(r'what about|how about|^and\b|same|that|those|them|more|what should|what next',q))
    if not explicit and followup:
        context=history[-1].lower()+' '+q
    if re.search(r'forecast|predict|next year|next month|eligib|suitab|discount|pricing|profit|conversion|customer|policyholder|employee|salary|weather|stock price|expense|combined ratio|margin|revenue|commission|tax|investment|claim count|number of claims|how many claims|gross loss ratio',q):
        return unavailable('That is outside this financial dashboard’s verified data. I can compare GWP, NEP, net incurred claims and net loss ratio by business line, channel or month. Forecasts, pricing, customer details and eligibility are not available here.')
    if re.search(r'ignore.{0,30}(instruction|rule|evidence)|system prompt|drop table|execute.{0,15}sql|invent|fabricat',q):
        return unavailable('I can only answer from the verified financial results for the selected filters. I cannot execute user-supplied SQL or invent findings.')
    if not re.search(r'gwp|nep|premium|claim|loss|ratio|performance|plan|variance|channel|distribution|motor|travel|business line|underperform|shortfall|compare|trend|month',context):
        return unavailable('Ask about GWP, NEP, net incurred claims or net loss ratio for the selected dates, business lines and channels. For example: “Which channel has the largest GWP shortfall?”')
    years=re.findall(r'\b20\d{2}\b',q)
    if any(not int(scope['start'][:4])<=int(y)<=int(scope['end'][:4]) for y in years):
        return unavailable('The question refers to a year outside the selected reporting period. Change the date filters first; I will not substitute figures from another period.')
    if scope['line']!='All' and any(re.search(r'\b'+line.lower()+r'\b',q) for line in ['Motor','Travel'] if line!=scope['line']):
        return unavailable('That business line is outside the selected scope. Set Business line to All to compare Motor and Travel.')

    metric=('LOSS_RATIO' if re.search(METRICS['LOSS_RATIO'],context) else
            'NET_INCURRED_CLAIMS' if re.search(METRICS['NET_INCURRED_CLAIMS'],context) else
            'NEP' if re.search(METRICS['NEP'],context) else 'GWP')
    # Explicit new metric overrides earlier follow-up context.
    if explicit:
        metric=next((m for m in ['LOSS_RATIO','NET_INCURRED_CLAIMS','NEP','GWP'] if m in explicit),'GWP')
    dimension='MONTH' if re.search(r'month|trend|over time',q) else 'CHANNEL' if re.search(r'channel|distribution',q) else 'LINE' if re.search(r'motor|travel|line|underperform|shortfall',q) else 'TOTAL'
    target=q
    if followup and dimension=='TOTAL':
        previous=history[-1].lower()
        dimension='MONTH' if re.search(r'month|trend|over time',previous) else 'CHANNEL' if re.search(r'channel|distribution',previous) else 'LINE' if re.search(r'motor|travel|line|shortfall',previous) else 'TOTAL'
        target=previous
    channels=[str(x) for x in data.DISTRIBUTION_CHANNEL.dropna().unique()]
    requested_channels=[name for name in (available_channels or channels) if re.search(r'\b'+re.escape(name.lower())+r'\b',target)]
    if any(name not in channels for name in requested_channels):
        return unavailable('That distribution channel is outside the selected scope. Change the channel filter before asking about it.')
    named_channels=[name for name in channels if re.search(r'\b'+re.escape(name.lower())+r'\b',target)]
    if named_channels: dimension='CHANNEL'
    named_months=[i+1 for i,name in enumerate(MONTHS) if re.search(r'\b'+name+r'\b|\b'+name[:3]+r'\b',q) and name!='may']
    if re.search(r'\bmay\s+20\d{2}\b|\b(for|in|during|month)\s+may\b',q): named_months.append(5)
    if named_months: dimension='MONTH'
    rows=data.loc[data.LEVEL.eq(dimension)].copy()
    if dimension=='LINE':
        named=[line for line in ['Motor','Travel'] if re.search(r'\b'+line.lower()+r'\b',target)]
        if named: rows=rows.loc[rows.LINE_OF_BUSINESS.isin(named)]
    if named_channels: rows=rows.loc[rows.DISTRIBUTION_CHANNEL.isin(named_channels)]
    if named_months:
        dates=pd.to_datetime(rows.ACCOUNTING_MONTH)
        if any(m not in dates.dt.month.tolist() for m in named_months):
            return unavailable('The requested month is outside the selected reporting period. Change the date filters first.')
        rows=rows.loc[dates.dt.month.isin(named_months)]
        if years: rows=rows.loc[pd.to_datetime(rows.ACCOUNTING_MONTH).dt.year.isin([int(y) for y in years])]
    if rows.empty:
        return unavailable('The requested breakdown is not available under the active filters. Change the scope or ask about the selected portfolio.')
    comparison=bool(re.search(r'plan|variance|shortfall|underperform|below|above|gap',history[-1].lower()+' '+q if followup else q))
    if comparison and metric in ('GWP','NEP'):
        rows=rows.loc[rows[metric+'_VARIANCE'].notna()]
        if rows.empty:
            return unavailable('A comparable actual/plan variance is unavailable for this scope because coverage is incomplete. I will not treat missing comparisons as zero.')
    if dimension=='MONTH': rows=rows.sort_values('ACCOUNTING_MONTH')
    elif dimension!='TOTAL':
        field=metric+'_VARIANCE' if comparison and metric in ('GWP','NEP') else metric
        ascending=bool(comparison or re.search(r'lowest|smallest',q))
        if re.search(r'best|highest|above plan',q): ascending=metric=='LOSS_RATIO'
        rows=rows.sort_values(field,ascending=ascending,na_position='last')
    # For monthly trends, offer at most 24 aggregate rows; never raw customer data.
    rows=rows.head(24)
    facts=[fact(row,metric) for _,row in rows.iterrows()]
    ids=list(range(min(3,len(facts))))
    source='Calculated answer · Cortex disabled' if not ai else 'Calculated answer · AI optional'
    if ai:
        try:
            ids=validate_ai_selection({'evidence_ids':service.explain(facts,question=question)},len(facts))[:3]
            source='Cortex-assisted answer · verified SQL evidence'
        except Exception:
            source='Calculated answer · Cortex unavailable or response rejected'
    cause=bool(re.search(r'why|cause|reason|driver',q))
    answer=('The data identifies accounting contributions, but does not establish their causes. Here are the relevant verified results.' if cause else
            'Here are the verified results for the selected reporting scope.')
    if re.search(r'what.*(do|action)|recommend|investigat|improve',q):
        answer='Review the reported line and channel differences with the business owner. These results identify investigation areas, not proven causes or forecasts.'
    return {**response,'supported':True,'answer':answer,'source':source,
            'evidence':[{'id':i+1,'text':facts[i],'source':SOURCES} for i in ids]}
