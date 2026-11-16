"""Shared presentation helpers; no business rules or financial calculations."""
from html import escape
from pathlib import Path
import base64
from urllib.parse import quote

import pandas as pd
import streamlit as st

LOGO_PATH = Path(__file__).resolve().parent / 'assets' / 'tune-protect-group-logo.png'
RED = '#D81D46'
NAVY = '#182D4C'
TEAL = '#237D75'

ICONS = {
    'chart': '<path d="M4 20V10m5 10V4m5 16v-7m5 7V7M2 22h20"/>',
    'users': '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M17 4a3 3 0 0 1 0 6m1 4a5 5 0 0 1 3 4v3"/>',
    'target': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    'layers': '<path d="m3 7 9-5 9 5-9 5-9-5Zm0 5 9 5 9-5M3 17l9 5 9-5"/>',
    'shield': '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6l-9-4Z"/>',
    'document': '<path d="M6 2h8l5 5v15H6V2Zm8 0v6h5M9 12h7M9 16h7"/>',
    'percent': '<path d="m5 20 14-16"/><circle cx="7" cy="6" r="3"/><circle cx="17" cy="18" r="3"/>',
    'spark': '<path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7Z"/>',
}


def icon(name):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(name, ICONS["chart"])}</svg>'


def setup_page(title):
    st.set_page_config(page_title=title, page_icon=str(LOGO_PATH) if LOGO_PATH.is_file() else '✦', layout='wide')
    nav_icons = ''.join(f'''[data-testid="stSidebar"] label[data-baseweb="radio"]:nth-of-type({i})::before {{mask-image:url("data:image/svg+xml,{quote(icon(name))}");-webkit-mask-image:url("data:image/svg+xml,{quote(icon(name))}")}}''' for i,name in enumerate(['chart','users','target'],1))
    st.markdown('''<style>
    :root {--navy:#17263F;--red:#E20836;--muted:#55647C;--border:#E8EBF2}
    html,body,[data-testid="stApp"] {font-family:Inter,"Segoe UI",Arial,sans-serif;color:var(--navy)}
    [data-testid="stAppViewContainer"] {background:#FFFFFF}
    [data-testid="stHeader"] {background:transparent;height:2.25rem}
    [data-testid="stToolbar"],[data-testid="stDecoration"] {display:none}
    .block-container {max-width:1700px;padding:2.25rem 2.1rem 2rem}
    h1 {font-size:clamp(25px,2.1vw,34px)!important;letter-spacing:-.8px;font-weight:600!important;color:var(--navy);padding:.05rem 0 .35rem!important;line-height:1.2!important}
    h2 {font-size:1.2rem!important;letter-spacing:-.3px;font-weight:600!important;color:var(--navy)}
    h3 {font-size:1.02rem!important;font-weight:600!important;color:var(--navy);padding:.1rem 0 .35rem!important}
    [data-testid="stVerticalBlock"] {gap:.8rem}
    [data-testid="stSidebar"] {background:#fff;border-right:1px solid var(--border);min-width:246px!important;max-width:246px!important;width:246px!important}
    [data-testid="stSidebarHeader"] {position:absolute!important;top:8px!important;right:8px!important;padding:0!important;margin:0!important;z-index:2}
    [data-testid="stSidebarUserContent"] {padding:1.25rem .95rem 1rem!important}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.65rem}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {padding:10px 12px;border-radius:10px;margin:2px 0;min-height:43px;gap:10px;white-space:nowrap;font-size:14px}
    [data-testid="stSidebar"] label[data-baseweb="radio"]>div:first-child {position:absolute;width:1px;height:1px;opacity:0;overflow:hidden}
    [data-testid="stSidebar"] label[data-baseweb="radio"]::before {content:"";width:19px;height:19px;min-width:19px;background:var(--navy);mask-size:contain;-webkit-mask-size:contain;mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {background:#FFF0F4;color:#D90030}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked)::before {background:#E20836}
    [data-testid="stSidebar"] hr {margin:.65rem 0;border-color:#EEF0F5}
    [data-testid="stSidebar"] button {font-size:12px}
    .brand {padding:0 10px 8px}
    .brand img {display:block;width:70px;height:70px;margin-bottom:10px}
    .brand-name {font-size:16px;font-weight:550;margin-bottom:16px}
    .brand-area {font-size:10px;letter-spacing:1px;color:#56647A;margin-bottom:8px}
    .brand-app {font-size:16px;font-weight:600}
    [data-testid="stMetric"] {background:linear-gradient(125deg,#fff,#FEFAFC);border:1px solid var(--border);border-radius:14px;padding:16px 18px;box-shadow:0 3px 10px #15274504;min-height:110px}
    [data-testid="stMetricLabel"] {color:#43516A;font-size:.8rem}
    [data-testid="stMetricValue"] {font-size:clamp(23px,2vw,30px);font-weight:550;color:var(--navy)}
    [data-testid="stMetricValue"]>div {white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere}
    [data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p {color:#596880!important;font-size:12px;line-height:1.5}
    [data-testid="stDataFrame"] {border:1px solid var(--border);border-radius:9px;overflow:hidden}
    [data-testid="stExpander"] {background:transparent}
    [class*="st-key-panel-"] {background:#fff;border-radius:14px;border-color:#E8EBF2!important;box-shadow:0 3px 13px #182D4C04}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:focus-visible) {outline:2px solid #E20836;outline-offset:2px}
    [data-baseweb="select"]>div {background:#fff;border-color:#E0E5EF;border-radius:8px;min-height:36px;font-size:13px}
    [data-testid="stPopover"] button {min-height:36px;border-color:#E0E5EF;border-radius:8px;font-size:13px;box-shadow:0 2px 5px #182D4C04}
    .eyebrow {font-size:10px;color:#DF0030;letter-spacing:1.8px;font-weight:750;margin-bottom:9px}
    .subtitle {color:#53627A;font-size:14px;line-height:1.5;margin:0 0 7px}
    .kpi-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:4px 0 6px}
    .kpi-card {display:flex;gap:14px;border:1px solid var(--border);border-radius:15px;min-height:126px;padding:18px;background:linear-gradient(130deg,#fff,#FBFCFF);box-shadow:0 3px 12px #17263F04}
    .kpi-card.rose {background:linear-gradient(120deg,#FFFDFE,#FFF5F7)}
    .kpi-icon {height:39px;width:39px;min-width:39px;border-radius:50%;background:#FFF0F3;color:#E20836;display:flex;align-items:center;justify-content:center}
    .kpi-icon svg {height:23px;width:23px}
    .kpi-label {font-size:12px;color:#34435D;margin-bottom:9px}
    .kpi-value {font-size:clamp(23px,2vw,31px);font-weight:500;letter-spacing:-.6px;color:#17263F;line-height:1.2;overflow-wrap:anywhere}
    .kpi-detail {font-size:11px;color:#53627A;margin-top:9px;line-height:1.5}
    .negative {color:#E20836}.positive {color:#18734C}
    .insight-label {display:flex;align-items:center;gap:8px;font-size:18px;font-weight:600;margin-bottom:12px;color:#17263F}
    .insight-label svg {width:22px;height:22px;color:#E20836}
    .insight-pill {font-size:10px;background:#F2EEFA;border-radius:12px;padding:4px 8px;font-weight:400;margin-left:auto;white-space:nowrap}
    .insight-lead {background:#FFF0F4;border-radius:10px;padding:13px;font-size:13px;line-height:1.55;font-weight:550;color:#17263F;margin-bottom:14px}
    .profile-label {font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#5D6A80;margin-bottom:7px}
    .profile-id {font-size:20px;font-weight:600;letter-spacing:-.3px;color:#17263F}
    .profile-grid {display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}
    .profile-value {font-size:17px;font-weight:550;color:#17263F}.profile-caption {font-size:11px;color:#53627A;margin-top:3px}
    .risk-tag {display:inline-block;padding:4px 8px;background:#FFF0F4;color:#BA1740;border-radius:6px;font-size:12px}
    @media(max-width:1150px) {.kpi-card{padding:14px;gap:9px}.kpi-icon{display:none}.block-container{padding-left:1.25rem;padding-right:1.25rem}}
    @media(max-width:800px) {.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style>'''+f'<style>{nav_icons}</style>', unsafe_allow_html=True)


def sidebar_brand(title, area):
    logo = f'<img src="data:image/png;base64,{base64.b64encode(LOGO_PATH.read_bytes()).decode()}" alt="Tune Protect logo">' if LOGO_PATH.is_file() else ''
    st.markdown(f'<div class="brand">{logo}<div class="brand-name">Tune Protect Group</div><div class="brand-area">{escape(area)}</div><div class="brand-app">{escape(title)}</div></div>',unsafe_allow_html=True)
    st.divider()


def financial_cards(cards):
    html=[]
    for label,value,detail,symbol,tone,exact in cards:
        html.append(f'<div class="kpi-card {escape(tone)}" title="{escape(exact,quote=True)}"><div class="kpi-icon">{icon(symbol)}</div><div><div class="kpi-label">{escape(label)}</div><div class="kpi-value">{escape(value)}</div><div class="kpi-detail">{detail}</div></div></div>')
    st.markdown('<div class="kpi-grid">'+''.join(html)+'</div>',unsafe_allow_html=True)


def insight_heading(label='AI insights',pill='Cortex AI'):
    st.markdown(f'<div class="insight-label">{icon("spark")}{escape(label)}<span class="insight-pill">{escape(pill)}</span></div>',unsafe_allow_html=True)


def insight_lead(text):
    st.markdown(f'<div class="insight-lead">{escape(text)}</div>',unsafe_allow_html=True)


def customer_profile(customer_id,value,value_band,risk,score):
    tone = 'background:#EDF8F1;color:#18734C' if risk == 'Low' else ('background:#FFF6E5;color:#866012' if risk == 'Medium' else '')
    st.markdown(f'<div class="profile-label">Customer spotlight</div><div class="profile-id">{escape(customer_id)}</div><div class="profile-grid"><div><div class="profile-value">{escape(value)}</div><div class="profile-caption">{escape(value_band)} customer value</div></div><div><span class="risk-tag" style="{tone}">{escape(risk)} risk</span><div class="profile-caption">Source score {escape(str(score))}</div></div></div>',unsafe_allow_html=True)


def heading(title, subtitle, tag='TUNE PROTECT / INTELLIGENCE'):
    st.markdown(f'<div class="eyebrow">{escape(tag)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="subtitle">{escape(subtitle)}</div>', unsafe_allow_html=True)


def compact_amount(value):
    """Display rounding only. Full source amounts remain in details and tooltips."""
    if pd.isna(value):
        return 'Unavailable'
    value = float(value)
    for threshold, suffix in [(1e9, 'B'), (1e6, 'M'), (1e3, 'K')]:
        if abs(value) >= threshold:
            digits = 2 if suffix in ('M','B') else 1
            number = f'{value/threshold:,.{digits}f}'
            if suffix == 'K':
                number = number.rstrip('0').rstrip('.')
            return f'RM {number}{suffix}'
    return f'RM {value:,.0f}'


def style_chart(fig, height=260):
    fig.update_layout(height=height, margin=dict(l=4,r=12,t=24,b=8),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Segoe UI, Arial, sans-serif',size=11,color='#455570'),
        legend=dict(title=None,orientation='h',y=1.14,x=1,xanchor='right',font_size=11),
        hoverlabel=dict(bgcolor='white',font_color='#182D4C'))
    fig.update_xaxes(showgrid=False,zeroline=False)
    fig.update_yaxes(gridcolor='#EDF0F5',zerolinecolor='#D6DDE7')
    return fig


def connection_error(subject='Snowflake data'):
    st.error(f'{subject.capitalize()} is temporarily unavailable. Check your connection, warehouse and object permissions, then refresh. No sample figures have been substituted.')
    st.caption('Connection setup and required privileges are documented in README.md.')
