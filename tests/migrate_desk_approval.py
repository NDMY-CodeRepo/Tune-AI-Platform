"""Explicit additive approval migration and optional illustrative pending ticket."""
import argparse
import json
from pathlib import Path
import re
import uuid
from shared.snowflake_service import get_service
from shared.desk_service import TICKETS,ACTIVITY

ROOT=Path(__file__).resolve().parents[1]
DEMO_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'tune-desk/effort-approval/demo-1'))


def gold_hash(s):
    return s.query("SELECT SHA2(GET_DDL('SCHEMA','TUNE_BI_DB.GOLD',TRUE),256) HASH").iloc[0,0]


def seed(s):
    existing=s.query(f'SELECT TICKET_ID FROM {TICKETS} WHERE TICKET_ID=?',[DEMO_ID])
    if existing.empty:
        s.create_ticket(DEMO_ID,'Claims','motor.demo','[Demo] Motor claims dashboard enhancement',
            'Illustrative effort approval request. No production delivery is implied.', 'ENHANCEMENT','MEDIUM',
            'Demonstrate business acknowledgement before Data Team engineering.',
            business_impact='Synthetic demonstration only.',data_domain='Motor',output_format='Dashboard')
        s.query(f'UPDATE {TICKETS} SET IS_DEMO=TRUE WHERE TICKET_ID=?',[DEMO_ID])
    t=s.ticket(DEMO_ID)
    if t['STATUS']=='NEW':
        s.change_ticket(DEMO_ID,t['VERSION'],'demo.engineer','Data Team',changes={
            'ASSIGNED_TO':'demo.engineer','CONFIRMED_PRIORITY':'MEDIUM','STATUS':'TRIAGED'},entry_type='STATUS_UPDATE')
        t=s.ticket(DEMO_ID)
    if t['STATUS']=='TRIAGED' and not t.get('EFFORT_ASSESSMENT_VERSION'):
        s.change_ticket(DEMO_ID,t['VERSION'],'demo.engineer','Data Team',changes={
            'EFFORT_ESTIMATE':'M','ASSESSMENT_NOTES':'Data mapping, development and validation are required.'},
            effort_action='SUBMIT',entry_type='STATUS_UPDATE')
    # Never reset a demonstrator's subsequent approval/rejection or edits.
    return s.ticket(DEMO_ID)


def run(seed_demo=False):
    s=get_service();before_gold=gold_hash(s)
    original=s.query(f'SELECT * FROM {TICKETS} ORDER BY TICKET_ID')
    original_activity=s.query(f'SELECT * FROM {ACTIVITY} ORDER BY ACTIVITY_ID')
    columns=original.columns.tolist()
    statements=[x.strip() for x in re.sub(r'--[^\n]*','',(ROOT/'sql/desk_effort_approval.sql').read_text()).split(';') if x.strip()]
    for _ in range(2):
        for sql in statements:
            s.query(sql)
        current=s.query(f"SELECT {','.join(columns)} FROM {TICKETS} ORDER BY TICKET_ID")
        assert original.equals(current),'Existing ticket data changed during migration'
        assert original_activity.equals(s.query(f'SELECT * FROM {ACTIVITY} ORDER BY ACTIVITY_ID')),'Historical activity changed'
    assert before_gold==gold_hash(s),'GOLD definitions changed'
    result=dict(migration='PASS',idempotent_rerun='PASS',existing_tickets_preserved=len(original),
                existing_activity_preserved=len(original_activity),gold_before=before_gold,gold_after=gold_hash(s),
                historical_backfill=False)
    if seed_demo:
        ticket=seed(s);first_version=ticket['VERSION'];again=seed(s)
        assert first_version==again['VERSION'],'Repeated seed changed the ticket'
        result['demo']={k:str(ticket[k]) for k in ('TICKET_ID','TICKET_NUMBER','STATUS','EFFORT_ESTIMATE','EFFORT_ASSESSMENT_VERSION')}
        result['seed_idempotent']='PASS'
    (ROOT/'validation/desk_effort_migration.json').write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed-demo',action='store_true')
    run(parser.parse_args().seed_demo)
