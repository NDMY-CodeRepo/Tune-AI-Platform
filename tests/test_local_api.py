"""API grounding, same-origin guard, parameter binding and failure contracts."""
from unittest.mock import patch
import pandas as pd
import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from apps.api.main import app


def financial():
    base=dict(GWP=100,PLAN_GWP=110,GWP_VARIANCE=-10,GWP_VARIANCE_PCT=-10/110,
              NEP=80,PLAN_NEP=90,NEP_VARIANCE=-10,NEP_VARIANCE_PCT=-10/90,
              NET_INCURRED_CLAIMS=40,LOSS_RATIO=.5,LINE_OF_BUSINESS=None,
              DISTRIBUTION_CHANNEL=None,KEY_COUNT=1,MISSING_ACTUAL=0,MISSING_PLAN=0)
    return pd.DataFrame([dict(base,LEVEL='TOTAL'),dict(base,LEVEL='LINE',LINE_OF_BUSINESS='Motor')])


def test_finance_adapter_preserves_values_and_passes_bound_scope():
    with patch('apps.api.main.read',return_value=financial()) as read:
        result=TestClient(app).get('/api/finance',params={'start':'2026-01-01','end':'2026-10-01','line':'Motor','channel':"Agency';--"})
    assert result.status_code==200
    assert result.json()['rows'][0]['GWP']==100
    assert result.json()['brief']['ids']==[3]
    read.assert_called_once_with('finance','2026-01-01','2026-10-01','Motor',"Agency';--",True)


def test_invalid_dates_rejected_before_query():
    with patch('apps.api.main.read') as read:
        response=TestClient(app).get('/api/finance?start=2026-10-01&end=2026-01-01')
    assert response.status_code==422 and not read.called


def test_ai_can_only_select_verified_evidence_and_invalid_selection_falls_back():
    body={'module':'EXEC','scope':{'start':'2026-01-01','end':'2026-10-01'}}
    with patch('apps.api.main.read',return_value=financial()),patch('apps.api.main.get_service') as service:
        service.return_value.explain.return_value=[999]
        result=TestClient(app).post('/api/explain',json=body)
    assert result.status_code==200
    assert 'response rejected' in result.json()['source']
    assert result.json()['ids']==[3]
    assert TestClient(app).post('/api/explain',json={**body,'facts':['invented finding']}).status_code==422


def test_cortex_disabled_does_not_call_ai():
    with patch('apps.api.main.read',return_value=financial()),patch('apps.api.main.get_service') as service:
        result=TestClient(app).post('/api/explain',json={'module':'EXEC','ai':False,'scope':{'start':'2026-01-01','end':'2026-10-01'}})
    assert result.status_code==200 and not service.called


def test_local_origin_and_host_guards():
    client=TestClient(app)
    assert client.post('/api/refresh',headers={'origin':'https://unrelated.example'}).status_code==403
    assert client.get('/api/health',headers={'host':'unrelated.example'}).status_code==400
    assert client.get('/api/health').json()['status']=='ok'


def test_connection_failure_is_sanitized_and_empty_selection_is_explicit():
    with patch('apps.api.main.read',side_effect=RuntimeError('private credentials')):
        response=TestClient(app,raise_server_exceptions=False).get('/api/finance?start=2026-01-01&end=2026-10-01')
    assert response.status_code==503 and 'private credentials' not in response.text
    with patch('apps.api.main.read',return_value=pd.DataFrame()):
        assert TestClient(app).get('/api/finance?start=2026-01-01&end=2026-10-01').json()=={'rows':[],'brief':None}


def test_customer_brief_requires_current_worklist_membership():
    rows=pd.DataFrame([{'CUSTOMER_ID':'C1'}])
    with patch('apps.api.main.customers',return_value=({},pd.DataFrame(),rows)):
        response=TestClient(app).post('/api/explain',json={'module':'NBO','customer_id':'C2'})
    assert response.status_code==404
