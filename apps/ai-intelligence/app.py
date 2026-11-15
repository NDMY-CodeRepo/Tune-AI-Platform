"""Tune AI Intelligence — Streamlit entrypoint."""
from pathlib import Path
import sys

APP_DIRECTORY = Path(__file__).resolve().parent
IMPORT_ROOT = APP_DIRECTORY if (APP_DIRECTORY / 'shared').is_dir() else APP_DIRECTORY.parent.parent
if (IMPORT_ROOT / 'shared').is_dir() and str(IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(IMPORT_ROOT))

import hashlib
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from shared.business_logic import customer_evidence
from shared.snowflake_service import get_service, read
from shared.ui import setup_page, sidebar_brand, heading, connection_error, compact_amount, style_chart

setup_page('Tune AI Intelligence')
with st.sidebar:
    sidebar_brand('Tune AI Intelligence', 'BUSINESS INTELLIGENCE')
    module = st.radio('Workspace', ['Executive Intelligence', 'Next Best Action', 'Next Best Offer'], label_visibility='collapsed')
    st.divider()
    ai_enabled = st.toggle('Enable Cortex AI', value=True)
    st.caption('Grounded explanations. Calculated metrics and business rules work without AI.')
    if st.button('Refresh Snowflake data', use_container_width=True):
        read.clear()
        st.rerun()
    st.caption('Snowflake · Synthetic demo records')


def explanation(key, recommendation, facts, action):
    fingerprint = hashlib.sha256(json.dumps([recommendation, facts, action]).encode()).hexdigest()
    state_key = key + fingerprint
    label = 'Generate Engagement Brief' if key == 'NBO' else ('Explain performance' if key == 'EXEC' else 'Explain recommendation')
    if st.button(label, type='primary', key=key):
        ids, source = list(range(len(facts))), 'Deterministic explanation'
        if ai_enabled:
            try:
                with st.spinner('Cortex is selecting supporting evidence…'):
                    ids = get_service().explain(facts)
                source = 'AI-curated explanation · Snowflake Cortex'
            except Exception:
                source = 'Deterministic explanation · Cortex unavailable or response rejected'
        st.session_state[state_key] = (ids, source)
    if state_key in st.session_state:
        ids, source = st.session_state[state_key]
        with st.container(border=True):
            st.caption(source)
            st.markdown('**Recommendation**')
            st.write(recommendation)
            st.markdown('**Supporting evidence**')
            for i in ids:
                st.write('• ' + facts[i])
            st.markdown('**Suggested next action**')
            st.write(action)
            st.caption('Human review required. Findings describe observed contributions, not proven causes.' if key == 'EXEC' else 'Human review required. No message is sent. Confirm consent, suitability and eligibility before any offer.')


def customer_page(mode):
    nbo = mode == 'NBO'
    health = read('health')
    if health['ROW_COUNT'] != health['CUSTOMERS'] or health['SNAPSHOT_MIN'] != health['SNAPSHOT_MAX']:
        st.error('Customer grain has changed. Resolve duplicate customers or mixed snapshots before ranking.'); return
    overview = read('overview', mode)
    if overview.empty:
        st.info('No customers match the source segment.'); return
    total = int(overview.CUSTOMERS.sum())
    high_value = int(overview.loc[overview.LIFETIME_VALUE_BAND.isin(['High','Top']), 'CUSTOMERS'].sum())
    high_risk = int(overview.loc[overview.RETENTION_RISK_BAND.eq('High'), 'CUSTOMERS'].sum())
    high_both = int(overview.loc[overview.RETENTION_RISK_BAND.eq('High') & overview.LIFETIME_VALUE_BAND.isin(['High','Top']), 'CUSTOMERS'].sum())
    priority = int(overview.loc[overview.RETENTION_RISK_BAND.eq('Low') & overview.LIFETIME_VALUE_BAND.isin(['High','Top']), 'CUSTOMERS'].sum()) if nbo else int(read('retention_priorities')['PRIORITY_CUSTOMERS'] or 0)
    heading('Customer Growth Intelligence' if nbo else 'Retention Intelligence',
            'Next Best Offer · Existing relationships. Explainable opportunities. Human-led engagement.' if nbo else 'Next Best Action · Prioritize the relationships that need attention.')
    if nbo:
        st.subheader(f'{total:,} Motor-to-Travel cross-sell candidates')
    labels = ['Total candidates','High / Top value','High-risk candidates','Priority opportunities'] if nbo else ['Customers in portfolio','High-risk customers','High-value at risk','Priority retention opportunities']
    values = [total,high_value,high_risk,priority] if nbo else [total,high_risk,high_both,priority]
    for col,label,val in zip(st.columns(4),labels,values):
        help_text = ('Low retention risk and High/Top source customer value; a review segment, not a conversion prediction.' if nbo else 'High risk + High/Top value + renewal in the next three full calendar months after the snapshot.') if label in ('Priority opportunities','Priority retention opportunities') else None
        col.metric(label,f'{val:,}',help=help_text)
    st.caption(f"Snapshot {health['SNAPSHOT_MAX']} · Snowflake source data · Read cache up to 5 minutes · Customer value in RM")
    if nbo:
        st.caption('Candidate segment: Motor held · Travel not held · Existing next-best-product Travel · Marketing consent Yes. Eligibility, suitability and propensity are not established.')
        with st.expander('Opportunity segmentation · risk, value and engagement channel',expanded=False):
            left,right=st.columns([1.3,1])
            with left:
                st.markdown('**Customer value × retention risk**')
                segments=overview.pivot_table(index='LIFETIME_VALUE_BAND',columns='RETENTION_RISK_BAND',values='CUSTOMERS',aggfunc='sum',fill_value=0)
                segments=segments.reindex(index=[v for v in ['Top','High','Medium','Low'] if v in segments.index],columns=[v for v in ['Low','Medium','High'] if v in segments.columns])
                st.dataframe(segments.style.format('{:,.0f}'),use_container_width=True)
                st.caption('Priority opportunities = Low retention risk + High/Top customer value. This is an explainable review segment, not predicted conversion.')
            with right:
                channels=overview.groupby('PREFERRED_CHANNEL',as_index=False).CUSTOMERS.sum().sort_values('CUSTOMERS')
                fig=px.bar(channels,x='CUSTOMERS',y='PREFERRED_CHANNEL',orientation='h',color_discrete_sequence=['#182D4C'])
                fig.update_layout(xaxis_title=None,yaxis_title=None)
                st.plotly_chart(style_chart(fig,230),use_container_width=True,config={'displayModeBar':False})
    else:
        st.info('Priority review focuses on High-risk, High/Top-value customers renewing in the next three full calendar months after the snapshot. Missing renewal dates never qualify as upcoming.')
    with st.expander('How prioritization works'):
        window_start = pd.Timestamp(health['SNAPSHOT_MAX']).to_period('M').to_timestamp() + pd.DateOffset(months=1)
        window_end = window_start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
        st.write(f"Renewal window: the next three full calendar months after the customer snapshot ({window_start:%d %B %Y}–{window_end:%d %B %Y}). High value means High or Top source value band.")
        st.write('Offer ranking: Low risk before Medium before High; then lifetime value descending, renewal-window flag first, renewal month ascending, and customer ID. High-risk customers receive a retention-first next action.' if nbo else
                 'Action order: High risk + High/Top value + renewal window → Priority retention review; other High risk → Retention review; Medium risk + renewal window → Proactive renewal engagement; other Medium → Monitor retention needs; Low → Standard relationship maintenance. Ties: value, risk score, customer ID.')
        st.caption('Rules are demo business priorities, not a newly trained model. Risk and value bands come directly from Customer 360.')

    with st.container(border=True):
        a,b,c=st.columns(3)
        risk=a.selectbox('Retention risk',['All']+sorted(overview.RETENTION_RISK_BAND.dropna().unique()),key=mode+'risk')
        value=b.selectbox('Customer value',['All']+sorted(overview.LIFETIME_VALUE_BAND.dropna().unique()),key=mode+'value')
        channel=c.selectbox('Preferred channel',['All']+sorted(overview.PREFERRED_CHANNEL.dropna().unique()),key=mode+'channel')
    customers=read('customers',mode,risk,value,channel)
    if customers.empty:
        st.info('No customers match these filters. Try a broader segment.'); return
    list_col,profile_col=st.columns([1.65,1],gap='large')
    with list_col:
        st.subheader('Ranked candidates' if nbo else 'Retention worklist')
        st.caption(f"{int(customers.iloc[0].FILTERED_TOTAL):,} match these filters · Showing the first {len(customers):,} · Select a row to explore")
        cols=['CUSTOMER_ID','LIFETIME_VALUE','LIFETIME_VALUE_BAND','RETENTION_RISK_BAND','NEXT_RENEWAL_MONTH','PREFERRED_CHANNEL']
        if not nbo:
            cols.append('ACTION')
        selection=st.dataframe(customers[cols],hide_index=True,use_container_width=True,height=440,
            on_select='rerun',selection_mode='single-row',key=mode+str((risk,value,channel)),
            column_config={c:st.column_config.Column(c.replace('_',' ').title()) for c in cols} | {
                'CUSTOMER_ID':st.column_config.TextColumn('Customer'),
                'LIFETIME_VALUE':st.column_config.NumberColumn('Value (RM)',format='RM %.2f'),
                'LIFETIME_VALUE_BAND':st.column_config.TextColumn('Value band'),
                'RETENTION_RISK_BAND':st.column_config.TextColumn('Risk'),
                'NEXT_RENEWAL_MONTH':st.column_config.DateColumn('Renewal',format='MMM YYYY')})
        st.caption('Existing source attributes · Deterministic SQL ranking · No automatic customer contact')
    idx=selection.selection.rows[0] if selection.selection.rows else 0
    row=customers.iloc[idx].to_dict()
    recommendation,facts,action=customer_evidence(row,mode)
    with profile_col:
        st.subheader('Customer spotlight')
        with st.container(border=True):
            st.caption('SELECTED CUSTOMER' if selection.selection.rows else 'TOP-RANKED CUSTOMER · SELECT A ROW TO CHANGE')
            st.markdown('### '+row['CUSTOMER_ID'])
            a,b=st.columns(2)
            a.markdown('**'+compact_amount(row['LIFETIME_VALUE'])+'**')
            a.caption(row['LIFETIME_VALUE_BAND']+' customer value')
            b.markdown('**'+row['RETENTION_RISK_BAND']+' risk**')
            b.caption('Source score '+str(row['RETENTION_RISK_SCORE']))
            st.divider()
            st.markdown('**Travel · candidate for review**' if nbo else '**'+row['ACTION']+'**')
            st.write(action)
            renewal='Unavailable in source' if pd.isna(row['NEXT_RENEWAL_MONTH']) else str(row['NEXT_RENEWAL_MONTH'])[:7]
            st.caption(f"Renewal {renewal} · {row['PREFERRED_CHANNEL']}")
            st.caption(f"Active policies {row['ACTIVE_POLICY_COUNT']} · Marketing consent {row['MARKETING_CONSENT']}")
            with st.expander('Why this customer · supporting evidence',expanded=not nbo):
                for fact in facts:
                    st.write('• '+fact)
            st.divider()
            st.markdown('**Engagement brief**' if nbo else '**Recommended retention action**')
            st.caption('Grounded evidence, with an optional Cortex explanation.')
            explanation(mode,recommendation,facts,action)


def amount(value):
    return 'Unavailable' if pd.isna(value) else f'RM {float(value):,.2f}'


def percentage(value):
    return 'Unavailable' if pd.isna(value) else f'{float(value):,.1%}'


def executive_page():
    heading('Executive Intelligence', 'A clear view of financial performance. Actuals, plan and the gaps that matter.')
    options = read('financial_options')
    if options.empty:
        st.info('No accounting periods are available.'); return
    months = sorted(options.ACCOUNTING_MONTH.unique())
    a,b,c,d = st.columns([1,1,1,1.5])
    year_start = next((i for i,m in enumerate(months) if m.year == months[-1].year), 0)
    start = a.selectbox('From month', months, index=year_start, format_func=lambda x:x.strftime('%b %Y'))
    end = b.selectbox('To month', months, index=len(months)-1, format_func=lambda x:x.strftime('%b %Y'))
    line = c.selectbox('Business line', ['All','Motor','Travel'])
    channel = d.selectbox('Distribution channel', ['All']+sorted(options.DISTRIBUTION_CHANNEL.dropna().unique()))
    if start > end:
        st.warning('Choose an end month on or after the start month.'); return
    data = read('finance', str(start), str(end), line, channel)
    total = data.loc[data.LEVEL.eq('TOTAL')].iloc[0]
    if int(total.KEY_COUNT) == 0:
        st.info('No actual or plan data exists for this selection.'); return
    st.subheader(f'{start:%B %Y} – {end:%B %Y}')
    st.caption(f"{line if line != 'All' else 'Motor & Travel'} · {channel if channel != 'All' else 'All distribution channels'} · Monthly accounting movements")
    a,b,c,d=st.columns(4)
    for col,label,actual,plan,variance in [(a,'Gross written premium',total.GWP,total.PLAN_GWP,total.GWP_VARIANCE_PCT),(b,'Net earned premium',total.NEP,total.PLAN_NEP,total.NEP_VARIANCE_PCT)]:
        delta=None if pd.isna(variance) else percentage(variance)+(' · Below plan' if variance<0 else ' · At / above plan')
        col.metric(label,compact_amount(actual),delta,help=f'Actual {amount(actual)} · Plan {amount(plan)}')
        col.caption('Plan '+compact_amount(plan))
    c.metric('Net incurred claims',compact_amount(total.NET_INCURRED_CLAIMS),help=amount(total.NET_INCURRED_CLAIMS)+' · Net of reinsurance recoveries')
    d.metric('Net loss ratio',percentage(total.LOSS_RATIO),help='Net incurred claims / net earned premium. Plan claims basis remains unconfirmed.')
    st.caption('RM · SQL-calculated amounts · Read cache up to 5 minutes · Exact values in the financial detail below')
    gaps=int(total.MISSING_ACTUAL or 0)+int(total.MISSING_PLAN or 0)
    if gaps:
        st.warning(f'{gaps} month/entity/line/channel keys lack an actual or plan counterpart. Affected comparisons are unavailable; missing values are not treated as zero.')
    trend,contribution=st.columns([1.35,1],gap='large')
    with trend,st.container(border=True):
        st.subheader('Actual vs plan')
        metric=st.radio('Measure',['Gross written premium','Net earned premium'],horizontal=True)
        actual_col,plan_col=('GWP','PLAN_GWP') if metric=='Gross written premium' else ('NEP','PLAN_NEP')
        monthly=data.loc[data.LEVEL.eq('MONTH')].copy()
        plot=monthly[['ACCOUNTING_MONTH',actual_col,plan_col]].rename(columns={actual_col:'Actual',plan_col:'Plan'}).melt('ACCOUNTING_MONTH',var_name='Series',value_name='RM')
        fig=px.line(plot,x='ACCOUNTING_MONTH',y='RM',color='Series',markers=True,
                    color_discrete_map={'Actual':'#D81D46','Plan':'#8092AF'})
        fig.update_layout(xaxis_title=None,yaxis_title=None)
        fig.update_traces(hovertemplate='%{x|%b %Y}<br>RM %{y:,.2f}<extra>%{fullData.name}</extra>')
        fig.update_yaxes(tickprefix='RM ',tickformat='~s')
        st.plotly_chart(style_chart(fig),use_container_width=True,config={'displayModeBar':False})
    with contribution,st.container(border=True):
        st.subheader('Variance contribution')
        dimension=st.radio('Compare by',['Business line','Distribution channel'],horizontal=True)
        level,field=('LINE','LINE_OF_BUSINESS') if dimension=='Business line' else ('CHANNEL','DISTRIBUTION_CHANNEL')
        var='GWP_VARIANCE' if actual_col=='GWP' else 'NEP_VARIANCE'
        breakdown=data.loc[data.LEVEL.eq(level)].dropna(subset=[var]).copy().sort_values(var)
        if breakdown.empty:
            st.info('Comparable variance is unavailable for this selection.')
        else:
            breakdown['Position']=breakdown[var].map(lambda x:'Below plan' if x<0 else 'At / above plan')
            fig=px.bar(breakdown,x=var,y=field,color='Position',orientation='h',color_discrete_map={'Below plan':'#D81D46','At / above plan':'#237D75'})
            fig.update_layout(xaxis_title=None,yaxis_title=None)
            fig.update_traces(hovertemplate='%{y}<br>Variance RM %{x:,.2f}<extra></extra>')
            fig.update_xaxes(tickprefix='RM ',tickformat='~s')
            st.plotly_chart(style_chart(fig),use_container_width=True,config={'displayModeBar':False})
        st.caption('Premium variance = actual − plan. Red is unfavorable; green is favorable. These are contributions, not proven causes.')
    left,right = st.columns([1.2,1])
    with left:
        st.subheader('Financial detail')
        summary = pd.DataFrame([
            {'Metric':'Gross written premium','Actual':amount(total.GWP),'Plan':amount(total.PLAN_GWP),'Variance':amount(total.GWP_VARIANCE),'Variance %':percentage(total.GWP_VARIANCE_PCT)},
            {'Metric':'Net earned premium','Actual':amount(total.NEP),'Plan':amount(total.PLAN_NEP),'Variance':amount(total.NEP_VARIANCE),'Variance %':percentage(total.NEP_VARIANCE_PCT)},
            {'Metric':'Net incurred claims','Actual':amount(total.NET_INCURRED_CLAIMS),'Plan':'Basis unconfirmed','Variance':'Unavailable','Variance %':'Unavailable'},
        ])
        st.dataframe(summary,hide_index=True,use_container_width=True)
        st.caption(f'Gross claims paid: {amount(total.CLAIMS_PAID)} · Gross incurred claims: {amount(total.GROSS_INCURRED_CLAIMS)}')
        st.caption(f'Source plan incurred claims: {amount(total.PLAN_INCURRED_CLAIMS)}. Gross/net basis is undocumented; claims variance and planned loss ratio are withheld.')
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
    with right,st.container(border=True):
        st.caption('EXECUTIVE PERFORMANCE SUMMARY · CALCULATED')
        st.markdown('**'+recommendation+'**')
        for fact in facts:
            st.write(fact)
    st.subheader('Investigation brief')
    st.caption('Optional Cortex explanation · Verified facts only · Human interpretation required')
    explanation('EXEC',recommendation,facts,'Review the line and channel variances with the business owner. These are accounting contributions; source data does not establish causal drivers.')
    with st.expander('Definitions, coverage and SQL evidence'):
        st.write('Net incurred = gross claims paid + outstanding reserve movement + IBNR movement − reinsurance recoveries. Net loss ratio = net incurred / net earned premium; zero denominators return unavailable. Definition reconciles to GOLD.DERIVED_METRIC.LOSS_RATIO at runtime.')
        st.write('Actual grain: policy/accounting month. Plan grain: accounting month/entity/business line/distribution channel. Each is aggregated at plan grain, then full-joined on all four keys. Amount variance = actual − plan; percentage variance = amount variance / plan. No claim-cause filters or historical extrapolation are used.')
        st.dataframe(data,hide_index=True,use_container_width=True)


try:
    if module == 'Executive Intelligence':
        executive_page()
    else:
        customer_page('NBO' if module == 'Next Best Offer' else 'NBA')
except Exception:
    connection_error()
