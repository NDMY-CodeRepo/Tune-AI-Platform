"""Tune Data Service Desk — independent Streamlit entrypoint."""
from pathlib import Path
import sys

APP_DIRECTORY = Path(__file__).resolve().parent
IMPORT_ROOT = APP_DIRECTORY if (APP_DIRECTORY / 'shared').is_dir() else APP_DIRECTORY.parent.parent
if (IMPORT_ROOT / 'shared').is_dir() and str(IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(IMPORT_ROOT))

import uuid
import streamlit as st
from shared.business_logic import CATEGORIES, PRIORITIES, STATUSES, TRANSITIONS
from shared.snowflake_service import get_service
from shared.ui import setup_page, sidebar_brand, heading, connection_error

setup_page('Tune Data Service Desk')
with st.sidebar:
    sidebar_brand('Tune Data Service Desk', 'DATA OPERATIONS')
    workspace = st.radio('Workspace', ['Business User Portal', 'Data Team Workspace'], label_visibility='collapsed')
    st.divider()
    st.caption('Demo workspace switching only. This is not authentication or authorization.')
    st.caption('Snowflake persistence · Existing request workflow')

def desk_page():
    role='Business User' if workspace=='Business User Portal' else 'Data Team'
    heading(workspace,'Request the data you need. Track every step to resolution.' if role=='Business User' else 'A clear view of pending work, ownership and delivery.', 'TUNE DATA SERVICE DESK / DATA OPERATIONS')
    st.caption('Demonstration workspace switching only — not authentication or authorization. All access uses the connected Snowflake role.')
    st.session_state.setdefault('request_token','TP-'+str(uuid.uuid4()).upper())
    if 'last_ticket' in st.session_state:
        st.success('Request submitted · '+st.session_state.last_ticket)
    requester=None
    if role == 'Business User':
        st.session_state.setdefault('demo_identity','motor.demo')
        requester = st.text_input('Demo requester identity',value=st.session_state.demo_identity,max_chars=100)
        st.session_state.demo_identity = requester
    overview=get_service().ticket_overview(requester)
    def count(statuses):
        return 0 if overview.empty else int(overview.loc[overview.STATUS.isin(statuses),'REQUESTS'].sum())
    open_count=count(['NEW','IN_PROGRESS'])
    resolved_count=count(['RESOLVED','CLOSED'])
    high_open=0 if overview.empty else int(overview.loc[overview.STATUS.isin(['NEW','IN_PROGRESS']) & overview.PRIORITY.eq('HIGH'),'REQUESTS'].sum())
    if role=='Business User':
        labels=['My requests','Awaiting action','In progress','Resolved / closed']
        values=[count(STATUSES),count(['NEW']),count(['IN_PROGRESS']),resolved_count]
    else:
        labels=['Open requests','In progress','Resolved / closed','High-priority open']
        values=[open_count,count(['IN_PROGRESS']),resolved_count,high_open]
    for col,label,value in zip(st.columns(4),labels,values):
        col.metric(label,f'{value:,}')
    if role=='Data Team':
        pending=overview.loc[overview.STATUS.isin(['NEW','IN_PROGRESS'])] if not overview.empty else overview
        priorities=' · '.join(f"{p.title()}: {0 if pending.empty else int(pending.loc[pending.PRIORITY.eq(p),'REQUESTS'].sum()):,}" for p in ['HIGH','MEDIUM','LOW'])
        st.caption('Pending work by priority · '+priorities+' · Counts include all requests; queue filters apply below.')
    if role == 'Business User':
        st.session_state.setdefault('show_request_form',False)
        if st.button('New Data Request',type='primary',use_container_width=False):
            st.session_state.show_request_form=True
        with st.expander('New request details',expanded=st.session_state.show_request_form):
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
                    st.session_state.show_request_form=False
                    st.session_state.request_token = 'TP-'+str(uuid.uuid4()).upper()
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))
        st.subheader('My Requests')
    else:
        requester = None
        st.subheader('Work queue')
    a,b,c,d = st.columns([1,1,1,1])
    status = a.selectbox('Status',['All']+STATUSES)
    category_filter = b.selectbox('Category',['All']+CATEGORIES)
    priority_filter = c.selectbox('Priority filter',['All']+PRIORITIES)
    d.button('Refresh requests')  # Ticket reads are deliberately uncached.
    tickets = get_service().tickets(status,category_filter,priority_filter,requester)
    if tickets.empty:
        st.info('No requests match this view. Submit a request or broaden the filters.'); return
    st.caption(f'Showing {len(tickets)} most recent matching requests (maximum 200).')
    queue=tickets[['TICKET_ID','BUSINESS_UNIT','TITLE','CATEGORY','PRIORITY','ASSIGNED_TO','STATUS','UPDATED_AT']].copy()
    queue['ASSIGNED_TO']=queue['ASSIGNED_TO'].fillna('Unassigned').replace('','Unassigned')
    queue['STATUS']=queue['STATUS'].map(lambda x:x.replace('_',' ').title())
    st.dataframe(queue,hide_index=True,use_container_width=True,height=300,
        column_config={c:st.column_config.Column(c.replace('_',' ').title()) for c in queue.columns})
    ticket_id = st.selectbox('Open request',tickets.TICKET_ID.tolist(),format_func=lambda x: x+' · '+tickets.loc[tickets.TICKET_ID.eq(x),'TITLE'].iloc[0])
    t = tickets.loc[tickets.TICKET_ID.eq(ticket_id)].iloc[0]
    with st.container(border=True):
        st.caption('REQUEST DETAIL')
        st.subheader(t.TITLE)
        st.caption(f'{t.TICKET_ID} · Requested by {t.REQUESTER} · {t.BUSINESS_UNIT}')
        stage=STATUSES.index(t.STATUS)
        st.progress((stage+1)/len(STATUSES),text=' → '.join(('● ' if i==stage else '')+status.replace('_',' ').title() for i,status in enumerate(STATUSES)))
        status_text=t.STATUS.replace('_',' ').title()
        if t.STATUS in ('RESOLVED','CLOSED'):
            st.success(status_text+' · Resolution available below',icon='✅')
        else:
            st.info(status_text+' · '+('Awaiting assignment' if not t.ASSIGNED_TO else 'Owner: '+t.ASSIGNED_TO))
        details,resolution=st.columns(2,gap='large')
        with details:
            st.markdown('**Request**'); st.write(t.DESCRIPTION)
            st.markdown('**Business justification**'); st.write(t.BUSINESS_JUSTIFICATION)
        with resolution:
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
    desk_page()
except Exception:
    connection_error('request data')
