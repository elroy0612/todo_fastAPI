from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from todo.core.deps import db_dep
from .service import TodoService
from .schemas import TodoCreate, TodoOut

router = APIRouter(prefix="/api", tags=["todo"])

def get_service(session: AsyncSession = Depends(db_dep)) -> TodoService:
    return TodoService(session)

@router.post("/todo", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(body: TodoCreate, service: TodoService = Depends(get_service)):
    item = await service.create(text=body.text)
    return item
