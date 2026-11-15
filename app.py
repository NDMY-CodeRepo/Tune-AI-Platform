"""Tune AI Intelligence — Streamlit entrypoint."""
import hashlib
import json
import uuid
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from business_logic import customer_evidence, CATEGORIES, PRIORITIES, STATUSES, TRANSITIONS
from snowflake_service import get_service, read

LOGO_PATH = Path(__file__).resolve().parent / 'tune-protect-group-logo.png'
st.set_page_config(page_title='Tune AI Intelligence', page_icon=str(LOGO_PATH) if LOGO_PATH.is_file() else '✦', layout='wide')
st.markdown('''<style>
.block-container {max-width:1500px;padding-top:2.2rem;padding-bottom:2rem}
h1 {letter-spacing:-1.3px;font-weight:750!important} h3 {letter-spacing:-.5px}
[data-testid="stSidebar"] {border-right:1px solid #e6e9ef}
[data-testid="stMetric"] {background:white;border:1px solid #e5e9f0;border-radius:14px;padding:18px 20px}
[data-testid="stMetricLabel"] {color:#617086;font-size:13px}
[data-testid="stMetricValue"] {font-size:30px;font-weight:700}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px}
.eyebrow {font-size:11px;color:#D81D46;letter-spacing:2px;font-weight:750;margin-bottom:8px}
.subtitle {color:#64748b;margin-top:-8px;margin-bottom:24px}
</style>''', unsafe_allow_html=True)

with st.sidebar:
    if LOGO_PATH.is_file():
        st.image(str(LOGO_PATH), width=112)
    else:
        st.markdown('## Tune Protect Group')
    st.markdown('**Tune AI Intelligence**')
    st.divider()
    module = st.radio('Workspace', ['Next Best Offer', 'Next Best Action', 'Executive Intelligence', 'Data Service Desk'], label_visibility='collapsed')
    st.divider()
    ai_enabled = st.toggle('Enable Cortex AI', value=True)
    st.caption('AI is optional. Metrics and recommendations remain available without it.')
    if st.button('Refresh Snowflake data', use_container_width=True):
        read.clear()
        st.rerun()
    st.caption('Snowflake demo data · Synthetic source records')


def heading(title, subtitle, tag='TUNE PROTECT / INTELLIGENCE'):
    st.markdown(f'<div class="eyebrow">{tag}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


def chart(df, field, title):
    data = df.groupby(field, dropna=False)['CUSTOMERS'].sum().reset_index()
    fig = px.bar(data, x=field, y='CUSTOMERS', color=field,
                 color_discrete_sequence=['#D81D46', '#162D50', '#8498B6', '#EDA0B0', '#498E95'])
    fig.update_layout(height=230, showlegend=False, margin=dict(l=0,r=0,t=10,b=0),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      xaxis_title=None, yaxis_title=None, font=dict(color='#52627A'))
    st.markdown(f'**{title}**')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


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
    heading('Next Best Offer' if nbo else 'Next Best Action',
            'Turn existing Motor relationships into considered Travel conversations.' if nbo else 'Focus retention attention where customer value and renewal needs meet.')
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
    for col, label, val in zip(st.columns(4),
            ['Cross-sell candidates' if nbo else 'Customers in view', 'High / Top value', 'High retention risk', 'High-value at risk'],
            [total, high_value, high_risk, high_both]):
        col.metric(label, f'{val:,}')
    st.caption(f"Customer snapshot: {health['SNAPSHOT_MAX']} · Live Snowflake reads cached for up to 5 minutes · Values in MYR")
    if nbo:
        st.info('Motor held · Travel not held · Existing next-best-product = Travel · Marketing consent = Yes. This is a candidate segment; eligibility and propensity are not established.')
    else:
        st.caption('Some customer records have no next renewal month. These remain visible for relationship review and are not classified as upcoming renewals.')
    for col, field, title in zip(st.columns(3), ['RETENTION_RISK_BAND','LIFETIME_VALUE_BAND','PREFERRED_CHANNEL'], ['Retention risk','Customer value','Preferred engagement channel']):
        with col:
            chart(overview, field, title)
    with st.expander('How prioritization works'):
        window_start = pd.Timestamp(health['SNAPSHOT_MAX']).to_period('M').to_timestamp() + pd.DateOffset(months=1)
        window_end = window_start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
        st.write(f"Renewal window: the next three full calendar months after the customer snapshot ({window_start:%d %B %Y}–{window_end:%d %B %Y}). High value means High or Top source value band.")
        st.write('Offer ranking: Low risk before Medium before High; then lifetime value descending, renewal-window flag first, renewal month ascending, and customer ID. High-risk customers receive a retention-first next action.' if nbo else
                 'Action order: High risk + High/Top value + renewal window → Priority retention review; other High risk → Retention review; Medium risk + renewal window → Proactive renewal engagement; other Medium → Monitor retention needs; Low → Standard relationship maintenance. Ties: value, risk score, customer ID.')
        st.caption('Rules are demo business priorities, not a newly trained model. Risk and value bands come directly from Customer 360.')
    st.subheader('Prioritized customers')
    a,b,c = st.columns(3)
    risk = a.selectbox('Retention risk', ['All'] + sorted(overview.RETENTION_RISK_BAND.dropna().unique()), key=mode+'risk')
    value = b.selectbox('Customer value', ['All'] + sorted(overview.LIFETIME_VALUE_BAND.dropna().unique()), key=mode+'value')
    channel = c.selectbox('Preferred channel', ['All'] + sorted(overview.PREFERRED_CHANNEL.dropna().unique()), key=mode+'channel')
    customers = read('customers', mode, risk, value, channel)
    if customers.empty:
        st.info('No customers match these filters. Try a broader segment.'); return
    st.caption(f"Showing the first {len(customers):,} of {int(customers.iloc[0].FILTERED_TOTAL):,} matching customers. Select a row to inspect supporting facts.")
    cols = ['CUSTOMER_ID','LIFETIME_VALUE','LIFETIME_VALUE_BAND','RETENTION_RISK_BAND','NEXT_RENEWAL_MONTH','PREFERRED_CHANNEL','NEXT_BEST_PRODUCT' if nbo else 'ACTION']
    selection = st.dataframe(customers[cols], hide_index=True, use_container_width=True,
        on_select='rerun', selection_mode='single-row', key=mode+str((risk,value,channel)),
        column_config={c: st.column_config.Column(c.replace('_',' ').title()) for c in cols} | {
            'LIFETIME_VALUE':st.column_config.NumberColumn('Customer value (MYR)',format='%.2f')})
    idx = selection.selection.rows[0] if selection.selection.rows else 0
    row = customers.iloc[idx].to_dict()
    recommendation, facts, action = customer_evidence(row, mode)
    left,right = st.columns([1,1.6])
    with left, st.container(border=True):
        st.caption('CUSTOMER SPOTLIGHT')
        st.subheader(row['CUSTOMER_ID'])
        st.markdown('**Travel · candidate for review**' if nbo else '**'+row['ACTION']+'**')
        for fact in facts:
            st.write(fact)
        st.caption(f"Active policies: {row['ACTIVE_POLICY_COUNT']} · Marketing consent: {row['MARKETING_CONSENT']}")
    with right:
        st.subheader('Recommended next step')
        st.write(action)
        st.caption('Calculated ranking · Rule-based recommendation · Optional AI-curated evidence')
        explanation(mode, recommendation, facts, action)


def amount(value):
    return 'Unavailable' if pd.isna(value) else f'MYR {float(value):,.0f}'


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
    a,b,c,d = st.columns(4)
    a.metric('Gross written premium', amount(total.GWP), percentage(total.GWP_VARIANCE_PCT)+' vs plan' if pd.notna(total.GWP_VARIANCE_PCT) else None)
    b.metric('Net earned premium', amount(total.NEP), percentage(total.NEP_VARIANCE_PCT)+' vs plan' if pd.notna(total.NEP_VARIANCE_PCT) else None)
    c.metric('Net incurred claims', amount(total.NET_INCURRED_CLAIMS))
    d.metric('Net loss ratio', percentage(total.LOSS_RATIO))
    st.caption(f'{start:%B %Y}–{end:%B %Y} · MYR · Source movements aggregated before joining · Ratios calculated from summed amounts')
    gaps = int(total.MISSING_ACTUAL or 0)+int(total.MISSING_PLAN or 0)
    if gaps:
        st.warning(f'{gaps} month/entity/line/channel keys lack an actual or plan counterpart. Affected comparisons are unavailable; missing values are not treated as zero.')
    st.subheader('Monthly performance')
    monthly = data.loc[data.LEVEL.eq('MONTH')].copy()
    metric = st.radio('Measure',['Gross written premium','Net earned premium'],horizontal=True)
    actual_col,plan_col = ('GWP','PLAN_GWP') if metric=='Gross written premium' else ('NEP','PLAN_NEP')
    plot = monthly[['ACCOUNTING_MONTH',actual_col,plan_col]].rename(columns={actual_col:'Actual',plan_col:'Plan'}).melt('ACCOUNTING_MONTH', var_name='Series',value_name='MYR')
    fig = px.line(plot,x='ACCOUNTING_MONTH',y='MYR',color='Series',markers=True,
                  color_discrete_map={'Actual':'#D81D46','Plan':'#8092AF'})
    fig.update_layout(height=320,margin=dict(l=0,r=0,t=10,b=0),xaxis_title=None,yaxis_title='MYR',legend_title=None,
                      paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    left,right = st.columns([1.2,1])
    with left:
        st.subheader('Performance versus plan')
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
        st.caption('CALCULATED EXECUTIVE INSIGHT')
        st.markdown('**'+recommendation+'**')
        for fact in facts:
            st.write(fact)
    explanation('EXEC',recommendation,facts,'Review the line and channel variances with the business owner. These are accounting contributions; source data does not establish causal drivers.')
    with st.expander('Definitions, coverage and SQL evidence'):
        st.write('Net incurred = gross claims paid + outstanding reserve movement + IBNR movement − reinsurance recoveries. Net loss ratio = net incurred / net earned premium; zero denominators return unavailable. Definition reconciles to GOLD.DERIVED_METRIC.LOSS_RATIO at runtime.')
        st.write('Actual grain: policy/accounting month. Plan grain: accounting month/entity/business line/distribution channel. Each is aggregated at plan grain, then full-joined on all four keys. Amount variance = actual − plan; percentage variance = amount variance / plan. No claim-cause filters or historical extrapolation are used.')
        st.dataframe(data,hide_index=True,use_container_width=True)


def desk_page():
    heading('Data Service Desk','One place to request data, track work and see the outcome.', 'TUNE PROTECT / DATA OPERATIONS')
    st.caption('Demonstration role switching only. This selector is not authentication or authorization. All ticket access uses the connected Snowflake role.')
    role = st.radio('Demo role',['Business User','Data Team'],horizontal=True)
    st.session_state.setdefault('request_token','TP-'+str(uuid.uuid4()).upper())
    if 'last_ticket' in st.session_state:
        st.success('Request submitted · '+st.session_state.last_ticket)
    if role == 'Business User':
        st.session_state.setdefault('demo_identity','motor.demo')
        requester = st.text_input('Demo requester identity',value=st.session_state.demo_identity,max_chars=100)
        st.session_state.demo_identity = requester
        with st.expander('Submit a new data request',expanded=True):
            with st.form('new_request',clear_on_submit=False):
                a,b = st.columns(2)
                bu = a.selectbox('Business unit',['Motor','Travel','Finance','Claims','Distribution','Other'])
                category = b.selectbox('Request category',CATEGORIES)
                title = st.text_input('Request title',max_chars=200)
                description = st.text_area('Description',max_chars=4000)
                justification = st.text_area('Business justification',max_chars=2000)
                priority = st.selectbox('Priority',PRIORITIES,index=1)
                submit = st.form_submit_button('Submit request',type='primary')
            if submit:
                try:
                    token = st.session_state.request_token
                    # Recover an acknowledged or uncertain submission without duplicating it on retry.
                    existing = get_service().query('SELECT TICKET_ID FROM TUNE_BI_DB.APP_STATE.DATA_REQUEST_TICKET WHERE TICKET_ID=?',[token])
                    if existing.empty:
                        get_service().create_ticket(token,bu,requester,title,description,category,priority,justification)
                    st.session_state.last_ticket = token
                    st.session_state.request_token = 'TP-'+str(uuid.uuid4()).upper()
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))
        st.subheader('Your requests')
    else:
        requester = None
        st.subheader('Centralized request queue')
    a,b,c,d = st.columns([1,1,1,1])
    status = a.selectbox('Status',['All']+STATUSES)
    category_filter = b.selectbox('Category',['All']+CATEGORIES)
    priority_filter = c.selectbox('Priority filter',['All']+PRIORITIES)
    d.button('Refresh requests')  # Ticket reads are deliberately uncached.
    tickets = get_service().tickets(status,category_filter,priority_filter,requester)
    if tickets.empty:
        st.info('No requests match this view. Submit a request or broaden the filters.'); return
    st.caption(f'Showing {len(tickets)} most recent matching requests (maximum 200).')
    st.dataframe(tickets[['TICKET_ID','BUSINESS_UNIT','TITLE','CATEGORY','PRIORITY','ASSIGNED_TO','STATUS','UPDATED_AT']],hide_index=True,use_container_width=True)
    ticket_id = st.selectbox('Open request',tickets.TICKET_ID.tolist(),format_func=lambda x: x+' · '+tickets.loc[tickets.TICKET_ID.eq(x),'TITLE'].iloc[0])
    t = tickets.loc[tickets.TICKET_ID.eq(ticket_id)].iloc[0]
    with st.container(border=True):
        st.subheader(t.TITLE)
        st.caption(f'{t.TICKET_ID} · {t.STATUS} · Requested by {t.REQUESTER} · {t.BUSINESS_UNIT}')
        st.write(t.DESCRIPTION)
        st.markdown('**Business justification**'); st.write(t.BUSINESS_JUSTIFICATION)
        st.markdown('**Work progress**'); st.write(t.PROGRESS_NOTES or 'Awaiting a progress update.')
        st.markdown('**Resolution notes**'); st.write(t.RESOLUTION_NOTES or 'No resolution recorded yet.')
        st.caption(f'Created {t.CREATED_AT} · Updated {t.UPDATED_AT} (Snowflake timestamps)')
    if role == 'Data Team':
        with st.form('update_'+ticket_id+'_'+str(t.VERSION)):
            a,b = st.columns(2)
            owner = a.text_input('Assigned owner',value=t.ASSIGNED_TO or '',max_chars=100)
            allowed = TRANSITIONS[t.STATUS]
            new_status = b.selectbox('Update status',allowed,index=allowed.index(t.STATUS))
            progress = st.text_area('Work progress',value=t.PROGRESS_NOTES or '',max_chars=4000)
            notes = st.text_area('Resolution notes',value=t.RESOLUTION_NOTES or '',max_chars=4000)
            save = st.form_submit_button('Save ticket update',type='primary')
        if save:
            try:
                get_service().update_ticket(ticket_id,t.VERSION,t.STATUS,new_status,owner,progress,notes)
                st.session_state['ticket_update'] = ticket_id
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))
        if st.session_state.get('ticket_update') == ticket_id:
            st.success('Ticket update saved to Snowflake.')


try:
    if module in ('Next Best Offer', 'Next Best Action'):
        customer_page('NBO' if module == 'Next Best Offer' else 'NBA')
    elif module == 'Executive Intelligence':
        executive_page()
    else:
        desk_page()
except Exception:
    st.error('Snowflake data is temporarily unavailable. Check your connection, warehouse and object permissions, then refresh. No sample figures have been substituted.')
    st.caption('Connection setup and required privileges are documented in README.md.')
