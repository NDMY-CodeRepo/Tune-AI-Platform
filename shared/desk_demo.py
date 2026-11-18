"""Explicit, idempotent synthetic examples; never run during application startup."""
from .desk_service import TICKETS, CATALOGUE


def seed_demo(service):
    examples = [
        ('motor-report','Motor','Motor claims report request','REPORT_REQUEST','NEW'),
        ('travel-extract','Travel','Travel performance extract','DATA_EXTRACT','TRIAGED'),
        ('finance-issue','Finance','Finance reconciliation issue','DATA_ISSUE','IN_PROGRESS'),
        ('claims-question','Claims','Claims dashboard clarification','REPORT_REQUEST','WAITING_FOR_BU'),
        ('motor-monthly','Motor','Motor monthly report','REPORT_REQUEST','RESOLVED'),
    ]
    for key,bu,title,category,target in examples:
        tid='DEMO-TDS-'+key
        exists=not service.query(f'SELECT TICKET_ID FROM {TICKETS} WHERE TICKET_ID=?',[tid]).empty
        if exists and service.ticket(tid)['STATUS']!='NEW':
            continue
        service.create_ticket(tid,bu,'motor.demo','[Demo] '+title,
            'Synthetic demonstration request. No real business data or delivery is implied.',category,'MEDIUM',
            'Illustrates a structured business-to-data-team workflow.',business_impact='Synthetic demo: supports monthly review.',
            data_domain=bu,required_fields='Month, channel, claim count',output_format='Excel')
        # Seed marker is not part of the requester mutation API.
        service.query(f'UPDATE {TICKETS} SET IS_DEMO=TRUE WHERE TICKET_ID=?',[tid])
        for status in ['TRIAGED','IN_PROGRESS']:
            if target=='NEW':
                break
            t=service.ticket(tid)
            if status=='IN_PROGRESS':
                service.change_ticket(tid,t['VERSION'],'demo.engineer','Data Team',effort_action='SUBMIT',entry_type='STATUS_UPDATE',
                    changes={'ASSESSMENT_NOTES':'Illustrative mapping, development and validation effort.'})
                t=service.ticket(tid)
                service.change_ticket(tid,t['VERSION'],'motor.demo','Business User',effort_action='APPROVE',entry_type='STATUS_UPDATE',
                    assessment_version=t['EFFORT_ASSESSMENT_VERSION'],confirmed=True)
                t=service.ticket(tid)
            service.change_ticket(tid,t['VERSION'],'demo.engineer','Data Team',changes={
                'ASSIGNED_TO':'demo.engineer','CONFIRMED_PRIORITY':'MEDIUM','STATUS':status,'EFFORT_ESTIMATE':'M'},entry_type='STATUS_UPDATE')
            if target==status:
                break
        t=service.ticket(tid)
        if target=='WAITING_FOR_BU':
            service.change_ticket(tid,t['VERSION'],'demo.engineer','Data Team',entry_type='CLARIFICATION_REQUEST',
                                  message='Synthetic example: should the dashboard group claims by notification month or settlement month?')
        elif target=='RESOLVED':
            service.change_ticket(tid,t['VERSION'],'demo.engineer','Data Team',changes={
                'STATUS':'RESOLVED','RESOLUTION_NOTES':'Synthetic demonstration resolution. No actual report has been delivered.',
                'DELIVERED_REFERENCE':'DEMO-OUTPUT: Motor monthly report (illustrative reference only)'},entry_type='STATUS_UPDATE')
    # Only add illustrative catalogue entries when real catalogue records are absent.
    real=service.query(f'SELECT COUNT(*) N FROM {CATALOGUE} WHERE NOT IS_DEMO')
    if int(real.iloc[0,0])==0:
        for rid,name,domain,description in [
            ('demo-motor','[Demo] Motor monthly overview','Motor','Illustrative catalogue entry for premium and claims trends.'),
            ('demo-travel','[Demo] Travel performance summary','Travel','Illustrative catalogue entry for monthly channel performance.'),
            ('demo-finance','[Demo] Finance reconciliation guide','Finance','Illustrative catalogue entry for reconciliation definitions.')]:
            service.query(f'''INSERT INTO {CATALOGUE}
              (REPORT_ID,REPORT_NAME,DESCRIPTION,BUSINESS_DOMAIN,DATA_OWNER,REFRESH_FREQUENCY,IS_DEMO)
              SELECT ?,?,?,?,?,?,TRUE WHERE NOT EXISTS (SELECT 1 FROM {CATALOGUE} WHERE REPORT_ID=?)''',
              [rid,name,description,domain,'Demo Data Team','Monthly (illustrative)',rid])
