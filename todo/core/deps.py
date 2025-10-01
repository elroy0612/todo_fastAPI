from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from .database import get_session

def db_dep(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session
