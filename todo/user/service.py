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