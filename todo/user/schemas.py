from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TodoCreate(BaseModel):
    text: str = Field(min_length=1, max_length=255)
    
class TodoOut(BaseModel):
    id: int
    text: str
    done: bool
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)