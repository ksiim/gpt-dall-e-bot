from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import delete
from config import DATABASE_URL, DB_NAME
import os

engine = create_async_engine(DATABASE_URL)
Session = async_sessionmaker(engine)

Base = declarative_base()

async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
            