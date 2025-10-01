from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from todo.user.router import router as todo_router 

app = FastAPI(title="Todo API", version="0.1.0")
app.include_router(todo_router) 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
async def test():
    return {"ok":True}