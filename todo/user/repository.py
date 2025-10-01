from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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