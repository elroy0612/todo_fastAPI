from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, conlist

class TodoCreate(BaseModel):
    text: str = Field(min_length=1, max_length=255)
    
class TodoOut(BaseModel):
    id: int
    text: str
    done: bool
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)
    
class TodoDel(BaseModel): # client 요청 바디
    ids: conlist(int, min_length=1)
    
class DeleteResult(BaseModel): # server 응답 바디
    deleted: list[int]
    count: int