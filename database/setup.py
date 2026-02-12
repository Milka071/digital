from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .models import Base
import os

# For now using SQLite
DB_NAME = os.getenv("DB_NAME", "school_bot.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
