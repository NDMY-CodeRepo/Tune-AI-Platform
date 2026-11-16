"""Service Desk HTTP adapter over the existing Snowflake workflow, local demo only."""
import datetime as dt
import json
from typing import Literal
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from shared.desk_rules import (BUSINESS_UNITS as LEGACY_BUSINESS_UNITS,CATEGORIES,CATEGORY_LABELS,DOMAINS,FORMATS,
                               PRIORITIES,STATUSES,STATUS_LABELS,TRANSITIONS,reference)
from shared.snowflake_service import get_service

router=APIRouter(prefix='/api/desk',tags=['Data Service Desk'])
Role=Literal['Business User','Data Team']
RecordScope=Literal['All records','Synthetic demo only','Exclude validation']
# Demo shortlist based on published Tune Protect functions, not an approved directory.
REQUESTING_FUNCTIONS = ['Finance', 'Claims', 'Underwriting', 'Actuarial', 'Sales & Distribution',
                       'Partnerships', 'Customer Experience', 'Technology', 'People & Culture',
                       'Risk & Compliance', 'Corporate Strategy', 'Other']
# Preserve filters for historical requests that used product lines as their BU.
BUSINESS_UNIT_FILTERS = list(dict.fromkeys(REQUESTING_FUNCTIONS + LEGACY_BUSINESS_UNITS))


def records(frame):
    result=json.loads(frame.to_json(orient='records',date_format='iso'))
    for row in result:
        if row.get('TICKET_NUMBER') is not None:
            row['REFERENCE']=reference(row['TICKET_NUMBER'])
    return result


def identity(actor):
    actor=actor.strip()
    if not actor:
        raise HTTPException(422,'Enter a demo identity.')
    return actor


def requester(actor,role):
    actor=identity(actor)
    return actor if role=='Business User' else None


def ticket_payload(ticket_id,actor,role):
    s=get_service()
    try:
        t=s.ticket(ticket_id,requester(actor,role))
    except ValueError as exc:
        raise HTTPException(404,str(exc)) from None
    return {'ticket':records(pd.DataFrame([t]))[0],
            'activity':records(s.activity(ticket_id,requester(actor,role)))}


@router.get('/meta')
def meta():
    return dict(business_units=REQUESTING_FUNCTIONS,business_unit_filters=BUSINESS_UNIT_FILTERS,categories=CATEGORIES,category_labels=CATEGORY_LABELS,
                domains=DOMAINS,formats=FORMATS,priorities=PRIORITIES,statuses=STATUSES,
                status_labels=STATUS_LABELS,transitions=TRANSITIONS,
                notice='Demo role and identity switching only. This is not authentication or authorization.')


@router.get('/overview')
def overview(actor:str=Query(min_length=1,max_length=100),role:Role='Business User',
             scope:RecordScope='Exclude validation',
             dimension:Literal['Business unit','Priority','Assigned owner','Status']='Business unit'):
    s=get_service();who=requester(actor,role)
    rows=s.desk_queue(requester=who,sort='Recently updated',scope=scope)
    updates=[]
    for _,t in rows.head(3).iterrows():
        history=s.activity(t.TICKET_ID,who)
        if not history.empty:
            latest=records(history.tail(1))[0]
            latest['TITLE']=t.TITLE
            updates.append(latest)
    return dict(metrics={k:int(v) for k,v in s.desk_metrics(who,scope).items()},rows=records(rows),updates=updates,
                distribution=records(s.desk_distribution(dimension,scope)) if role=='Data Team' else [])


@router.get('/tickets')
def tickets(actor:str=Query(min_length=1,max_length=100),role:Role='Business User',
            scope:RecordScope='Exclude validation',status:str=Query('All',max_length=30),
            bu:str=Query('All',max_length=100),category:str=Query('All',max_length=30),
            priority:str=Query('All',max_length=10),owner:str=Query('All',max_length=100),
            sort:Literal['Newest','Oldest / age','Priority','Recently updated']='Newest'):
    s=get_service()
    owners=s.desk_owners() if role=='Data Team' else pd.DataFrame()
    return {'rows':records(s.desk_queue(requester(actor,role),status,bu,category,priority,owner,sort,scope)),
            'owners':owners.ASSIGNED_TO.tolist() if not owners.empty else []}


@router.get('/tickets/{ticket_id}')
def detail(ticket_id:str,actor:str=Query(min_length=1,max_length=100),role:Role='Business User'):
    return ticket_payload(ticket_id,identity(actor),role)


class StrictModel(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)


class NewTicket(StrictModel):
    ticket_id:UUID
    actor:str=Field(min_length=1,max_length=100)
    business_unit:str=Field(min_length=1,max_length=100)
    title:str=Field(min_length=1,max_length=200)
    description:str=Field(min_length=1,max_length=4000)
    justification:str=Field(min_length=1,max_length=2000)
    category:str=Field(min_length=1,max_length=30)
    priority:str=Field(min_length=1,max_length=10)
    required_by:dt.date
    business_impact:str=Field(min_length=1,max_length=2000)
    data_domain:str=Field(min_length=1,max_length=100)
    existing_reference:str=Field(default='',max_length=1000)
    reporting_period:str|None=Field(default=None,max_length=200)
    required_fields:str|None=Field(default=None,max_length=2000)
    output_format:str|None=Field(default=None,max_length=30)


@router.post('/tickets')
def create(body:NewTicket):
    data=body.model_dump(mode='json')
    actor=identity(data.pop('actor'));tid=data.pop('ticket_id')
    args=[data.pop(k) for k in ('business_unit','title','description','category','priority','justification')]
    try:
        get_service().create_ticket(tid,args[0],actor,*args[1:],**data)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from None
    return ticket_payload(tid,actor,'Business User')


class Changes(StrictModel):
    ASSIGNED_TO:str|None=Field(default=None,max_length=100)
    CONFIRMED_PRIORITY:Literal['LOW','MEDIUM','HIGH']|None=None
    TARGET_DATE:dt.date|None=None
    EFFORT_ESTIMATE:Literal['S','M','L']|None=None
    STATUS:Literal['NEW','TRIAGED','IN_PROGRESS','WAITING_FOR_BU','RESOLVED','CLOSED']|None=None
    PROGRESS_NOTES:str|None=Field(default=None,max_length=4000)
    RESOLUTION_NOTES:str|None=Field(default=None,max_length=4000)
    DELIVERED_REFERENCE:str|None=Field(default=None,max_length=2000)


class Update(StrictModel):
    actor:str=Field(min_length=1,max_length=100)
    role:Role
    version:int=Field(ge=1)
    changes:Changes|None=None
    entry_type:Literal['COMMENT','CLARIFICATION_REQUEST','CLARIFICATION_RESPONSE','STATUS_UPDATE']='COMMENT'
    message:str=Field(default='',max_length=4000)
    internal:bool=False
    resume:bool=False


@router.post('/tickets/{ticket_id}/updates')
def update(ticket_id:str,body:Update):
    changes=body.changes.model_dump(mode='json',exclude_unset=True) if body.changes else {}
    if 'STATUS' in changes and changes['STATUS'] is None:
        raise HTTPException(422,'Choose a status.')
    if not changes and not body.message:
        raise HTTPException(422,'Enter a message or change a ticket field.')
    try:
        get_service().change_ticket(ticket_id,body.version,identity(body.actor),body.role,changes=changes,
            entry_type=body.entry_type,message=body.message,internal=body.internal,resume=body.resume)
    except ValueError as exc:
        raise HTTPException(409 if 'another session' in str(exc) else 422,str(exc)) from None
    return ticket_payload(ticket_id,body.actor,body.role)


@router.get('/catalogue')
def catalogue(keyword:str=Query('',max_length=200),domain:Literal['All','Motor','Travel','Claims','Finance','Customer','Other']='All'):
    return {'rows':records(get_service().catalogue(keyword,domain))}
