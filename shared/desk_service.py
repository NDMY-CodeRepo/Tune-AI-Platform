"""Snowflake desk persistence using the existing connection and version protocol.

All mutation + activity pairs use one transaction under the connection lock.
Only allowlisted identifiers are interpolated; user values are bound parameters.
"""
from contextlib import contextmanager
from datetime import date
import json
import uuid

from .desk_rules import (EXTRA_FIELDS, PRIORITIES, validate_request,
                         validate_ticket_change, reference)

STATE = 'TUNE_BI_DB.APP_STATE'
TICKETS = STATE + '.DATA_REQUEST_TICKET'
ACTIVITY = STATE + '.DATA_REQUEST_ACTIVITY'
CATALOGUE = STATE + '.REPORT_CATALOGUE'


class DeskPersistence:
    @contextmanager
    def desk_transaction(self):
        with self.lock:
            self.query('BEGIN TRANSACTION')
            try:
                yield
                self.query('COMMIT')
            except BaseException:
                self.query('ROLLBACK')
                raise

    def ticket(self, ticket_id, requester=None):
        rows = self.query(f'SELECT * FROM {TICKETS} WHERE TICKET_ID=?' +
                          (' AND REQUESTER=?' if requester is not None else ''),
                          [ticket_id] + ([requester] if requester is not None else []))
        if len(rows) != 1:
            raise ValueError('Request unavailable. Refresh the queue.')
        return rows.iloc[0].to_dict()

    def create_ticket(self, ticket_id, bu, requester, title, description, category, priority, justification, **extra):
        validate_request(bu,requester,title,description,category,priority,justification,extra)
        with self.desk_transaction():
            existing = self.query(f'SELECT TICKET_ID FROM {TICKETS} WHERE TICKET_ID=?',[ticket_id])
            if not existing.empty:
                if self.ticket(ticket_id)['REQUESTER'] != requester.strip():
                    raise ValueError('Submission reference is already in use.')
                return ticket_id
            columns = ['TICKET_ID','BUSINESS_UNIT','REQUESTER','TITLE','DESCRIPTION','CATEGORY','PRIORITY','BUSINESS_JUSTIFICATION']
            values = [ticket_id,bu.strip(),requester.strip(),title.strip(),description.strip(),category,priority,justification.strip()]
            for field in EXTRA_FIELDS:
                if field in extra:
                    columns.append(field.upper())
                    value = extra[field]
                    values.append(str(value).strip() if value is not None else None)
            self.query(f"INSERT INTO {TICKETS} (TICKET_NUMBER,{','.join(columns)}) VALUES ({STATE}.DATA_REQUEST_NUMBER.NEXTVAL,{','.join('?' for _ in columns)})",values)
            self._activity(ticket_id,requester.strip(),'Business User','STATUS_UPDATE','Request submitted · New')
        return ticket_id

    def _activity(self, ticket_id, author, role, entry_type, message, internal=False):
        self.query(f'''INSERT INTO {ACTIVITY}
          (ACTIVITY_ID,TICKET_ID,AUTHOR,AUTHOR_ROLE,ENTRY_TYPE,MESSAGE,IS_INTERNAL)
          VALUES (?,?,?,?,?,?,?)''',
          [str(uuid.uuid4()),ticket_id,author,role,entry_type,message,bool(internal)])

    def activity(self, ticket_id, requester=None):
        # Scope both ticket and history; do not fetch internal text into the BU view.
        if requester is not None:
            self.ticket(ticket_id,requester)
        return self.query(f'''SELECT a.*,t.TICKET_NUMBER FROM {ACTIVITY} a
          JOIN {TICKETS} t ON a.TICKET_ID=t.TICKET_ID
          WHERE a.TICKET_ID=? {'AND NOT a.IS_INTERNAL' if requester is not None else ''}
          ORDER BY a.CREATED_AT,a.ACTIVITY_ID''',[ticket_id])

    def change_ticket(self, ticket_id, version, actor, role, *, changes=None,
                      entry_type='COMMENT', message='', internal=False, resume=False):
        """Guard role, stored state, required fields and compare-and-set in one place."""
        if role not in ('Business User','Data Team') or not actor.strip() or len(actor)>100:
            raise ValueError('Choose a demo identity and role.')
        if len(message)>4000:
            raise ValueError('Messages must be 4,000 characters or fewer.')
        allowed = {'ASSIGNED_TO','CONFIRMED_PRIORITY','TARGET_DATE','EFFORT_ESTIMATE',
                   'STATUS','PROGRESS_NOTES','RESOLUTION_NOTES','DELIVERED_REFERENCE'}
        changes = dict(changes or {})
        if set(changes)-allowed:
            raise ValueError('Unsupported ticket field.')
        if entry_type not in ('COMMENT','CLARIFICATION_REQUEST','CLARIFICATION_RESPONSE','STATUS_UPDATE','RESOLUTION'):
            raise ValueError('Unsupported activity type.')
        if entry_type in ('COMMENT','CLARIFICATION_REQUEST','CLARIFICATION_RESPONSE') and not message.strip():
            raise ValueError('Enter a message before saving.')
        with self.desk_transaction():
            t = self.ticket(ticket_id, actor if role=='Business User' else None)
            if int(t['VERSION']) != int(version):
                raise ValueError('This ticket changed in another session. Refresh before updating.')
            if role=='Business User':
                if internal or set(changes)-{'STATUS'} or entry_type not in ('COMMENT','CLARIFICATION_RESPONSE','STATUS_UPDATE'):
                    raise ValueError('Requesters cannot overwrite Data Team-owned fields.')
                if 'STATUS' in changes and (t['STATUS'],changes['STATUS']) not in (
                    ('RESOLVED','CLOSED'),('RESOLVED','IN_PROGRESS')):
                    raise ValueError('Requesters may confirm closure or reopen a resolved request.')
                if changes.get('STATUS')=='IN_PROGRESS' and not message.strip():
                    raise ValueError('Explain why this request should reopen.')
            elif entry_type=='CLARIFICATION_RESPONSE':
                raise ValueError('Only the requester can respond to clarification.')
            if t['STATUS']=='CLOSED' and (changes or entry_type!='COMMENT'):
                raise ValueError('Closed requests only accept additional comments.')
            if entry_type=='CLARIFICATION_REQUEST':
                if internal or t['STATUS']!='IN_PROGRESS':
                    raise ValueError('Request clarification from an in-progress ticket using a BU-visible message.')
                changes['STATUS']='WAITING_FOR_BU'
            if entry_type=='CLARIFICATION_RESPONSE':
                if t['STATUS']!='WAITING_FOR_BU':
                    raise ValueError('This request is not waiting for clarification.')
                if resume:
                    changes['STATUS']='IN_PROGRESS'
            status = changes.get('STATUS',t['STATUS'])
            if status=='WAITING_FOR_BU' and t['STATUS']!='WAITING_FOR_BU' and entry_type!='CLARIFICATION_REQUEST':
                raise ValueError('Use Request clarification and enter a BU-visible question.')
            if internal and changes:
                raise ValueError('Internal notes cannot modify BU-visible request fields.')
            owner = changes.get('ASSIGNED_TO',t.get('ASSIGNED_TO')) or ''
            notes = changes.get('RESOLUTION_NOTES',t.get('RESOLUTION_NOTES')) or ''
            # Legacy unassigned resolved tickets can still receive comments.
            if changes or status!=t['STATUS']:
                validate_ticket_change(t['STATUS'],status,owner,notes)
            merged = {**t,**changes}
            if status in ('TRIAGED','IN_PROGRESS','WAITING_FOR_BU') and changes and merged.get('CONFIRMED_PRIORITY') not in PRIORITIES:
                raise ValueError('Confirm priority before triaging or starting work.')
            if changes.get('CONFIRMED_PRIORITY') is not None and changes['CONFIRMED_PRIORITY'] not in PRIORITIES:
                raise ValueError('Invalid confirmed priority.')
            if changes.get('EFFORT_ESTIMATE') not in (None,'','S','M','L'):
                raise ValueError('Effort estimate must be S, M or L.')
            for key,value in changes.items():
                if key=='TARGET_DATE' and value:
                    date.fromisoformat(str(value))
                elif value is not None and len(str(value)) > (100 if key=='ASSIGNED_TO' else 2000 if key=='DELIVERED_REFERENCE' else 4000):
                    raise ValueError('An update field exceeds its allowed length.')
            assignments = [f'{key}=?' for key in changes]
            values = [str(v).strip() if v is not None else None for v in changes.values()]
            if status=='RESOLVED' and t['STATUS']!='RESOLVED':
                assignments.append('RESOLVED_AT=CURRENT_TIMESTAMP()')
            elif status=='IN_PROGRESS' and t['STATUS']=='RESOLVED':
                assignments.append('RESOLVED_AT=NULL')
            assignments += ['UPDATED_AT=CURRENT_TIMESTAMP()','VERSION=VERSION+1']
            result = self.query(f"UPDATE {TICKETS} SET {','.join(assignments)} WHERE TICKET_ID=? AND VERSION=? AND STATUS=?",
                                values+[ticket_id,int(version),t['STATUS']])
            if int(result.iloc[0,0])!=1:
                raise ValueError('This ticket changed in another session. Refresh before updating.')
            if changes:
                # Exact before/after values preserve edits to owner, priority, target and resolution.
                audit = json.dumps({k:{'from':t.get(k),'to':v} for k,v in changes.items()},default=str,ensure_ascii=False)
                self._activity(ticket_id,actor,role,'STATUS_UPDATE',audit,internal)
            if status=='RESOLVED' and t['STATUS']!='RESOLVED':
                self._activity(ticket_id,actor,role,'RESOLUTION',notes)
            if message.strip():
                self._activity(ticket_id,actor,role,entry_type,message.strip(),internal)

    def update_ticket(self, ticket_id, version, old_status, status, owner, progress, notes):
        # Backward-compatible signature; old_status is never trusted as the stored state.
        self.change_ticket(ticket_id,version,'demo.engineer','Data Team',changes={
            'ASSIGNED_TO':owner,'STATUS':status,'PROGRESS_NOTES':progress,'RESOLUTION_NOTES':notes,
            'CONFIRMED_PRIORITY':self.ticket(ticket_id).get('CONFIRMED_PRIORITY') or 'MEDIUM'},
            entry_type='STATUS_UPDATE')

    def desk_queue(self, requester=None, status='All', bu='All', category='All', priority='All', owner='All', sort='Newest', scope='All records'):
        where,params = self._desk_scope(requester,scope)
        for col,val in [('STATUS',status),('BUSINESS_UNIT',bu),('CATEGORY',category),('COALESCE(CONFIRMED_PRIORITY,PRIORITY)',priority),('COALESCE(NULLIF(ASSIGNED_TO,\'\'),\'Unassigned\')',owner)]:
            if val!='All':
                where.append(col+'=?'); params.append(val)
        order={'Recently updated':'UPDATED_AT DESC','Newest':'CREATED_AT DESC','Oldest / age':'CREATED_AT ASC','Priority':"CASE COALESCE(CONFIRMED_PRIORITY,PRIORITY) WHEN 'HIGH' THEN 0 WHEN 'MEDIUM' THEN 1 ELSE 2 END,CREATED_AT ASC"}
        if sort not in order:
            raise ValueError('Invalid sort order.')
        return self.query(f"SELECT *,DATEDIFF(day,CREATED_AT,CURRENT_TIMESTAMP()) AGE_DAYS,COUNT(*) OVER() MATCHING_TOTAL FROM {TICKETS} WHERE {' AND '.join(where)} ORDER BY {order[sort]},TICKET_ID LIMIT 200",params)

    def _desk_scope(self, requester, scope):
        where,params=['1=1'],[]
        if requester is not None:
            where.append('REQUESTER=?'); params.append(requester)
        if scope=='Synthetic demo only':
            where.append('IS_DEMO=TRUE')
        elif scope=='Exclude validation':
            where.append("TITLE NOT ILIKE '[Validation]%'")
        elif scope!='All records':
            raise ValueError('Invalid record scope.')
        return where,params

    def desk_metrics(self, requester=None, scope='All records'):
        where,params=self._desk_scope(requester,scope)
        return self.query(f'''SELECT COUNT_IF(STATUS NOT IN ('RESOLVED','CLOSED')) OPEN_REQUESTS,
        COUNT_IF(STATUS='NEW' OR (NULLIF(ASSIGNED_TO,'') IS NULL AND STATUS NOT IN ('RESOLVED','CLOSED'))) NEW_UNASSIGNED,
        COUNT_IF(STATUS='IN_PROGRESS') IN_PROGRESS,COUNT_IF(STATUS='WAITING_FOR_BU') WAITING_FOR_BU,
        COUNT_IF(STATUS IN ('RESOLVED','CLOSED')) RESOLVED_CLOSED,
        COUNT_IF(STATUS NOT IN ('RESOLVED','CLOSED') AND TARGET_DATE<CURRENT_DATE()) OVERDUE,
        COUNT_IF(STATUS IN ('RESOLVED','CLOSED') AND RESOLVED_AT>=DATE_TRUNC('month',CURRENT_DATE())) RESOLVED_MONTH
        FROM {TICKETS} WHERE {' AND '.join(where)}''',params).iloc[0].fillna(0).to_dict()

    def desk_distribution(self, dimension, scope='All records'):
        columns={'Business unit':'BUSINESS_UNIT','Priority':'COALESCE(CONFIRMED_PRIORITY,PRIORITY)',
                 'Assigned owner':"COALESCE(NULLIF(ASSIGNED_TO,''),'Unassigned')",'Status':'STATUS'}
        if dimension not in columns:
            raise ValueError('Unknown distribution.')
        where,params=self._desk_scope(None,scope)
        return self.query(f"SELECT {columns[dimension]} LABEL,COUNT(*) REQUESTS FROM {TICKETS} WHERE {' AND '.join(where)} GROUP BY 1 ORDER BY REQUESTS DESC,LABEL",params)

    def desk_owners(self):
        return self.query(f"SELECT DISTINCT ASSIGNED_TO FROM {TICKETS} WHERE NULLIF(ASSIGNED_TO,'') IS NOT NULL ORDER BY 1")

    def catalogue(self, keyword='', domain='All'):
        where,params=['1=1'],[]
        if keyword.strip():
            where.append('(REPORT_NAME ILIKE ? OR DESCRIPTION ILIKE ?)')
            params += ['%'+keyword.strip()+'%']*2
        if domain!='All':
            where.append('BUSINESS_DOMAIN=?'); params.append(domain)
        return self.query(f"SELECT * FROM {CATALOGUE} WHERE {' AND '.join(where)} ORDER BY IS_DEMO,REPORT_NAME LIMIT 100",params)
