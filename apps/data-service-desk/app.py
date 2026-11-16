"""Tune Data Service Desk — independent Streamlit entrypoint."""
from pathlib import Path
import sys

APP_DIRECTORY = Path(__file__).resolve().parent
IMPORT_ROOT = APP_DIRECTORY if (APP_DIRECTORY / 'shared').is_dir() else APP_DIRECTORY.parent.parent
if (IMPORT_ROOT / 'shared').is_dir() and str(IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(IMPORT_ROOT))

import json
import logging
import uuid
from datetime import date
from html import escape
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from shared.desk_rules import (CATEGORIES, CATEGORY_LABELS, PRIORITIES, STATUSES, STATUS_LABELS,
    TRANSITIONS, BUSINESS_UNITS, DOMAINS, FORMATS, reference, safe_link, validate_request)
from shared.snowflake_service import get_service
from shared.ui import setup_page, sidebar_brand, heading, connection_error

setup_page('Tune Data Service Desk')
st.markdown('''<style>
.block-container{max-width:1450px;padding-top:1.5rem;padding-bottom:1.25rem}
h1{font-size:25px!important;font-weight:500!important}
h2,h3{font-weight:500!important}.eyebrow{font-weight:500;letter-spacing:1px}
[data-testid="stVerticalBlock"]{gap:.55rem}
strong{font-weight:500}
.desk-status{display:inline-block;padding:4px 10px;border-radius:6px;font-size:13px;font-weight:500;background:#EEF2F7;color:#182D4C}
.desk-status.waiting{background:#FFF0F4;color:#AF193D}
.desk-status.done{background:#ECF6F0;color:#246747}
[data-testid="stMetric"]{min-height:92px;background:#fff;padding:12px 16px}
[data-testid="stMetricValue"]{font-size:25px;font-weight:500}
[data-testid="stSidebar"] label[data-baseweb="radio"]>div:first-child{position:static;width:auto;height:auto;opacity:1;overflow:visible}
[data-testid="stSidebar"] label[data-baseweb="radio"]::before{display:none}
[data-testid="stSidebar"] label[data-baseweb="radio"]{white-space:normal;font-size:13px;padding:7px 8px}
[data-testid="stForm"]{border-color:#E8EBF2;border-radius:12px}
</style>''',unsafe_allow_html=True)

with st.sidebar:
    sidebar_brand('Data Service Desk', 'DATA OPERATIONS')
    workspace = st.radio('Workspace',['Business User Portal','Data Team Workspace'],label_visibility='collapsed')
    team = workspace=='Data Team Workspace'
    pages = ['Operations Dashboard','Request Queue'] if team else ['Overview','New Data Request','Find Existing Reports','My Requests']
    nav_key='team_page' if team else 'bu_page'
    page=st.radio('Navigate',pages,key=nav_key,label_visibility='collapsed')
    st.divider()
    identity=st.text_input('Demo Data Team identity' if team else 'Demo requester identity',
        key='team_identity' if team else 'demo_identity',
        value=st.session_state.get('saved_team_identity','demo.engineer') if team else st.session_state.get('saved_requester','motor.demo'),max_chars=100)
    st.session_state['saved_team_identity' if team else 'saved_requester']=identity
    scope=st.selectbox('Record view',['All records','Synthetic demo only','Exclude validation'],index=2)
    st.caption('Synthetic tickets are labelled [Demo]. Historical [Validation] tickets are retained.')
    st.caption('Demo role and identity switching only. This is not authentication or authorization. Access uses the connected Snowflake role.')

role='Data Team' if team else 'Business User'
requester=None if team else identity.strip()


def navigate(destination):
    st.session_state[nav_key]=destination
    st.session_state.pop('selected_ticket',None)
    st.session_state.pop('loaded_ticket',None)


def refresh():
    st.session_state.pop('loaded_ticket',None)
    st.rerun()


def value(t,key,fallback='Not set'):
    v=t.get(key)
    return fallback if v is None or pd.isna(v) or v=='' else v


def open_request(ticket_id):
    st.session_state.selected_ticket=ticket_id
    st.session_state.pop('loaded_ticket',None)


def activity_summary(entry):
    if entry.ENTRY_TYPE=='STATUS_UPDATE' and entry.MESSAGE.startswith('{'):
        updates=json.loads(entry.MESSAGE)
        if 'STATUS' in updates:
            return 'Status changed to '+STATUS_LABELS.get(updates['STATUS']['to'],updates['STATUS']['to'])
        return 'Updated '+', '.join(field.replace('_',' ').lower() for field in updates)
    return entry.MESSAGE


def save_change(t, rerun=True, **kwargs):
    try:
        get_service().change_ticket(t['TICKET_ID'],t['VERSION'],identity.strip(),role,**kwargs)
        st.session_state.flash='Ticket update saved to Snowflake.'
        st.session_state.pop('loaded_ticket',None)
        if rerun:
            st.rerun()
    except ValueError as exc:
        st.warning(str(exc))


def overview():
    m=get_service().desk_metrics(requester,scope)
    specs=([('New / unassigned','NEW_UNASSIGNED'),('In progress','IN_PROGRESS'),('Waiting for BU','WAITING_FOR_BU'),
            ('Overdue','OVERDUE'),('Resolved this month','RESOLVED_MONTH')] if team else
           [('My open requests','OPEN_REQUESTS'),('Awaiting my response','WAITING_FOR_BU'),
            ('In progress','IN_PROGRESS'),('Resolved / closed','RESOLVED_CLOSED')])
    for col,(label,key) in zip(st.columns(len(specs)),specs):
        col.metric(label,f'{int(m[key]):,}')
    st.caption('Counts use the selected record view and all matching requests. Target date determines overdue work.' if team else
               'Your requests across the selected record view. Waiting for BU means your response is needed.')
    if team:
        st.caption('Resolved this month uses recorded resolution events. Historical tickets with unknown resolution dates are excluded.')
        st.subheader('Workload distribution')
        dimension=st.selectbox('Group requests by',['Business unit','Priority','Assigned owner','Status'])
        dist=get_service().desk_distribution(dimension,scope)
        if dist.empty:
            st.info('No requests in this view.')
        else:
            if dimension=='Status':
                dist['LABEL']=dist.LABEL.map(STATUS_LABELS)
            if 2 <= len(dist) <= 10:
                # A short horizontal comparison is easier to scan than a count table.
                fig=go.Figure(go.Bar(x=dist.REQUESTS,y=dist.LABEL,orientation='h',
                    marker_color='#D81D46',text=dist.REQUESTS,textposition='outside',
                    hovertemplate='%{y}: %{x:,} requests<extra></extra>'))
                fig.update_layout(height=max(160,min(320,35*len(dist)+40)),
                    margin=dict(l=0,r=40,t=5,b=5),paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',font=dict(family='Segoe UI, Arial',size=12,color='#182D4C'),
                    xaxis=dict(title=None,visible=False,rangemode='tozero'),
                    yaxis=dict(title=None,autorange='reversed'),showlegend=False)
                st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
            else:
                st.dataframe(dist.rename(columns={'LABEL':dimension,'REQUESTS':'Requests'}),hide_index=True,use_container_width=True,
                             height=min(320,35*len(dist)+38))
        st.button('Open Request Queue',on_click=navigate,args=('Request Queue',),type='primary')
    else:
        for col,label in zip(st.columns(3),['New Data Request','Find Existing Reports','My Requests']):
            col.button(label,on_click=navigate,args=(label,),use_container_width=True,type='primary' if label=='New Data Request' else 'secondary')
        recent=get_service().desk_queue(requester=requester,sort='Recently updated',scope=scope)
        if recent.empty:
            st.info('No requests yet. Find an existing report or create your first data request.')
            return
        requests,updates=st.columns([1.7,1],gap='large')
        with requests:
            st.subheader('Recent Requests')
            st.caption('Awaiting your response first, followed by the latest updated requests. Showing up to six.')
            ordered=recent.assign(AWAITING=recent.STATUS.eq('WAITING_FOR_BU')).sort_values(
                ['AWAITING','UPDATED_AT'],ascending=[False,False]).head(6)
            for _,ticket in ordered.iterrows():
                link,summary=st.columns([1,3])
                link.button(reference(ticket.TICKET_NUMBER),key='recent_'+ticket.TICKET_ID,
                    on_click=open_request,args=(ticket.TICKET_ID,),use_container_width=True)
                with summary:
                    st.write(ticket.TITLE)
                    label=STATUS_LABELS[ticket.STATUS]
                    if ticket.STATUS=='WAITING_FOR_BU':
                        st.markdown('<span class="desk-status waiting">Response needed · Waiting for BU</span>',unsafe_allow_html=True)
                    else:
                        st.caption(label+' · '+str(value(ticket,'ASSIGNED_TO','Unassigned')))
                    st.caption('Updated '+str(ticket.UPDATED_AT))
        with updates:
            st.subheader('Latest updates')
            for _,ticket in recent.head(3).iterrows():
                history=get_service().activity(ticket.TICKET_ID,requester)
                st.caption(reference(ticket.TICKET_NUMBER)+' · '+ticket.TITLE)
                if history.empty:
                    st.write(str(value(ticket,'PROGRESS_NOTES',STATUS_LABELS[ticket.STATUS]))[:240])
                    st.caption(str(ticket.UPDATED_AT))
                else:
                    latest=history.iloc[-1]
                    message=activity_summary(latest)
                    st.write(message[:240]+('…' if len(message)>240 else ''))
                    st.caption(str(latest.AUTHOR)+' · '+str(latest.CREATED_AT))
                st.divider()


def new_request():
    st.session_state.setdefault('request_token',str(uuid.uuid4()))
    step=st.session_state.get('request_step',1)
    st.caption(f'Step {step} of 3 · Request information → Data requirements → Review & submit')
    # Each step uses its own form; the draft survives reruns and navigation.
    draft=st.session_state.setdefault('request_draft',{})
    if step==1:
        with st.form('request_information'):
            st.subheader('Request information')
            a,b=st.columns(2)
            bu=a.selectbox('Business unit',BUSINESS_UNITS,index=BUSINESS_UNITS.index(draft.get('bu','Motor')))
            category=b.selectbox('Request category',CATEGORIES,format_func=CATEGORY_LABELS.get,index=CATEGORIES.index(draft.get('category',CATEGORIES[0])))
            title=st.text_input('Request title',value=draft.get('title',''),max_chars=200)
            description=st.text_area('Description',value=draft.get('description',''),max_chars=4000,height=100)
            justification=st.text_area('Business justification',value=draft.get('justification',''),max_chars=2000,height=80)
            a,b=st.columns(2)
            required_by=a.date_input('Required-by date',value=draft.get('required_by'),min_value=date.today())
            priority=b.selectbox('Requested priority',PRIORITIES,index=PRIORITIES.index(draft.get('priority','MEDIUM')),format_func=str.title)
            impact=st.text_area('Business impact',value=draft.get('business_impact',''),max_chars=2000,height=80,
                help='Explain who is affected and what happens if delivery is delayed.')
            next_step=st.form_submit_button('Continue to data requirements',type='primary')
        if next_step:
            draft.update(bu=bu,category=category,title=title,description=description,justification=justification,
                         priority=priority,required_by=required_by,business_impact=impact)
            try:
                validate_request(bu,identity,title,description,category,priority,justification,
                                 {'required_by':required_by,'business_impact':impact})
                if not required_by or not impact.strip():
                    raise ValueError('Complete the required-by date and business impact.')
                st.session_state.request_step=2
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))
    elif step==2:
        category=draft['category']
        with st.form('data_requirements'):
            st.subheader('Data requirements')
            domain=st.selectbox('Data domain',DOMAINS,index=DOMAINS.index(draft.get('data_domain','Motor')))
            existing=st.text_input('Existing report / dataset reference',value=draft.get('existing_reference',''),max_chars=1000)
            reporting=fields=output=None
            if category in ('REPORT_REQUEST','DATA_EXTRACT','DATA_ISSUE','ENHANCEMENT','OTHER'):
                reporting=st.text_input('Reporting period',value=draft.get('reporting_period') or '',max_chars=200,placeholder='e.g. October 2026')
                fields=st.text_area('Required metrics or fields',value=draft.get('required_fields') or '',max_chars=2000,height=100)
            if category in ('REPORT_REQUEST','DATA_EXTRACT','ENHANCEMENT','OTHER'):
                output=st.selectbox('Preferred output format',FORMATS,index=FORMATS.index(draft.get('output_format') or 'Excel'))
            st.caption('Supporting documents are outside this iteration. Describe your requirements in the fields above.')
            a,b=st.columns(2)
            back=a.form_submit_button('Back to request information')
            review=b.form_submit_button('Review request',type='primary')
        if back or review:
            draft.update(data_domain=domain,existing_reference=existing,reporting_period=reporting,required_fields=fields,output_format=output)
            st.session_state.request_step=1 if back else 3
            st.rerun()
    else:
        st.subheader('Review & submit')
        st.write(draft['title'])
        st.caption(f"{draft['bu']} · {CATEGORY_LABELS[draft['category']]} · Requested priority: {draft['priority'].title()} · Required by: {draft['required_by']}")
        for label,key in [('Description','description'),('Business justification','justification'),('Business impact','business_impact')]:
            st.markdown(f'**{label}**'); st.write(draft[key])
        st.caption(' · '.join(str(draft[k]) for k in ('data_domain','existing_reference','reporting_period','required_fields','output_format') if draft.get(k)))
        st.caption('Priority and delivery date will be confirmed by the Data Team.')
        a,b=st.columns([1,3])
        if a.button('Edit request'):
            st.session_state.request_step=1; st.rerun()
        if b.button('Submit request',type='primary'):
            try:
                extras={k:draft.get(k) for k in ('required_by','business_impact','data_domain','existing_reference','reporting_period','required_fields','output_format')}
                tid=st.session_state.request_token
                get_service().create_ticket(tid,draft['bu'],identity,draft['title'],draft['description'],draft['category'],draft['priority'],draft['justification'],**extras)
                t=get_service().ticket(tid,identity)
                st.session_state.flash='Request submitted · '+reference(t['TICKET_NUMBER'])
                st.session_state.selected_ticket=tid
                st.session_state.request_token=str(uuid.uuid4())
                st.session_state.request_step=1
                st.session_state.request_draft={}
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))


def catalogue():
    a,b=st.columns([3,1])
    keyword=a.text_input('Search reports',placeholder='Report name or keyword')
    domain=b.selectbox('Business domain',['All']+DOMAINS)
    reports=get_service().catalogue(keyword,domain)
    st.caption('Catalogue entries are separate from requests. [Demo] entries are illustrative and do not represent available reports.')
    if reports.empty:
        st.info('No catalogue entries match. You can submit a new request.')
    for _,r in reports.iterrows():
        with st.container(border=True):
            st.subheader(r.REPORT_NAME)
            st.write(r.DESCRIPTION)
            st.caption(f'{r.BUSINESS_DOMAIN} · Owner: {r.DATA_OWNER} · Refresh: {r.REFRESH_FREQUENCY}')
            if safe_link(r.ACCESS_LINK):
                st.link_button('Open report',r.ACCESS_LINK)
            else:
                st.caption('Illustrative entry · No report link configured.' if r.IS_DEMO else 'No report link configured.')
    st.button('New Data Request',on_click=navigate,args=('New Data Request',),type='primary')


def queue():
    a,b,c,d=st.columns([1.1,1,1.2,.8])
    status=a.selectbox('Status',['All']+STATUSES,format_func=lambda x:STATUS_LABELS.get(x,x))
    priority=b.selectbox('Priority',['All']+PRIORITIES,format_func=str.title)
    sort=c.selectbox('Sort by',['Newest','Oldest / age','Priority','Recently updated'])
    d.caption('Live queue')
    d.button('Refresh requests',use_container_width=True)
    bu=owner='All'
    with st.expander('More filters · category, business unit and owner' if team else 'More filters · category'):
        a,b,c=st.columns(3) if team else (st.container(),None,None)
        category=a.selectbox('Category',['All']+CATEGORIES,format_func=lambda x:CATEGORY_LABELS.get(x,x))
        if team:
            bu=b.selectbox('Business unit',['All']+BUSINESS_UNITS)
            owners=get_service().desk_owners()
            owner=c.selectbox('Owner',['All','Unassigned']+([] if owners.empty else owners.ASSIGNED_TO.tolist()))
    tickets=get_service().desk_queue(requester,status,bu,category,priority,owner,sort,scope)
    if tickets.empty:
        st.info('No requests match this view. Broaden the filters or submit a request.'); return
    st.caption(f"Showing {len(tickets)} of {int(tickets.iloc[0].MATCHING_TOTAL)} matching requests (maximum 200). Select a row to open its workspace.")
    columns=(['TICKET_NUMBER','TITLE','STATUS','ASSIGNED_TO','CONFIRMED_PRIORITY','AGE_DAYS','TARGET_DATE','BUSINESS_UNIT','CATEGORY','PRIORITY'] if team else
             ['TICKET_NUMBER','TITLE','STATUS','ASSIGNED_TO','PRIORITY','UPDATED_AT','TARGET_DATE','CREATED_AT','CATEGORY'])
    view=tickets[columns].copy()
    view.TICKET_NUMBER=view.TICKET_NUMBER.map(reference)
    view.STATUS=view.STATUS.map(STATUS_LABELS)
    view.CATEGORY=view.CATEGORY.map(lambda x:CATEGORY_LABELS.get(x,x))
    view.ASSIGNED_TO=view.ASSIGNED_TO.fillna('Unassigned').replace('','Unassigned')
    if team:
        view.CONFIRMED_PRIORITY=view.CONFIRMED_PRIORITY.fillna('Not confirmed').replace('','Not confirmed')
    labels={'TICKET_NUMBER':'Reference','TITLE':'Title','BUSINESS_UNIT':'Business unit','CATEGORY':'Category','PRIORITY':'Requested priority',
            'CONFIRMED_PRIORITY':'Confirmed priority','ASSIGNED_TO':'Owner','STATUS':'Status','AGE_DAYS':'Age (days)',
            'CREATED_AT':'Submitted','TARGET_DATE':'Target date','UPDATED_AT':'Last updated'}
    def highlight_waiting(row):
        return ['background-color: #FFF0F4; color: #8F1835' if row['Status']=='Waiting for BU' else '' for _ in row]
    display=view.rename(columns=labels)
    event=st.dataframe(display.style.apply(highlight_waiting,axis=1),hide_index=True,use_container_width=True,
                       height=min(420,35*len(view)+38),
                       column_config={'Reference':st.column_config.TextColumn(width='small'),
                                      'Title':st.column_config.TextColumn(width='medium'),
                                      'Status':st.column_config.TextColumn(width='small'),
                                      'Owner':st.column_config.TextColumn(width='small'),
                                      'Age (days)':st.column_config.NumberColumn(width='small',format='%d')},
                       on_select='rerun',selection_mode='single-row',
                       key='queue_'+str((team,scope,status,bu,category,priority,owner,sort,st.session_state.get('queue_revision',0))))
    if event.selection.rows:
        open_request(tickets.iloc[event.selection.rows[0]].TICKET_ID)
        st.rerun()


def detail(tid):
    snapshot=st.session_state.get('loaded_ticket')
    if not snapshot or snapshot['TICKET_ID']!=tid:
        snapshot=get_service().ticket(tid,requester)
        st.session_state.loaded_ticket=snapshot
    t=snapshot
    def back_to_queue():
        navigate('Request Queue' if team else 'My Requests')
        st.session_state.queue_revision=st.session_state.get('queue_revision',0)+1
    back,refresh_button=st.columns([4,1])
    back.button('← Back to '+('queue' if team else 'my requests'),on_click=back_to_queue)
    refresh_button.button('Refresh request',on_click=lambda:st.session_state.pop('loaded_ticket',None),use_container_width=True)
    st.subheader(reference(t['TICKET_NUMBER'])+' · '+t['TITLE'])
    if t.get('IS_DEMO'):
        st.caption('SYNTHETIC DEMONSTRATION DATA · No real request or delivered report is implied.')
    widget_prefix=tid+'_'+str(t['VERSION'])+'_'
    status=STATUS_LABELS[t['STATUS']]
    tone='waiting' if t['STATUS']=='WAITING_FOR_BU' else 'done' if t['STATUS'] in ('RESOLVED','CLOSED') else ''
    st.markdown(f'<span class="desk-status {tone}">{escape(status)}</span>',unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    for col,label,key in [(a,'Assigned owner','ASSIGNED_TO'),(b,'Confirmed priority','CONFIRMED_PRIORITY'),
                          (c,'Target completion','TARGET_DATE'),(d,'Requested priority','PRIORITY')]:
        col.caption(label); col.write(str(value(t,key)))
    st.caption(f"{t['BUSINESS_UNIT']} · {CATEGORY_LABELS.get(t['CATEGORY'],t['CATEGORY'])} · Requested by {t['REQUESTER']} · Required by {value(t,'REQUIRED_BY')} · Effort {value(t,'EFFORT_ESTIMATE')}")
    section=st.radio('Ticket section',['Conversation & history']+(['Manage request'] if team else [])+['Request details','Resolution'],
                     horizontal=True,key='section_'+str(team)+'_'+tid)
    if section=='Request details':
        st.markdown('**Description**'); st.write(t['DESCRIPTION'])
        justification,impact=st.columns(2)
        for col,label,key in [(justification,'Business justification','BUSINESS_JUSTIFICATION'),(impact,'Business impact','BUSINESS_IMPACT')]:
            col.markdown(f'**{label}**'); col.write(value(t,key,'Not recorded'))
        with st.expander('Data requirements & timestamps'):
            for label,key in [('Domain','DATA_DOMAIN'),('Existing reference','EXISTING_REFERENCE'),('Reporting period','REPORTING_PERIOD'),
                ('Required metrics / fields','REQUIRED_FIELDS'),('Output format','OUTPUT_FORMAT')]:
                st.caption(label); st.write(str(value(t,key)))
            st.caption(f"Submitted {t['CREATED_AT']} · Updated {t['UPDATED_AT']} · Version {t['VERSION']} · Snowflake timestamps")
        st.markdown('**Latest progress**'); st.write(value(t,'PROGRESS_NOTES','Awaiting a progress update.'))
    if section=='Conversation & history':
        history=get_service().activity(tid,requester)
        thread,composer=st.columns([1.4,1],gap='large')
        with thread:
            st.subheader('Conversation & history')
            with st.container(height=320,border=False):
                if history.empty:
                    st.caption('No activity entries recorded. Older progress and resolution notes are preserved in the request.')
                internal_tab=st.checkbox('Show internal notes only',value=False) if team else False
                for _,entry in history.iterrows():
                    if team and bool(entry.IS_INTERNAL)!=internal_tab:
                        continue
                    st.caption(f"{reference(entry.TICKET_NUMBER)} · {entry.AUTHOR} · {entry.AUTHOR_ROLE} · {entry.CREATED_AT} · {entry.ENTRY_TYPE.replace('_',' ').title()}"+(' · INTERNAL' if entry.IS_INTERNAL else ''))
                    if entry.ENTRY_TYPE=='STATUS_UPDATE' and entry.MESSAGE.startswith('{'):
                        updates=json.loads(entry.MESSAGE)
                        for field,change in updates.items():
                            before=change['from'] or 'Not set'; after=change['to'] or 'Not set'
                            if field=='STATUS':
                                before=STATUS_LABELS.get(before,before); after=STATUS_LABELS.get(after,after)
                            st.write(f"{field.replace('_',' ').title()}: {before} → {after}")
                    else:
                        st.write(entry.MESSAGE)
                    st.divider()
        with composer:
            st.subheader('Add an update')
            with st.form('conversation_'+tid+'_'+str(t['VERSION'])):
                choices=['Comment']
                if team and t['STATUS']=='IN_PROGRESS': choices.append('Request clarification')
                if not team and t['STATUS']=='WAITING_FOR_BU': choices.append('Respond to clarification')
                action=st.selectbox('Entry type',key=widget_prefix+'entry',options=choices)
                message=st.text_area('Message',key=widget_prefix+'message',max_chars=4000,height=100)
                internal=st.checkbox('Internal note — hidden from BU',key=widget_prefix+'internal') if team else False
                resume=st.checkbox('Return to In Progress with this response',key=widget_prefix+'resume',value=True) if not team and t['STATUS']=='WAITING_FOR_BU' else False
                submit=st.form_submit_button('Send update',type='primary')
            if submit:
                kind={'Comment':'COMMENT','Request clarification':'CLARIFICATION_REQUEST','Respond to clarification':'CLARIFICATION_RESPONSE'}[action]
                save_change(t,entry_type=kind,message=message,internal=internal,resume=resume)
    if section=='Resolution':
        st.write(value(t,'RESOLUTION_NOTES','No resolution recorded yet.'))
        delivered=value(t,'DELIVERED_REFERENCE','')
        if delivered:
            st.caption('Delivered artifact reference'); st.write(delivered)
            if safe_link(delivered): st.link_button('Open delivered output',delivered)
        if not team and t['STATUS']=='RESOLVED':
            st.button('Confirm closure',type='primary',key=widget_prefix+'close',
                on_click=save_change,args=(t,),kwargs={'rerun':False,'changes':{'STATUS':'CLOSED'},
                'entry_type':'STATUS_UPDATE','message':'Requester confirmed closure.'})
            def reopen_request():
                save_change(t,rerun=False,changes={'STATUS':'IN_PROGRESS'},entry_type='STATUS_UPDATE',
                            message=st.session_state[widget_prefix+'reason'])
            with st.form('reopen_'+widget_prefix):
                st.text_input('Reason to reopen',max_chars=2000,key=widget_prefix+'reason')
                st.form_submit_button('Reopen request',on_click=reopen_request)
    if team:
        if section=='Manage request':
            st.caption('Assign and confirm priority to triage. Use Conversation & history for clarification; record resolution below before resolving.')
            if t['STATUS']=='CLOSED':
                st.info('This request is closed. Additional comments can be added in the conversation.'); return
            with st.form('manage_'+tid+'_'+str(t['VERSION'])):
                a,b=st.columns(2)
                owner=a.text_input('Assigned owner',key=widget_prefix+'owner',value=value(t,'ASSIGNED_TO',''),max_chars=100)
                confirmed=b.selectbox('Confirmed priority',key=widget_prefix+'priority',options=['Not confirmed']+PRIORITIES,index=(PRIORITIES.index(t['CONFIRMED_PRIORITY'])+1) if t.get('CONFIRMED_PRIORITY') in PRIORITIES else 0,format_func=str.title)
                a,b,c=st.columns(3)
                target=a.date_input('Target completion date',key=widget_prefix+'target',value=t.get('TARGET_DATE'))
                effort=b.selectbox('Effort estimate',key=widget_prefix+'effort',options=['Not estimated','S','M','L'],index=['Not estimated','S','M','L'].index(value(t,'EFFORT_ESTIMATE','Not estimated')))
                allowed=[s for s in TRANSITIONS[t['STATUS']] if s!='WAITING_FOR_BU' or t['STATUS']=='WAITING_FOR_BU']
                status=c.selectbox('Update status',key=widget_prefix+'status',options=allowed,format_func=STATUS_LABELS.get)
                progress_col,resolution_col=st.columns(2)
                progress=progress_col.text_area('Work progress',key=widget_prefix+'progress',value=value(t,'PROGRESS_NOTES',''),max_chars=4000,height=100)
                notes=resolution_col.text_area('Resolution notes',key=widget_prefix+'resolution',value=value(t,'RESOLUTION_NOTES',''),max_chars=4000,height=100)
                delivered=st.text_input('Delivered output link or reference',key=widget_prefix+'delivery',value=value(t,'DELIVERED_REFERENCE',''),max_chars=2000)
                submit=st.form_submit_button('Save ticket update',type='primary')
            if submit:
                save_change(t,changes={'ASSIGNED_TO':owner,'CONFIRMED_PRIORITY':None if confirmed=='Not confirmed' else confirmed,
                    'TARGET_DATE':target,'EFFORT_ESTIMATE':None if effort=='Not estimated' else effort,'STATUS':status,
                    'PROGRESS_NOTES':progress,'RESOLUTION_NOTES':notes,'DELIVERED_REFERENCE':delivered},entry_type='STATUS_UPDATE')


def desk_page():
    # Check connectivity before rendering counters; never substitute sample metrics.
    get_service().desk_metrics(requester,scope)
    heading(workspace,'Structured requests. Clear ownership. Visible progress.','TUNE PROTECT / DATA OPERATIONS')
    if st.session_state.get('flash'):
        st.success(st.session_state.pop('flash'))
    if not identity.strip():
        st.info('Enter a demo identity to continue.'); return
    context=(workspace,identity,page,scope)
    if st.session_state.get('desk_context')!=context:
        st.session_state.pop('selected_ticket',None)
        st.session_state.pop('loaded_ticket',None)
        st.session_state.desk_context=context
    if st.session_state.get('selected_ticket'):
        detail(st.session_state.selected_ticket); return
    st.subheader(page)
    if page in ('Overview','Operations Dashboard'): overview()
    elif page=='New Data Request': new_request()
    elif page=='Find Existing Reports': catalogue()
    else: queue()

try:
    desk_page()
except ValueError as exc:
    st.warning(str(exc))
except Exception:
    logging.getLogger(__name__).exception('Service Desk operation failed')
    connection_error('request data')
    st.caption('The enhanced desk requires sql/desk_upgrade.sql. Migrations and demo seeding never run on app startup.')
