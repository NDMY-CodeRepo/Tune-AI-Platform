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
from shared.ui import setup_page, sidebar_brand, heading, connection_error, compact_amount, style_chart, financial_cards, insight_heading, insight_lead, customer_profile

setup_page('Tune AI Intelligence')
with st.sidebar:
    sidebar_brand('Tune AI Intelligence', 'BUSINESS INTELLIGENCE')
    module = st.radio('Workspace', ['Executive Intelligence', 'Next Best Action', 'Next Best Offer'], label_visibility='collapsed')
    st.divider()
    ai_enabled = st.toggle('Enable Cortex AI', value=True)
    st.caption('Optional explanations from verified facts.')
    if st.button('Refresh Snowflake data', use_container_width=True):
        read.clear()
        st.rerun()
    st.caption('Snowflake · Synthetic demo records')


def explanation(key, recommendation, facts, action, default_ids=None, show_recommendation=True, show_action=True):
    fingerprint=hashlib.sha256(json.dumps([recommendation,facts,action]).encode()).hexdigest()
    state_key=key+fingerprint
    label='Generate Engagement Brief' if key=='NBO' else ('Explain performance' if key=='EXEC' else 'Explain recommendation')
    body=st.container()
    if st.button(label,type='primary',key=key,use_container_width=True):
        ids,source=list(range(len(facts))),'Deterministic explanation'
        if ai_enabled:
            try:
                with st.spinner('Preparing a grounded brief…'):
                    ids=get_service().explain(facts)
                source='AI-curated explanation · Snowflake Cortex'
            except Exception:
                source='Deterministic explanation · Cortex unavailable or response rejected'
        st.session_state[state_key]=(ids,source)
    selected=st.session_state.get(state_key)
    if selected is None and default_ids is not None:
        selected=(default_ids,'Calculated insight · Deterministic')
    if selected is not None:
        ids,source=selected
        with body:
            st.caption(source)
            if show_recommendation:
                st.markdown('**'+recommendation+'**')
            for i in ids[:3]:
                st.write('• '+facts[i])
            with st.expander('Full supporting evidence'):
                for i in ids:
                    st.write('• '+facts[i])
            if show_action:
                st.divider()
                st.markdown('**Suggested next action**')
                st.write(action)
            st.caption('Human review required. Contributions are not proven causes.' if key=='EXEC' else 'Human review required. No message is sent.')


def customer_page(mode):
    nbo=mode=='NBO'
    health=read('health')
    if health['ROW_COUNT']!=health['CUSTOMERS'] or health['SNAPSHOT_MIN']!=health['SNAPSHOT_MAX']:
        st.error('Customer grain has changed. Resolve duplicate customers or mixed snapshots before ranking.'); return
    overview=read('overview',mode)
    if overview.empty:
        st.info('No customers match the source segment.'); return
    total=int(overview.CUSTOMERS.sum())
    high_value=int(overview.loc[overview.LIFETIME_VALUE_BAND.isin(['High','Top']),'CUSTOMERS'].sum())
    high_risk=int(overview.loc[overview.RETENTION_RISK_BAND.eq('High'),'CUSTOMERS'].sum())
    high_both=int(overview.loc[overview.RETENTION_RISK_BAND.eq('High') & overview.LIFETIME_VALUE_BAND.isin(['High','Top']),'CUSTOMERS'].sum())
    priority=int(overview.loc[overview.RETENTION_RISK_BAND.eq('Low') & overview.LIFETIME_VALUE_BAND.isin(['High','Top']),'CUSTOMERS'].sum()) if nbo else int(read('retention_priorities')['PRIORITY_CUSTOMERS'] or 0)
    title,filters=st.columns([1.15,1],vertical_alignment='bottom',gap='medium')
    with title:
        heading('Customer Growth Intelligence' if nbo else 'Retention Intelligence',f'{total:,} Motor-to-Travel cross-sell candidates' if nbo else 'Prioritize the relationships that need attention.','TUNE PROTECT / AI INTELLIGENCE')
    with filters:
        a,b,c=st.columns(3,gap='small')
        risk=a.selectbox('Retention risk',['All']+sorted(overview.RETENTION_RISK_BAND.dropna().unique()),key=mode+'risk',label_visibility='collapsed',format_func=lambda x:'Risk: '+x)
        value=b.selectbox('Customer value',['All']+sorted(overview.LIFETIME_VALUE_BAND.dropna().unique()),key=mode+'value',label_visibility='collapsed',format_func=lambda x:'Value: '+x)
        channel=c.selectbox('Preferred channel',['All']+sorted(overview.PREFERRED_CHANNEL.dropna().unique()),key=mode+'channel',label_visibility='collapsed',format_func=lambda x:'Channel: '+x)
    labels=['Total candidates','High / Top value','High-risk candidates','Priority opportunities'] if nbo else ['Customers in portfolio','High-risk customers','High-value at risk','Priority retention opportunities']
    values=[total,high_value,high_risk,priority] if nbo else [total,high_risk,high_both,priority]
    for col,label,val in zip(st.columns(4),labels,values):
        help_text=('Low risk + High/Top customer value; a review segment, not a conversion prediction.' if nbo else 'High risk + High/Top value + renewal in the next three full months after the snapshot.') if label in ('Priority opportunities','Priority retention opportunities') else None
        col.metric(label,f'{val:,}',help=help_text)
    st.caption(f"Portfolio snapshot {health['SNAPSHOT_MAX']} · Cards describe the full segment; filters refine the worklist · Values in RM")
    customers=read('customers',mode,risk,value,channel)
    if customers.empty:
        st.info('No customers match these filters. Try a broader segment.'); return
    list_col,profile_col=st.columns([3.1,1.15],gap='medium')
    with list_col,st.container(border=True,key='panel-worklist'):
        st.subheader('Ranked candidates' if nbo else 'Retention worklist')
        st.caption(f"{int(customers.iloc[0].FILTERED_TOTAL):,} match · Top {len(customers):,} shown · Select a row to explore")
        cols=['CUSTOMER_ID','LIFETIME_VALUE','LIFETIME_VALUE_BAND','RETENTION_RISK_BAND','NEXT_RENEWAL_MONTH','PREFERRED_CHANNEL']
        if not nbo:
            cols.append('ACTION')
        selection=st.dataframe(customers[cols],hide_index=True,use_container_width=True,height=370,
            on_select='rerun',selection_mode='single-row',key=mode+str((risk,value,channel)),
            column_config={c:st.column_config.Column(c.replace('_',' ').title()) for c in cols} | {
                'CUSTOMER_ID':st.column_config.TextColumn('Customer',width='small'),
                'LIFETIME_VALUE':st.column_config.NumberColumn('Value (RM)',format='%.2f',width='small'),
                'LIFETIME_VALUE_BAND':st.column_config.TextColumn('Value band',width='small'),
                'RETENTION_RISK_BAND':st.column_config.TextColumn('Risk',width='small'),
                'NEXT_RENEWAL_MONTH':st.column_config.DateColumn('Renewal',format='MMM YYYY',width='small'),
                'PREFERRED_CHANNEL':st.column_config.TextColumn('Channel'),
                'ACTION':st.column_config.TextColumn('Recommended action')})
    idx=selection.selection.rows[0] if selection.selection.rows else 0
    row=customers.iloc[idx].to_dict()
    recommendation,facts,action=customer_evidence(row,mode)
    with profile_col,st.container(border=True,key='panel-customer'):
        customer_profile(row['CUSTOMER_ID'],compact_amount(row['LIFETIME_VALUE']),row['LIFETIME_VALUE_BAND'],row['RETENTION_RISK_BAND'],row['RETENTION_RISK_SCORE'])
        st.caption('Selected customer' if selection.selection.rows else 'Top-ranked customer · Select a table row to change')
        st.markdown('**Travel · candidate for review**' if nbo else '**Recommended retention action**')
        insight_lead(action)
        renewal='Unavailable in source' if pd.isna(row['NEXT_RENEWAL_MONTH']) else pd.Timestamp(row['NEXT_RENEWAL_MONTH']).strftime('%b %Y')
        st.write('**Renewal**  '+renewal)
        st.write('**Preferred channel**  '+row['PREFERRED_CHANNEL'])
        st.caption(f"{row['ACTIVE_POLICY_COUNT']} active policies · Marketing consent: {row['MARKETING_CONSENT']}")
        explanation(mode,recommendation,facts,action,show_recommendation=False,show_action=False)
        st.caption('Eligibility and suitability require human review.' if nbo else 'Confirm the permitted contact route. No automatic engagement.')
    with st.expander('Segment definitions & methodology'):
        st.caption('Existing source attributes · SQL ranking · Optional Cortex explanations · No model training')
        if nbo:
            st.write('Motor held, Travel not held, existing next-best-product Travel and marketing consent Yes. This candidate segment does not establish eligibility, suitability or propensity.')
            st.write('Priority opportunity segment: Low retention risk + High/Top customer value.')
            st.markdown('**Customer value × retention risk**')
            segments=overview.pivot_table(index='LIFETIME_VALUE_BAND',columns='RETENTION_RISK_BAND',values='CUSTOMERS',aggfunc='sum',fill_value=0)
            st.dataframe(segments.style.format('{:,.0f}'),use_container_width=True)
        else:
            st.write('Customers with missing renewal dates remain visible but are never classified as upcoming renewals.')
        window_start=pd.Timestamp(health['SNAPSHOT_MAX']).to_period('M').to_timestamp()+pd.DateOffset(months=1)
        window_end=window_start+pd.DateOffset(months=3)-pd.Timedelta(days=1)
        st.write(f'Renewal window: {window_start:%d %B %Y}–{window_end:%d %B %Y}, the next three full months after the snapshot. High value means High or Top source band.')
        st.write('Offer ranking: Low risk, then Medium, then High; lifetime value descending, upcoming-renewal flag first, renewal month ascending and customer ID.' if nbo else 'Priority retention review: High risk + High/Top value + renewal window. Other High risk: Retention review. Medium + renewal window: Proactive renewal engagement. Other Medium: Monitor retention needs. Low: Standard relationship maintenance. Ties: value, risk score and customer ID.')
        st.caption('Source reads are cached for up to five minutes. Use Refresh Snowflake data before presenting.')


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


def executive_page():
    options=read('financial_options')
    if options.empty:
        st.info('No accounting periods are available.'); return
    months=sorted(options.ACCOUNTING_MONTH.unique())
    year_start=next((i for i,m in enumerate(months) if m.year==months[-1].year),0)
    title,filters=st.columns([1.1,1],vertical_alignment='bottom',gap='medium')
    with title:
        heading('Executive Intelligence','A clear view of financial performance, actuals and plan.','TUNE PROTECT / AI INTELLIGENCE')
    with filters:
        period,business,distribution=st.columns([1.15,1,1],gap='small')
        current_start=st.session_state.get('finance_start',months[year_start])
        current_end=st.session_state.get('finance_end',months[-1])
        with period.popover(f'{current_start:%b %Y} – {current_end:%b %Y}',icon=':material/date_range:',use_container_width=True):
            start=st.selectbox('From month',months,index=year_start,format_func=lambda x:x.strftime('%b %Y'),key='finance_start')
            end=st.selectbox('To month',months,index=len(months)-1,format_func=lambda x:x.strftime('%b %Y'),key='finance_end')
        line=business.selectbox('Business line',['All','Motor','Travel'],label_visibility='collapsed',format_func=lambda x:'Business: '+x)
        channel=distribution.selectbox('Distribution channel',['All']+sorted(options.DISTRIBUTION_CHANNEL.dropna().unique()),label_visibility='collapsed',format_func=lambda x:'Channel: '+x)
    if start>end:
        st.warning('Choose an end month on or after the start month.'); return
    period_label=f'{start:%b %Y}–{end:%b %Y}' if start.year!=end.year else f'{start:%b}–{end:%b %Y}'
    data=read('finance',str(start),str(end),line,channel)
    total=data.loc[data.LEVEL.eq('TOTAL')].iloc[0]
    if int(total.KEY_COUNT)==0:
        st.info('No actual or plan data exists for this selection.'); return
    cards=[]
    for label,actual,plan,variance,symbol in [('Gross written premium',total.GWP,total.PLAN_GWP,total.GWP_VARIANCE_PCT,'layers'),('Net earned premium',total.NEP,total.PLAN_NEP,total.NEP_VARIANCE_PCT,'shield')]:
        if pd.isna(variance):
            detail='Comparable plan unavailable'
        else:
            color='negative' if variance<0 else 'positive'
            arrow='↓' if variance<0 else '↑'
            detail=f'<span class="{color}">{arrow} {percentage(variance)}</span> vs plan ({compact_amount(plan)})'
        cards.append((label,compact_amount(actual),detail,symbol,'rose' if pd.notna(variance) and variance<0 else '',f'Actual {amount(actual)} · Plan {amount(plan)}'))
    cards.extend([
        ('Net incurred claims',compact_amount(total.NET_INCURRED_CLAIMS),'Net of reinsurance recoveries','document','',amount(total.NET_INCURRED_CLAIMS)),
        ('Net loss ratio',percentage(total.LOSS_RATIO),'Plan comparison unavailable','percent','',percentage(total.LOSS_RATIO)),
    ])
    financial_cards(cards)
    gaps=int(total.MISSING_ACTUAL or 0)+int(total.MISSING_PLAN or 0)
    if gaps:
        st.warning(f'{gaps} accounting keys lack an actual or plan counterpart. Affected comparisons are unavailable.')
    main,insight=st.columns([3.1,1.05],gap='medium')
    with main:
        trend,contribution=st.columns([1.65,1],gap='medium')
        with trend,st.container(border=True,key='panel-trend'):
            st.subheader('Monthly premium')
            with st.popover('GWP / NEP'):
                metric=st.radio('Measure',['Gross written premium','Net earned premium'])
            actual_col,plan_col=('GWP','PLAN_GWP') if metric=='Gross written premium' else ('NEP','PLAN_NEP')
            monthly=data.loc[data.LEVEL.eq('MONTH')].copy()
            plot=monthly[['ACCOUNTING_MONTH',actual_col,plan_col]].rename(columns={actual_col:'Actual',plan_col:'Plan'}).melt('ACCOUNTING_MONTH',var_name='Series',value_name='RM')
            fig=px.line(plot,x='ACCOUNTING_MONTH',y='RM',color='Series',markers=True,color_discrete_map={'Actual':'#E20836','Plan':'#6884AA'})
            fig.update_traces(line_width=2,marker_size=6,marker_color='white',marker_line_width=1.8,hovertemplate='%{x|%b %Y}<br>RM %{y:,.2f}<extra>%{fullData.name}</extra>')
            for trace in fig.data:
                trace.marker.line.color=trace.line.color
                if trace.name=='Actual':
                    trace.fill='tozeroy';trace.fillcolor='rgba(226,8,54,0.06)'
            numbers=pd.to_numeric(plot.RM,errors='coerce').dropna()
            if not numbers.empty:
                low,high=float(numbers.min()),float(numbers.max())
                pad=(high-low)*.18 or abs(high)*.1 or 1
                fig.update_yaxes(range=[low-pad,high+pad])
            fig.update_layout(xaxis_title=None,yaxis_title=None)
            fig.update_yaxes(tickprefix='RM ',tickformat='.3s')
            fig.update_xaxes(dtick='M1' if len(monthly)<=12 else 'M3',tickformat='%b' if start.year==end.year else '%b %y')
            st.plotly_chart(style_chart(fig,245),use_container_width=True,config={'displayModeBar':False})
            st.caption(metric+' · '+f'{start:%b %Y}–{end:%b %Y}')
        with contribution,st.container(border=True,key='panel-variance'):
            st.subheader('Variance contribution')
            with st.popover('Breakdown'):
                dimension=st.radio('Compare by',['Business line','Distribution channel'])
            level,field=('LINE','LINE_OF_BUSINESS') if dimension=='Business line' else ('CHANNEL','DISTRIBUTION_CHANNEL')
            var='GWP_VARIANCE' if actual_col=='GWP' else 'NEP_VARIANCE'
            breakdown=data.loc[data.LEVEL.eq(level)].dropna(subset=[var]).copy().sort_values(var,ascending=False)
            if breakdown.empty:
                st.info('Comparable variance is unavailable.')
            else:
                breakdown['Position']=breakdown[var].map(lambda x:'Below plan' if x<0 else 'At / above plan')
                breakdown['Label']=breakdown[var].map(compact_amount)
                fig=px.bar(breakdown,x=var,y=field,color='Position',orientation='h',text='Label',color_discrete_map={'Below plan':'#E20836','At / above plan':'#237D75'})
                fig.update_layout(xaxis_title=None,yaxis_title=None,showlegend=False,bargap=.52)
                fig.update_traces(textposition='auto',textfont_size=11,hovertemplate='%{y}<br>Variance RM %{x:,.2f}<extra></extra>')
                fig.update_xaxes(tickprefix='RM ',tickformat='.2s')
                st.plotly_chart(style_chart(fig,245),use_container_width=True,config={'displayModeBar':False})
            st.caption(('GWP' if actual_col=='GWP' else 'NEP')+' · Red below plan / green above plan')
        with st.container(border=True,key='panel-detail'):
            st.subheader('Financial detail')
            summary=pd.DataFrame([
                {'Metric':'Gross written premium','Actual':amount(total.GWP),'Plan':amount(total.PLAN_GWP),'Variance':amount(total.GWP_VARIANCE),'Variance %':percentage(total.GWP_VARIANCE_PCT)},
                {'Metric':'Net earned premium','Actual':amount(total.NEP),'Plan':amount(total.PLAN_NEP),'Variance':amount(total.NEP_VARIANCE),'Variance %':percentage(total.NEP_VARIANCE_PCT)},
                {'Metric':'Net incurred claims','Actual':amount(total.NET_INCURRED_CLAIMS),'Plan':'Not comparable','Variance':'—','Variance %':'—'},
                {'Metric':'Net loss ratio','Actual':percentage(total.LOSS_RATIO),'Plan':'Not established','Variance':'—','Variance %':'—'},
            ])
            st.dataframe(summary,hide_index=True,use_container_width=True,height=178)
            st.caption('Claims-plan gross/net basis is unconfirmed; claims and loss-ratio comparisons are withheld.')
    recommendation,facts=financial_narrative(data,total)
    with insight,st.container(border=True,key='panel-insights'):
        insight_heading(pill='Cortex optional' if ai_enabled else 'Rules & SQL')
        if pd.notna(total.GWP_VARIANCE):
            percent_note='' if pd.isna(total.GWP_VARIANCE_PCT) else f' ({percentage(abs(total.GWP_VARIANCE_PCT))})'
            lead=(f'GWP is in line with plan for {period_label}.' if total.GWP_VARIANCE==0 else
                  f'GWP is {compact_amount(abs(total.GWP_VARIANCE))}{percent_note} '+('below' if total.GWP_VARIANCE<0 else 'above')+f' plan for {period_label}.')
        else:
            lead='Comparable GWP variance is unavailable for this selection.'
        insight_lead(lead)
        explanation('EXEC',recommendation,facts,'Review business-line performance by channel and segment to identify areas requiring investigation. Observed contributions do not establish causes.',default_ids=list(range(3,len(facts)))[:3] or [0],show_recommendation=False)
    with st.expander('Reporting basis & source evidence'):
        st.write('Net incurred = gross claims paid + outstanding reserve movement + IBNR movement − reinsurance recoveries. Net loss ratio = net incurred / net earned premium; zero denominators return unavailable. Definition reconciles to GOLD.DERIVED_METRIC.LOSS_RATIO at runtime.')
        st.write('Actual grain: policy/accounting month. Plan grain: accounting month/entity/business line/distribution channel. Each is aggregated at plan grain before joining. Amount variance = actual − plan; percentage variance = amount variance / plan.')
        st.caption(f'Gross claims paid: {amount(total.CLAIMS_PAID)} · Gross incurred: {amount(total.GROSS_INCURRED_CLAIMS)} · Source plan incurred: {amount(total.PLAN_INCURRED_CLAIMS)} (basis unconfirmed)')
        st.caption('Snowflake synthetic demo records · Read cache up to five minutes · Exact amounts shown above')
        st.dataframe(data,hide_index=True,use_container_width=True)


try:
    if module == 'Executive Intelligence':
        executive_page()
    else:
        customer_page('NBO' if module == 'Next Best Offer' else 'NBA')
except Exception:
    connection_error()
