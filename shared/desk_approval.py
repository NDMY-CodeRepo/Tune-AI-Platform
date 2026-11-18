"""Effort approval rules used inside the existing ticket transaction.

Ticket VERSION protects every save; EFFORT_ASSESSMENT_VERSION identifies the exact
size/notes submitted for a BU decision. No legacy approval is fabricated.
"""
from datetime import datetime, timezone

ASSESSMENT_FIELDS = {'EFFORT_ESTIMATE','ASSESSMENT_NOTES'}
DECISION_FIELDS = ('APPROVAL_DECISION','APPROVAL_ASSESSMENT_VERSION','APPROVAL_DECIDED_BY',
                   'APPROVAL_DECIDED_AT','APPROVAL_COMMENTS')
REASSESSMENT_STATES = {'TRIAGED','AWAITING_BU_APPROVAL','APPROVED','REJECTED',
                       'IN_PROGRESS','WAITING_FOR_BU','RESOLVED'}


def assessment_version(t):
    return int(t.get('EFFORT_ASSESSMENT_VERSION') or 0)


def valid_effort_approval(t):
    return bool(assessment_version(t)>0 and t.get('EFFORT_ESTIMATE') in ('S','M','L')
                and (t.get('ASSESSMENT_NOTES') or '').strip() and t.get('ASSESSED_BY') and t.get('ASSESSED_AT')
                and t.get('APPROVAL_DECISION')=='APPROVED'
                and t.get('APPROVAL_ASSESSMENT_VERSION')==assessment_version(t)
                and t.get('APPROVAL_DECIDED_BY')==t.get('REQUESTER') and t.get('APPROVAL_DECIDED_AT'))


def prepare_effort_change(t,actor,role,changes,action=None,reviewed_version=None,confirmed=False,message=''):
    """Return validated server-owned changes, audit events, and a reassessment flag."""
    changes=dict(changes)
    old=t['STATUS'];events=[]
    revised=any(k in changes and (changes[k] or '')!=(t.get(k) or '') for k in ASSESSMENT_FIELDS)
    now=datetime.now(timezone.utc).isoformat()
    if action not in (None,'SUBMIT','APPROVE','REJECT','REASSESS'):
        raise ValueError('Unknown effort approval action.')
    if action in ('APPROVE','REJECT'):
        if role!='Business User' or actor!=t['REQUESTER']:
            raise ValueError('Only this request\'s Business User can decide the effort approval.')
        if not confirmed:
            raise ValueError('Explicitly confirm your effort approval decision.')
        if changes:
            raise ValueError('An approval decision cannot change the assessed effort or other ticket fields.')
        if old!='AWAITING_BU_APPROVAL':
            raise ValueError('This request is not awaiting effort approval.')
        if reviewed_version is None or int(reviewed_version)!=assessment_version(t):
            raise ValueError('The effort assessment changed. Refresh and review the current assessment.')
        if not (assessment_version(t)>0 and t.get('EFFORT_ESTIMATE') in ('S','M','L')
                and (t.get('ASSESSMENT_NOTES') or '').strip() and t.get('ASSESSED_BY') and t.get('ASSESSED_AT')):
            raise ValueError('A complete submitted effort assessment is required.')
        if action=='REJECT' and not message.strip():
            raise ValueError('A rejection reason is required.')
        decision='APPROVED' if action=='APPROVE' else 'REJECTED'
        changes.update(STATUS=decision,APPROVAL_DECISION=decision,
            APPROVAL_ASSESSMENT_VERSION=assessment_version(t),APPROVAL_DECIDED_BY=actor,
            APPROVAL_DECIDED_AT=now,APPROVAL_COMMENTS=message.strip())
        events.append(('EFFORT_'+decision, f'Assessment v{assessment_version(t)} · Effort {t["EFFORT_ESTIMATE"]} · '
                       +(message.strip() or 'Approved without additional comments.')))
        return changes,events,False
    if action and role!='Data Team':
        raise ValueError('Only the Data Team can assess or submit effort.')
    if role!='Data Team' and revised:
        raise ValueError('Requesters cannot change the effort assessment.')
    if action=='REASSESS':
        if old not in REASSESSMENT_STATES:
            raise ValueError('This ticket cannot be reassessed in its current state.')
        if 'STATUS' in changes and changes['STATUS']!='TRIAGED':
            raise ValueError('Reassessment returns the request to Triaged.')
        changes['STATUS']='TRIAGED'
    if revised or action in ('SUBMIT','REASSESS'):
        if old=='CLOSED':
            raise ValueError('Closed requests cannot change their effort assessment.')
        if revised and changes.get('STATUS')=='IN_PROGRESS':
            raise ValueError('Revised effort must receive a new BU approval before work can start.')
        # Every edit/resubmission is a new assessment identity, even with the same size.
        revision=assessment_version(t)+1
        changes.update(EFFORT_ASSESSMENT_VERSION=revision,ASSESSED_BY=actor,ASSESSED_AT=now)
        changes.update({k:None for k in DECISION_FIELDS})
        if (revised and old not in ('NEW','TRIAGED')) or action=='REASSESS':
            changes['STATUS']='TRIAGED'
        events.append(('EFFORT_REVISED' if assessment_version(t)>0 else 'EFFORT_ASSESSED',
                       f'Assessment v{revision} · Effort {changes.get("EFFORT_ESTIMATE",t.get("EFFORT_ESTIMATE")) or "Not set"} · '
                       +(changes.get('ASSESSMENT_NOTES',t.get('ASSESSMENT_NOTES')) or 'Assessment draft.')
                       + (' · '+message.strip() if action=='REASSESS' and message.strip() else '')))
    if action=='SUBMIT':
        if old!='TRIAGED':
            raise ValueError('Triage the request before submitting effort for BU approval. Reassess rejected estimates first.')
        merged={**t,**changes}
        if merged.get('EFFORT_ESTIMATE') not in ('S','M','L') or not (merged.get('ASSESSMENT_NOTES') or '').strip():
            raise ValueError('Provide effort size S/M/L and assessment notes before requesting approval.')
        changes['STATUS']='AWAITING_BU_APPROVAL'
        events.append(('EFFORT_SUBMITTED',f'Assessment v{assessment_version(merged)} submitted by {actor}.'))
        events.append(('APPROVAL_REQUESTED',f'Business User approval requested for assessment v{assessment_version(merged)}.'))
    elif changes.get('STATUS') in ('AWAITING_BU_APPROVAL','APPROVED','REJECTED') and changes['STATUS']!=old:
        raise ValueError('Use the explicit effort submission or BU decision action.')
    elif old=='REJECTED' and changes.get('STATUS')=='TRIAGED' and action!='REASSESS' and not revised:
        raise ValueError('Use Reassess effort to revise and resubmit a rejected assessment.')
    merged={**t,**changes}
    status=changes.get('STATUS',old)
    if status=='IN_PROGRESS' and old!='IN_PROGRESS' and not valid_effort_approval(merged):
        raise ValueError('Current effort assessment requires explicit BU approval before work can start or resume. Reassess legacy requests first.')
    return changes,events,(changes.get('STATUS')=='TRIAGED' and old in REASSESSMENT_STATES and old!='TRIAGED')
