from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from web.modules import list_modules, get_module
from web.db import set_database_url, reset_engine, get_engine, init_db
from sqlmodel import SQLModel
import asyncio
from sqlalchemy import text

print('loaded modules:', [m.name for m in list_modules()])
print('welcome module:', get_module('welcome'))
print('metadata tables before init:', list(SQLModel.metadata.tables.keys()))

set_database_url(f'sqlite+aiosqlite:///{Path("tmp_test.db").resolve()}')
reset_engine()
async def main():
    await init_db()
    print('metadata tables after init:', list(SQLModel.metadata.tables.keys()))
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        print('sqlite tables:', [row[0] for row in result.fetchall()])

asyncio.run(main())
