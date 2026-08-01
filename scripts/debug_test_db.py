import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from web.db import set_database_url, reset_engine, get_engine, init_db
from sqlalchemy import text

set_database_url(f"sqlite+aiosqlite:///{Path('tmp_test.db').resolve()}")
reset_engine()

async def main():
    await init_db()
    engine = get_engine()
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        print('tables row list:', tables)
        print('has welcomeconfig:', any('welcomeconfig' in name.lower() for name in tables))

asyncio.run(main())
