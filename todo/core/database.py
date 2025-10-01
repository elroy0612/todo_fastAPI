from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import AsyncIterator

class Settings(BaseSettings):
    DB_USER: str = "root"
    DB_PASS: str = "root"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "todo"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

def _build_db_url() -> str:
    s = get_settings()
    return (
        f"mysql+aiomysql://{s.DB_USER}:{s.DB_PASS}"
        f"@{s.DB_HOST}:{s.DB_PORT}/{s.DB_NAME}?charset=utf8mb4"
    )

engine = create_async_engine(
    _build_db_url(),
    pool_pre_ping=True,
    pool_recycle=1800
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session