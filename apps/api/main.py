"""Local, same-origin React adapter. No database/schema migration or SQL input."""
import datetime as dt
import json
import logging
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from shared.business_logic import customer_evidence, validate_ai_selection
from shared.executive_ui import compact_evidence
from shared.insight_facts import financial_narrative
from shared.snowflake_service import get_service, read

ROOT=Path(__file__).resolve().parents[2]
DIST=ROOT/'apps/ai-intelligence-react/dist'
app=FastAPI(title='Tune AI Intelligence — local API',docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])


@app.middleware('http')
async def local_origin(request:Request,call_next):
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        if origin and origin!=str(request.base_url).rstrip('/'):
            return JSONResponse({'detail':'Cross-origin requests are not allowed.'},status_code=403)
    response=await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    return response


@app.exception_handler(Exception)
async def unavailable(request,exc):
    logging.getLogger('tune.api').error('Request failed: %s',type(exc).__name__)
    return JSONResponse({'detail':'Snowflake is unavailable or source validation failed. Please retry. No sample data is substituted.'},status_code=503)


def records(frame):
    # JSON nulls for all missing values; dates ISO and Decimals numeric.
    return json.loads(frame.to_json(orient='records',date_format='iso'))


class Scope(BaseModel):
    model_config=ConfigDict(extra='forbid')
    start:dt.date
    end:dt.date
    line:Literal['All','Motor','Travel']='All'
    channel:str=Field(default='All',max_length=100)


def finances(scope):
    if scope.start>scope.end:
        raise HTTPException(422,'End month must be on or after start month.')
    data=read('finance',str(scope.start),str(scope.end),scope.line,scope.channel,True)
    return data


def executive_brief(data):
    total=data.loc[data.LEVEL.eq('TOTAL')].iloc[0]
    finding,facts=financial_narrative(data,total)
    return {'finding':finding,'facts':facts,'short_facts':compact_evidence(data,total),
            'ids':list(range(3,len(facts)))[:3] or [0],
            'action':'Review business-line and channel variances with the business owner.',
            'source':'Calculated results · AI optional'}


@app.get('/api/health')
def health():
    return {'status':'ok','mode':'Local demo','data':'Snowflake synthetic demo records'}


@app.get('/api/finance/options')
def options():
    data=read('financial_options')
    if data.empty:
        return {'months':[],'channels':[]}
    return {'months':sorted(str(x)[:10] for x in data.ACCOUNTING_MONTH.unique()),
            'channels':sorted(data.DISTRIBUTION_CHANNEL.dropna().unique().tolist())}


@app.get('/api/finance')
def finance(start:dt.date,end:dt.date,line:Literal['All','Motor','Travel']='All',channel:str=Query('All',max_length=100)):
    data=finances(Scope(start=start,end=end,line=line,channel=channel))
    if data.empty:
        return {'rows':[],'brief':None}
    return {'rows':records(data),'brief':executive_brief(data)}


def customers(mode,risk='All',value='All',channel='All'):
    health=read('health')
    if health['ROW_COUNT']!=health['CUSTOMERS'] or health['SNAPSHOT_MIN']!=health['SNAPSHOT_MAX']:
        raise HTTPException(503,'Customer grain validation failed: duplicate customers or mixed snapshots.')
    overview=read('overview',mode)
    rows=read('customers',mode,risk,value,channel)
    return health,overview,rows


@app.get('/api/customers/{mode}')
def customer_list(mode:Literal['NBA','NBO'],risk:str=Query('All',max_length=100),
                  value:str=Query('All',max_length=100),channel:str=Query('All',max_length=100)):
    health,overview,rows=customers(mode,risk,value,channel)
    total=int(overview.CUSTOMERS.sum()) if not overview.empty else 0
    count=lambda mask:int(overview.loc[mask,'CUSTOMERS'].sum()) if not overview.empty else 0
    high_value=overview.LIFETIME_VALUE_BAND.isin(['High','Top']) if not overview.empty else pd.Series(dtype=bool)
    high_risk=overview.RETENTION_RISK_BAND.eq('High') if not overview.empty else pd.Series(dtype=bool)
    priority=(count(high_value & overview.RETENTION_RISK_BAND.eq('Low')) if mode=='NBO' and total else
              int(read('retention_priorities')['PRIORITY_CUSTOMERS'] or 0) if mode=='NBA' else 0)
    counts={'total':total,'high_value':count(high_value),'high_risk':count(high_risk),
            'high_value_at_risk':count(high_value & high_risk),'priority':priority}
    profiles={}
    for _,row in rows.iterrows():
        recommendation,facts,action=customer_evidence(row.to_dict(),mode)
        profiles[row.CUSTOMER_ID]={'finding':recommendation,'facts':facts,'action':action,
                                   'ids':list(range(min(3,len(facts)))),'source':'Rule-based recommendation'}
    return {'rows':records(rows),'profiles':profiles,'counts':counts,
            'filtered_total':int(rows.iloc[0].FILTERED_TOTAL) if not rows.empty else 0,
            'snapshot':str(health['SNAPSHOT_MAX']), 'segments':records(overview),
            'options':{key:sorted(overview[field].dropna().unique().tolist()) if not overview.empty else []
                       for key,field in [('risk','RETENTION_RISK_BAND'),('value','LIFETIME_VALUE_BAND'),('channel','PREFERRED_CHANNEL')]}}


class Explain(BaseModel):
    model_config=ConfigDict(extra='forbid')
    module:Literal['EXEC','NBA','NBO']
    scope:Scope|None=None
    customer_id:str|None=Field(default=None,max_length=100)
    risk:str=Field(default='All',max_length=100)
    value:str=Field(default='All',max_length=100)
    channel:str=Field(default='All',max_length=100)
    ai:bool=True


@app.post('/api/explain')
def explain(body:Explain):
    if body.module=='EXEC':
        if body.scope is None:
            raise HTTPException(422,'Reporting scope is required.')
        data=finances(body.scope)
        if data.empty:
            raise HTTPException(404,'No financial data for this scope.')
        brief=executive_brief(data)
    else:
        _,_,rows=customers(body.module,body.risk,body.value,body.channel)
        selected=rows.loc[rows.CUSTOMER_ID.eq(body.customer_id)] if not rows.empty else rows
        if selected.empty:
            raise HTTPException(404,'Select a customer from the current ranked worklist.')
        finding,facts,action=customer_evidence(selected.iloc[0].to_dict(),body.module)
        brief={'finding':finding,'facts':facts,'action':action,'ids':list(range(min(3,len(facts))))}
    brief['source']='Deterministic explanation'
    if body.ai:
        try:
            ids=get_service().explain(brief['facts'])
            # Validate again at the API boundary; no model prose can reach React.
            brief['ids']=validate_ai_selection({'evidence_ids':ids},len(brief['facts']))[:3]
            brief['source']='AI-curated explanation · Snowflake Cortex'
        except Exception:
            brief['source']='Deterministic explanation · Cortex unavailable or response rejected'
    return brief


@app.post('/api/refresh')
def refresh():
    read.clear()
    return {'status':'refreshed'}


if (DIST/'assets').is_dir():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')


@app.get('/tune-logo.png',include_in_schema=False)
def logo():
    return FileResponse(ROOT/'shared/assets/tune-protect-group-logo.png')


@app.get('/',include_in_schema=False)
def frontend():
    if not (DIST/'index.html').exists():
        raise HTTPException(503,'Build the React frontend first: npm run build.')
    return FileResponse(DIST/'index.html')
