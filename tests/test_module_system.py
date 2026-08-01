import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import SQLModel

from web.app import app
from web.db import init_db, reset_engine, set_database_url, get_engine
from web.modules import list_modules, get_module


@pytest.fixture(autouse=True)
def sqlite_db(tmp_path: Path):
    database_file = tmp_path / 'test.db'
    set_database_url(f'sqlite+aiosqlite:///{database_file}')
    reset_engine()
    yield


@pytest.fixture(autouse=True)
def create_tables(sqlite_db):
    asyncio.run(init_db())
    yield


def test_module_loading():
    modules = list_modules()
    assert any(m.name == 'welcome' for m in modules), 'Welcome module must be registered'
    assert any(m.name == 'staff' for m in modules), 'Staff module must be registered'

    welcome = get_module('welcome')
    assert welcome is not None
    assert welcome.title == 'Welcome'

    staff = get_module('staff')
    assert staff is not None
    assert staff.title == 'Staff'


@pytest.mark.asyncio
async def test_database_models_created():
    engine = get_engine()
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        print('DEBUG TABLES', tables)

    assert any('welcomeconfig' in name.lower() for name in tables)


def test_module_api_routes():
    client = TestClient(app)
    response = client.get('/api/modules')
    assert response.status_code == 200
    assert any(module['name'] == 'welcome' for module in response.json())


def test_generic_module_route_registration():
    client = TestClient(app)
    response = client.get('/api/modules/welcome/guilds/test-guild')
    assert response.status_code in (401, 403)


def test_plugin_api_routes():
    client = TestClient(app)
    response = client.get('/api/plugins')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert any(plugin.get('name') == 'sample-welcome-ext' for plugin in response.json())


def test_module_configuration_error():
    welcome = get_module('welcome')
    assert welcome is not None
    with pytest.raises(AttributeError):
        _ = welcome.non_existent_property
