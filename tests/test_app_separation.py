"""Entry points remain usable and independent even without a connection."""
from pathlib import Path
import os
import subprocess
import sys
import shutil
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest
from shared.snowflake_service import read
from shared.ui import compact_amount

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('entry,options,ai',[
    ('apps/ai-intelligence/app.py',['Executive Intelligence','Next Best Action','Next Best Offer'],True),
    ('apps/data-service-desk/app.py',['Business User Portal','Data Team Workspace'],False),
])
def test_separate_navigation_and_connection_failure(entry,options,ai):
    read.clear()
    with patch('shared.snowflake_service.get_service',side_effect=RuntimeError('offline')):
        app=AppTest.from_file(str(ROOT/entry),default_timeout=15).run()
    assert not app.exception
    assert app.sidebar.radio[0].options == options
    assert bool(app.toggle) == ai
    assert app.error and not app.metric
    assert 'No sample figures' in app.error[0].value


@pytest.mark.parametrize('value,expected',[(18926262.09,'RM 18.93M'),(9410000,'RM 9.41M'),
                                         (850000,'RM 850K'),(-850000,'RM -850K'),(None,'Unavailable')])
def test_money_display_keeps_large_kpis_compact(value,expected):
    assert compact_amount(value)==expected


@pytest.mark.parametrize('folder',['ai-intelligence','data-service-desk'])
def test_entry_point_imports_from_its_own_directory(folder):
    # Isolated Python excludes the repo from sys.path. No connection is supplied;
    # the app must still import shared helpers and handle its offline state.
    env={k:v for k,v in os.environ.items() if not k.startswith('TUNE_SNOWFLAKE_')}
    result=subprocess.run([sys.executable,'-I','-c',
        "import runpy; runpy.run_path('app.py',run_name='__main__')"],
        cwd=ROOT/'apps'/folder,env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('folder',['ai-intelligence','data-service-desk'])
def test_entry_point_imports_in_a_standalone_deployment_bundle(folder,tmp_path):
    # The hosted shape has shared/ beside app.py, without access to the repo.
    shutil.copy2(ROOT/'apps'/folder/'app.py',tmp_path/'app.py')
    shutil.copytree(ROOT/'shared',tmp_path/'shared',ignore=shutil.ignore_patterns('__pycache__'))
    env={k:v for k,v in os.environ.items() if not k.startswith('TUNE_SNOWFLAKE_')}
    result=subprocess.run([sys.executable,'-I','-c',
        "from pathlib import Path; from streamlit.testing.v1 import AppTest; "
        "a=AppTest.from_file(str(Path('app.py').resolve()),default_timeout=20).run(); "
        "assert not a.exception, a.exception; assert a.error"],
        cwd=tmp_path,env=env,capture_output=True,text=True,timeout=40)
    assert result.returncode==0,result.stderr
