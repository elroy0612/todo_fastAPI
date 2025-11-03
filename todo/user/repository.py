from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .models import Todo

class TodoRepository:
    def __init__(self, session:AsyncSession):
        self.session = session
        
    async def add(self, text: str) -> Todo:
        item = Todo(text=text, done=False)
        self.session.add(item)
        return item

    async def get_by_id(self, todo_id: int) -> Todo | None:
        return await self.session.get(Todo, todo_id)

    async def list_desc(self) -> list[Todo]:
        result = await self.session.execute(select(Todo).order_by(Todo.id.desc()))
        return result.scalars().all()
    
    async def delete(self, ids: list[int]) -> list[int]:
        result = await self.session.execute( # 존재하는 id만 조회
            select(Todo.id).where(Todo.id.in_(ids)) # in_() : 파이썬의 예약어/연산자와 이름이 충돌하는 것을 피하기 위함
        )
        existing_ids = result.scalars().all() # 첫 번째 값 뽑기 
        if not existing_ids:
            return []
        
        await self.session.execute( # 삭제, db에는 아직 반영 X -> service의 commit으로 반영
            delete(Todo).where(Todo.id.in_(existing_ids))
        )
        
        return existing_ids # service로