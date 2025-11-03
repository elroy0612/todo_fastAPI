from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .repository import TodoRepository
from .models import Todo

class TodoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TodoRepository(session)

    async def create(self, text: str) -> Todo:
        try:
            item = await self.repo.add(text)
            await self.session.commit()
            await self.session.refresh(item)
            return item
        except IntegrityError:
            await self.session.rollback()
            raise

    async def list(self) -> List[TodoOut]:
        rows = await self.repo.list_desc()
        return [TodoOut.model_validate(r) for r in rows]
    
    async def delete(self, ids: list[int]) -> list[int]:
        uniq = list(dict.fromkeys(ids)) # 중복 제거
        try:
            deleted_ids = await self.repo.delete(uniq) # 트랜잭션 안에서 삭제
            await self.session.commit() # db에 반영(확정) = 다른 세션에서도 반영됨
            return deleted_ids # router로 
        except:
            await self.session.rollback() # 전부 취소(원상복구)
            raise