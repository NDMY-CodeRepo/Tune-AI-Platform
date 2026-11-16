"""Small Service Desk rules. The demo role is a workflow guard, not authentication."""
from datetime import date
from urllib.parse import urlparse

CATEGORIES = ['REPORT_REQUEST', 'DATA_EXTRACT', 'DATA_ISSUE', 'ACCESS_REQUEST', 'ENHANCEMENT', 'OTHER']
CATEGORY_LABELS = dict(zip(CATEGORIES, ['Report / Dashboard', 'Data Extract', 'Data Issue', 'Access Request', 'Enhancement', 'Other']))
PRIORITIES = ['LOW', 'MEDIUM', 'HIGH']
STATUSES = ['NEW', 'TRIAGED', 'IN_PROGRESS', 'WAITING_FOR_BU', 'RESOLVED', 'CLOSED']
STATUS_LABELS = dict(zip(STATUSES, ['New', 'Triaged', 'In Progress', 'Waiting for BU', 'Resolved', 'Closed']))
# Same-status saves are allowed, including comments; closed tickets cannot reopen.
TRANSITIONS = {
 'NEW': ['NEW', 'TRIAGED'],
 'TRIAGED': ['TRIAGED', 'IN_PROGRESS'],
 'IN_PROGRESS': ['IN_PROGRESS', 'WAITING_FOR_BU', 'RESOLVED'],
 'WAITING_FOR_BU': ['WAITING_FOR_BU', 'IN_PROGRESS'],
 'RESOLVED': ['RESOLVED', 'IN_PROGRESS', 'CLOSED'],
 'CLOSED': ['CLOSED'],
}
BUSINESS_UNITS = ['Motor', 'Travel', 'Finance', 'Claims', 'Distribution', 'Other']
DOMAINS = ['Motor', 'Travel', 'Claims', 'Finance', 'Customer', 'Other']
FORMATS = ['Dashboard', 'Excel', 'CSV', 'PDF', 'Other']
EXTRA_FIELDS = {'required_by': None, 'business_impact': 2000, 'data_domain': 100,
 'existing_reference': 1000, 'reporting_period': 200, 'required_fields': 2000, 'output_format': 30}


def reference(number):
    return f'TDS-{int(number):06d}'


def safe_link(value):
    return bool(value and urlparse(str(value)).scheme in ('https', 'http') and urlparse(str(value)).netloc)


def validate_ticket_change(old_status, status, owner, notes):
    if status not in TRANSITIONS.get(old_status, []):
        raise ValueError('This status transition is not allowed. Follow the ticket workflow.')
    if status != 'NEW' and not owner.strip():
        raise ValueError('Assign an owner before triaging or starting work.')
    if status in ('RESOLVED', 'CLOSED') and not notes.strip():
        raise ValueError('Resolution notes are required before resolving or closing a request.')


def validate_request(bu, requester, title, description, category, priority, justification, extra):
    fields = [(bu,100),(requester,100),(title,200),(description,4000),(justification,2000)]
    if not all(isinstance(x,str) and x.strip() for x,_ in fields):
        raise ValueError('Complete all required request fields.')
    if category not in CATEGORIES or priority not in PRIORITIES:
        raise ValueError('Invalid request category or priority.')
    if set(extra) - set(EXTRA_FIELDS):
        raise ValueError('Requesters cannot set Data Team-owned fields.')
    fields += [(extra.get(k) or '',limit) for k,limit in EXTRA_FIELDS.items() if limit]
    if any(not isinstance(x,str) or len(x)>limit for x,limit in fields):
        raise ValueError('A request field exceeds its allowed length.')
    if extra.get('data_domain') and extra['data_domain'] not in DOMAINS:
        raise ValueError('Choose a valid data domain.')
    if extra.get('output_format') and extra['output_format'] not in FORMATS:
        raise ValueError('Choose a valid output format.')
    if extra.get('required_by'):
        try:
            requested = date.fromisoformat(str(extra['required_by']))
        except ValueError:
            raise ValueError('Choose a valid required-by date.') from None
        if requested < date.today():
            raise ValueError('Required-by date cannot be in the past.')
