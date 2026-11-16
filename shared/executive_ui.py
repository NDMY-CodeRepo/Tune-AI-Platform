"""Presentation scoped to the AI sidebar and Executive Intelligence only."""
import hashlib
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from .ui import compact_amount, insight_heading, insight_lead, style_chart
from .executive_analytics import ranked_variance, portfolio_frame, channel_scorecard


def sidebar_styles():
    # Only the AI app opts into this container; the separate desk is unaffected.
    # aria-expanded is the native sidebar collapse state in the pinned runtime.
    st.markdown('''<style>
    [data-testid="stSidebar"]:has(.st-key-ai-sidebar)[aria-expanded="true"] {width:252px!important;min-width:252px!important;max-width:252px!important;background:#fff}
    [data-testid="stSidebar"]:has(.st-key-ai-sidebar)[aria-expanded="false"] {width:0!important;min-width:0!important;max-width:0!important}
    [data-testid="stSidebar"]:has(.st-key-ai-sidebar) [data-testid="stSidebarHeader"] {position:relative!important;top:auto!important;right:auto!important;padding:.3rem .7rem!important;margin:0!important;justify-content:flex-end}
    [data-testid="stSidebar"]:has(.st-key-ai-sidebar) [data-testid="stSidebarContent"] {overflow-y:auto;overflow-x:hidden;height:100%}
    [data-testid="stSidebar"]:has(.st-key-ai-sidebar) [data-testid="stSidebarUserContent"] {padding:.15rem .85rem 1rem!important}
    .st-key-ai-sidebar {min-height:calc(100dvh - 70px);display:flex;flex-direction:column}
    .st-key-ai-sidebar .brand {padding:0 .4rem .5rem}
    .st-key-ai-sidebar .brand img {width:54px;height:54px;margin-bottom:8px}
    .st-key-ai-sidebar .brand-name {font-size:15px;font-weight:500;margin-bottom:8px;color:#1D2D49}
    .st-key-ai-sidebar .brand-area {display:none}
    .st-key-ai-sidebar .brand-app {font-size:15px;font-weight:500;color:#1D2D49}
    .st-key-ai-sidebar hr {margin:.35rem 0!important}
    .st-key-ai-sidebar [class*="st-key-ai-nav-"] button {justify-content:flex-start;min-height:38px;padding:.45rem .6rem;font-size:13px;font-weight:400;border-radius:8px;border:0;border-left:3px solid transparent;box-shadow:none;color:#1D2D49;white-space:nowrap}
    .st-key-ai-sidebar [class*="st-key-ai-nav-"] button p {font-size:13px;line-height:1.4;font-weight:inherit;white-space:nowrap}
    .st-key-ai-sidebar [class*="st-key-ai-nav-"] button:hover {background:#F8F6F5}
    .st-key-ai-sidebar [class*="st-key-ai-nav-"] button:focus-visible {outline:2px solid #D71942;outline-offset:2px}
    .st-key-ai-sidebar [class*="-active"] button {background:#FCEEF1!important;border-left-color:#D71942!important;color:#B51235!important;font-weight:500}
    .st-key-ai-sidebar [class*="st-key-ai-nav-"] {margin:0}
    .st-key-ai-sidebar .st-key-ai-utilities button {min-height:32px;padding:.25rem;font-size:13px}
    .st-key-ai-sidebar .st-key-ai-utilities {margin-top:auto!important;padding-top:.75rem;border-top:1px solid #E6E9EF}
    </style>''',unsafe_allow_html=True)


def executive_styles():
    # Own container keys scope the overrides; no random/generated CSS classes.
    st.markdown('''<style>
    [data-testid="stAppViewContainer"]:has(.st-key-executive-page) {background:#fff}
    .st-key-executive-page {color:#1D2D49;min-width:0;gap:1rem!important;background:#fff}
    .st-key-executive-page h1 {font-size:28px!important;font-weight:500!important;letter-spacing:-.5px}
    .st-key-executive-page h2,.st-key-executive-page h3 {font-weight:500!important;color:#1D2D49}
    .st-key-executive-page .eyebrow {color:#D71942;font-size:10px;margin-bottom:5px}
    .st-key-executive-page .subtitle {font-size:13px;margin-bottom:0;color:#58657A}
    .st-key-executive-page [data-testid="stVerticalBlock"] {gap:.75rem}
    .st-key-exec-header {gap:.25rem!important}
    .st-key-exec-filters button p {white-space:nowrap}
    .st-key-exec-filters button {box-shadow:none!important;min-height:36px}
    .st-key-exec-filters {max-width:none;margin:0}
    .st-key-executive-page .kpi-grid {gap:1rem;margin:0 0 10px 0}
    .st-key-executive-page .kpi-card {background:#fff;box-shadow:none;border:1px solid #E6E9EF;border-radius:12px;min-height:110px;padding:16px;gap:10px}
    .st-key-executive-page .kpi-card.rose {background:#fff}
    .st-key-executive-page .kpi-icon {width:30px;height:30px;min-width:30px;background:#fff;color:#D71942}
    .st-key-executive-page .kpi-icon svg {width:18px;height:18px}
    .st-key-executive-page .kpi-label {font-size:12px;font-weight:400;margin-bottom:7px;color:#536078}
    .st-key-executive-page .kpi-value {font-size:clamp(22px,1.85vw,30px);font-weight:500;color:#1D2D49;overflow:visible;white-space:normal}
    .st-key-executive-page .kpi-detail {font-size:11px;margin-top:7px;color:#536078}
    .st-key-executive-page [class*="st-key-panel-"] {box-shadow:none!important;border-color:#E6E9EF!important;border-radius:12px;background:#fff}
    .st-key-executive-page .insight-label {font-size:17px;font-weight:500;margin-bottom:8px;color:#1D2D49}
    .st-key-executive-page .insight-lead {font-size:14px;font-weight:500;padding:0;margin-bottom:0;background:#fff;border-radius:0;line-height:1.6}
    .st-key-executive-page .insight-pill {font-size:10px;font-weight:400;background:#fff;border:1px solid #E6E9EF}
    .st-key-panel-trend {margin-top:1rem!important}
    .st-key-executive-page [class*="st-key-panel-score-"] [data-testid="stMetricValue"] {font-size:clamp(20px,1.7vw,28px);font-weight:500;color:#1D2D49;white-space:normal}
    .st-key-executive-page [class*="st-key-panel-score-"] [data-testid="stMetricLabel"] p {font-size:12px;font-weight:400;color:#536078}
    .st-key-executive-page [class*="st-key-score-"] [data-testid="stMetricValue"] {font-size:30px}
    .st-key-panel-insights .insight-label {font-size:20px}
    .st-key-panel-insights p {font-size:13px;line-height:1.5}
    .st-key-panel-insights [data-testid="stCaptionContainer"] p {font-size:11px;letter-spacing:.3px;color:#59677A!important}
    .st-key-panel-insights button {font-weight:500;font-size:13px}
    .st-key-executive-page .negative {color:#D71942}
    .st-key-executive-page [data-testid="stColumn"] {min-width:0}
    @media(max-width:1100px) {
      .st-key-executive-page [data-testid="stHorizontalBlock"] {flex-direction:column!important;gap:.8rem}
      .st-key-executive-page [data-testid="stColumn"] {width:100%!important;flex:1 1 100%!important}
      .st-key-executive-page .kpi-grid {grid-template-columns:repeat(2,minmax(0,1fr))}
    }
    </style>''',unsafe_allow_html=True)


def _delta_sentence(label,value,ratio=None):
    if pd.isna(value):
        return f'{label}: comparison unavailable.'
    if value==0:
        return f'{label}: in line with plan.'
    percent='' if ratio is None or pd.isna(ratio) else f' ({abs(float(ratio)):.1%})'
    direction='below' if value<0 else 'above'
    return f'{label}: {compact_amount(abs(value))} {direction} plan{percent}.'


def compact_evidence(data,total):
    """Short display counterparts to financial_narrative's verified fact IDs."""
    short=[_delta_sentence('GWP',total.GWP_VARIANCE,total.GWP_VARIANCE_PCT),
           _delta_sentence('NEP',total.NEP_VARIANCE,total.NEP_VARIANCE_PCT),
           f'Net loss ratio: {float(total.LOSS_RATIO):.1%}.' if pd.notna(total.LOSS_RATIO) else 'Net loss ratio: unavailable.']
    lines=data.loc[data.LEVEL.eq('LINE')].sort_values('GWP_VARIANCE',na_position='last')
    for _,row in lines.iterrows():
        short.append(_delta_sentence(row.LINE_OF_BUSINESS,row.GWP_VARIANCE,row.GWP_VARIANCE_PCT))
    channels=data.loc[data.LEVEL.eq('CHANNEL')].sort_values('GWP_VARIANCE',na_position='last')
    if not channels.empty and pd.notna(channels.iloc[0].GWP_VARIANCE):
        row=channels.iloc[0]
        short.append(_delta_sentence(row.DISTRIBUTION_CHANNEL,row.GWP_VARIANCE))
    return short


def executive_insights(finding,facts,short_facts,default_ids,action,ai_enabled,explain):
    """One bounded panel; Cortex selects verified evidence, never new claims."""
    fingerprint=hashlib.sha256(json.dumps([finding,facts,action]).encode()).hexdigest()
    state_key='executive-brief-'+fingerprint
    saved=st.session_state.get(state_key)
    ids,source=saved if saved else (default_ids,'Calculated results · AI optional')
    title,controls=st.columns([4,1.25],vertical_alignment='center',gap='medium')
    with title:
        insight_heading('AI performance insights',pill='Cortex AI' if ai_enabled else 'Rules & SQL')
    button_slot=controls.empty()
    finding_col,contributors_col,action_col=st.columns([1.2,1.4,1.2],gap='medium')
    with finding_col:
        st.caption('KEY FINDING')
        insight_lead(finding)
    with contributors_col:
        st.caption('TOP CONTRIBUTORS')
        for i in ids[:3]:
            st.write('• '+short_facts[i])
    with action_col:
        st.caption('SUGGESTED ACTION')
        st.write(action)
    status_slot=st.empty()
    if button_slot.button('Explain performance',key='EXEC',type='primary',use_container_width=True):
        button_slot.empty()
        button_slot.button('Preparing explanation…',key='EXEC-loading',disabled=True,use_container_width=True)
        selected_ids=list(default_ids)
        explanation_source='Deterministic explanation'
        if ai_enabled:
            try:
                with status_slot.container(),st.spinner('Checking supporting evidence with Cortex…'):
                    selected_ids=explain(facts)
                explanation_source='AI-curated explanation · Snowflake Cortex'
            except Exception:
                explanation_source='Deterministic explanation · Cortex unavailable or response rejected'
        st.session_state[state_key]=(selected_ids,explanation_source)
        st.rerun()
    st.caption(source)
    with st.expander('Supporting evidence',expanded=False):
        for fact in facts:
            st.write('• '+fact)
        st.caption('Exact amounts are also shown in Financial detail. Human review required; accounting contributions do not establish causes.')


def variance_chart(data,level,metric):
    field='LINE_OF_BUSINESS' if level=='LINE' else 'DISTRIBUTION_CHANNEL'
    rows,excluded=ranked_variance(data,level,metric)
    if rows.empty:
        st.info('No fully comparable actual/plan groups for this selection.')
        return
    value=metric+'_VARIANCE'
    rows['Position']=rows[value].map(lambda x:'Below plan' if x<0 else 'At / above plan')
    rows['Label']=rows[value].map(compact_amount)
    fig=px.bar(rows,x=value,y=field,color='Position',orientation='h',text='Label',
        color_discrete_map={'Below plan':'#D71942','At / above plan':'#237D75'})
    fig.update_layout(xaxis_title=None,yaxis_title=None,showlegend=False,bargap=.35)
    fig.update_traces(textposition='auto',hovertemplate='%{y}<br>Variance RM %{x:,.2f}<extra></extra>')
    fig.update_xaxes(tickprefix='RM ',tickformat='~s')
    fig.update_yaxes(categoryorder='array',categoryarray=rows[field].tolist(),autorange='reversed')
    st.plotly_chart(style_chart(fig,280),use_container_width=True,config={'displayModeBar':False})
    st.caption(f'{metric} actual − plan · {excluded} incomplete/unavailable groups excluded')


def portfolio_chart(data,level,metric):
    field='LINE_OF_BUSINESS' if level=='LINE' else 'DISTRIBUTION_CHANNEL'
    rows=portfolio_frame(data,level,metric)
    if rows.empty:
        st.info('Premium shares are unavailable: missing, negative or zero-total actual premium.')
        return
    fig=px.pie(rows,names=field,values=metric+'_SHARE',hole=.65,
        custom_data=[metric,metric+'_SHARE'],
        color_discrete_sequence=['#D71942','#7289A9','#243D60','#A6B8C6','#6B8C88','#C59B9F'])
    fig.update_traces(textinfo='percent',textposition='inside',
        hovertemplate='%{label}<br>RM %{customdata[0]:,.2f}<br>%{customdata[1]:.1%}<extra></extra>')
    fig=style_chart(fig,280)
    fig.update_layout(legend=dict(orientation='v',x=1,y=.5,xanchor='left',yanchor='middle'),
                      margin=dict(l=8,r=8,t=12,b=8))
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    st.caption(f'Share of selected actual {metric} · Same dates, line and channel filters')


def line_scorecards(data):
    """Readable financial highlights, using the same six SQL-derived measures."""
    for column,line in zip(st.columns(2,gap='medium'),['Motor','Travel']):
        with column,st.container(border=True,key='panel-score-'+line.lower()):
            st.subheader(line)
            rows=data.loc[data.LEVEL.eq('LINE') & data.LINE_OF_BUSINESS.eq(line)]
            if rows.empty:
                st.info('Not present in the selected line/date/channel scope.')
                continue
            row=rows.iloc[0]
            variance=row.GWP_VARIANCE_PCT
            delta=None if pd.isna(variance) else f'{float(variance):+.1%} vs plan'
            with st.container(key='score-'+line.lower()+'-gwp'):
                st.metric('Actual gross written premium',compact_amount(row.GWP),delta=delta,
                          help='Exact actual GWP: '+('Unavailable' if pd.isna(row.GWP) else f'RM {row.GWP:,.2f}'))
            st.caption('Plan GWP · '+compact_amount(row.PLAN_GWP)+(' · Variance unavailable' if pd.isna(variance) else ''))
            st.divider()
            earned,claims,loss=st.columns(3,gap='small')
            earned.metric('Net earned premium',compact_amount(row.NEP),
                          help='Unavailable' if pd.isna(row.NEP) else f'RM {row.NEP:,.2f}')
            claims.metric('Net incurred claims',compact_amount(row.NET_INCURRED_CLAIMS),
                          help='Unavailable' if pd.isna(row.NET_INCURRED_CLAIMS) else f'RM {row.NET_INCURRED_CLAIMS:,.2f}')
            loss.metric('Net loss ratio','Unavailable' if pd.isna(row.LOSS_RATIO) else f'{float(row.LOSS_RATIO):.1%}',
                        help='Net incurred claims / net earned premium. No planned loss-ratio comparison.')


def channel_table(data):
    rows=channel_scorecard(data)
    if rows.empty:
        st.info('No channels in the selected scope.')
        return
    def variance_color(value):
        if pd.isna(value):
            return 'color: #667085'
        return 'color: #B21E3D' if value<0 else 'color: #23745A'
    money=['GWP','PLAN_GWP','GWP_VARIANCE','NEP','NET_INCURRED_CLAIMS']
    formats={field:compact_amount for field in money} | {'GWP_VARIANCE_PCT':'{:.1%}','LOSS_RATIO':'{:.1%}'}
    styled=rows.style.format(formats,na_rep='Unavailable').map(variance_color,subset=['GWP_VARIANCE','GWP_VARIANCE_PCT'])
    labels={'DISTRIBUTION_CHANNEL':'Channel','GWP':'GWP actual','PLAN_GWP':'GWP plan',
            'GWP_VARIANCE':'GWP variance','GWP_VARIANCE_PCT':'GWP var %','NEP':'NEP',
            'NET_INCURRED_CLAIMS':'Net incurred','LOSS_RATIO':'Net loss ratio'}
    st.dataframe(styled,hide_index=True,use_container_width=True,
        column_config={field:st.column_config.Column(label) for field,label in labels.items()})
    st.caption('Click a column header to sort. Display rounding only; exact grouped values remain in Source evidence. Unavailable variances are not zero.')
