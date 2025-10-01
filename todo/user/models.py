from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, TIMESTAMP
from todo.core.database import Base
from datetime import datetime
from sqlalchemy.sql import text as sa_text 

class Todo(Base):
    __tablename__ = "todo"
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text:Mapped[str] = mapped_column("task", String(255), nullable=False)
    done:Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=sa_text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    