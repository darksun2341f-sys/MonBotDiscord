import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

from web.app import app
from web.db import set_database_url, reset_engine, get_engine, init_db
from web.modules import list_modules, get_module
from sqlalchemy import text
import asyncio

print('app import success')
print('modules', [m.name for m in list_modules()])
print('welcome module', get_module('welcome'))

tmp = Path('tmp_pytest.db').resolve()
set_database_url(f'sqlite+aiosqlite:///{tmp}')
reset_engine()
print('DATABASE_URL', __import__('web.db', fromlist=['']).DATABASE_URL)

async def main():
    await init_db()
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        rows = result.fetchall()
        print('result.fetchall() type', type(rows), rows)
        tables = [row[0] for row in rows]
        print('tables', tables)
        print('has welcomeconfig', any('welcomeconfig' in name.lower() for name in tables))

asyncio.run(main())
