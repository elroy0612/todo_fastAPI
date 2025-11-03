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

@router.get("/todo", response_model=List[TodoOut])
async def read_todo(service: TodoService = Depends(get_service)):
    items = await service.list()
    return items

@router.delete("/todo", response_model=DeleteResult, status_code=200) 
async def delete_todo(body: TodoDel, service: TodoService = Depends(get_service)):
    deleted = await service.delete(body.ids)
    return {"deleted": deleted, "count": len(deleted)} # client로 보낼 json 응답
    # response_model을 이용해서 dict를 반환해도 FastAPI가 DeleteResult로 검증/직렬화 후 응답 보냄