"""Shared presentation helpers; no business rules or financial calculations."""
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

LOGO_PATH = Path(__file__).resolve().parent / 'assets' / 'tune-protect-group-logo.png'
RED = '#D81D46'
NAVY = '#182D4C'
TEAL = '#237D75'


def setup_page(title):
    st.set_page_config(page_title=title, page_icon=str(LOGO_PATH) if LOGO_PATH.is_file() else '✦', layout='wide')
    st.markdown('''<style>
    .block-container {max-width:1540px;padding-top:4rem;padding-bottom:3rem}
    h1 {font-size:2.05rem!important;letter-spacing:-1px;font-weight:750!important;color:#182D4C}
    h2 {font-size:1.4rem!important;letter-spacing:-.4px;color:#182D4C}
    h3 {font-size:1.15rem!important;color:#182D4C}
    [data-testid="stSidebar"] {background:#fff;border-right:1px solid #E6EAF0}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {padding:10px 12px;border-radius:8px;margin:3px 0}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background:#FFF0F3;color:#B81539;border-left:3px solid #D81D46}
    [data-testid="stMetric"] {background:#fff;border:1px solid #E4E9F0;border-radius:12px;padding:17px 18px;box-shadow:0 3px 12px #182D4C05;min-height:124px}
    [data-testid="stMetricLabel"] {color:#617087;font-size:.8rem}
    [data-testid="stMetricValue"] {font-size:clamp(20px,2.1vw,30px);font-weight:720;color:#182D4C}
    [data-testid="stMetricValue"] > div {white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere}
    [data-testid="stVerticalBlockBorderWrapper"] > div {border-color:#E4E9F0!important;border-radius:12px!important;background:#fff}
    [data-testid="stDataFrame"] {border-radius:10px}
    [data-testid="stCaptionContainer"] {color:#68788F}
    .eyebrow {font-size:10px;color:#B81539;letter-spacing:1.8px;font-weight:750;margin-bottom:4px}
    .subtitle {color:#64748B;font-size:.95rem;margin-top:-8px;margin-bottom:20px}
    </style>''', unsafe_allow_html=True)


def sidebar_brand(title, area):
    left, right = st.columns([1, 2.4], vertical_alignment='center')
    if LOGO_PATH.is_file():
        left.image(str(LOGO_PATH), width=56)
    right.markdown('**Tune Protect Group**')
    st.caption(area)
    st.markdown('### ' + title)
    st.divider()


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


def style_chart(fig, height=310):
    fig.update_layout(height=height, margin=dict(l=8,r=12,t=18,b=8),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif',size=12,color='#617087'),
        legend=dict(title=None,orientation='h',y=1.15,x=0),
        hoverlabel=dict(bgcolor='white',font_color='#182D4C'))
    fig.update_xaxes(showgrid=False,zeroline=False)
    fig.update_yaxes(gridcolor='#EDF0F5',zerolinecolor='#D6DDE7')
    return fig


def connection_error(subject='Snowflake data'):
    st.error(f'{subject.capitalize()} is temporarily unavailable. Check your connection, warehouse and object permissions, then refresh. No sample figures have been substituted.')
    st.caption('Connection setup and required privileges are documented in README.md.')
