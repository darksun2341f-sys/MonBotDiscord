import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

from web.db import set_database_url, reset_engine, get_engine, init_db
from sqlalchemy import text
import asyncio

set_database_url(f"sqlite+aiosqlite:///{Path('tmp_async_fetchall.db').resolve()}")
reset_engine()

async def main():
    await init_db()
    engine = get_engine()
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        print('result type', type(result))
        print('result keys', result.keys())
        rows = result.fetchall()
        print('fetchall rows', rows)
        if hasattr(result, 'all'):
            rows_all = result.all()
            print('all rows', rows_all)
        if hasattr(result, 'scalars'):
            try:
                print('scalars', result.scalars().all())
            except Exception as e:
                print('scalars error', e)

asyncio.run(main())
