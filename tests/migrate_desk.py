"""Explicit additive migration / seed runner. Uses the existing connection settings."""
import argparse
import json
from pathlib import Path
from shared.snowflake_service import get_service
from shared.desk_demo import seed_demo
from shared.desk_service import TICKETS

ROOT=Path(__file__).resolve().parents[1]


def gold_snapshot(s):
    return s.query("SELECT SHA2(GET_DDL('SCHEMA','TUNE_BI_DB.GOLD',TRUE),256) HASH").iloc[0,0]


def run(seed=False):
    s=get_service()
    original=s.query(f'SELECT * FROM {TICKETS} ORDER BY TICKET_ID')
    numbers=(original.loc[original.TICKET_NUMBER.notna(),['TICKET_ID','TICKET_NUMBER']].copy()
             if 'TICKET_NUMBER' in original else None)
    columns=[c for c in original.columns if c!='TICKET_NUMBER']
    original=original[columns]
    before=gold_snapshot(s)
    sql=(ROOT/'sql/desk_upgrade.sql').read_text()
    import re
    statements=[x.strip() for x in re.sub(r'--[^\n]*','',sql).split(';') if x.strip()]
    for _ in range(2):
        for statement in statements:
            try:
                s.query(statement)
            except Exception:
                print("Failed migration statement:",statement)
                raise
        current=s.query(f"SELECT {','.join(columns)} FROM {TICKETS} ORDER BY TICKET_ID")
        # On reruns new fields are included too; all preexisting values must remain unchanged.
        assert original.equals(current),'Existing ticket values changed during migration'
        if numbers is not None and not numbers.empty:
            assigned=s.query(f'SELECT TICKET_ID,TICKET_NUMBER FROM {TICKETS} ORDER BY TICKET_ID')
            assert numbers.reset_index(drop=True).equals(assigned[assigned.TICKET_ID.isin(numbers.TICKET_ID)].reset_index(drop=True)), 'Assigned references changed'
    report={'migration':'PASS','idempotent_rerun':'PASS','existing_tickets_preserved':len(original),
            'existing_reference_values_preserved':'PASS',
            'historical_validation_records':int(s.query(f"SELECT COUNT(*) N FROM {TICKETS} WHERE TITLE ILIKE '[Validation]%'").iloc[0,0]),
            'gold_before':before,'gold_after':gold_snapshot(s)}
    assert report['gold_before']==report['gold_after'],'GOLD definition changed'
    if seed:
        seed_demo(s)
        count=s.query(f'SELECT COUNT(*) N FROM {TICKETS} WHERE IS_DEMO=TRUE').iloc[0,0]
        seed_demo(s)
        assert int(count)==int(s.query(f'SELECT COUNT(*) N FROM {TICKETS} WHERE IS_DEMO=TRUE').iloc[0,0])
        report.update(demo_seed='PASS',synthetic_tickets=int(count),seed_rerun='PASS')
    (ROOT/'validation/desk_upgrade_migration.json').write_text(json.dumps(report,indent=2,default=str))
    print(json.dumps(report,indent=2,default=str))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed-demo',action='store_true')
    run(p.parse_args().seed_demo)
