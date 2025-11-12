from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import os

app = FastAPI(title="RGA TaskDesk", version="2.1")

# Simple data models without complex typing
class Task(BaseModel):
    id: str
    title: str
    description: str
    status: str = "pending"

class TaskCreate(BaseModel):
    title: str
    description: str

# In-memory storage
tasks_db = []

@app.get("/")
async def root():
    return {"message": "RGA TaskDesk API is running!", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "RGA TaskDesk"}

@app.get("/app")
async def app_route():
    return {"message": "App route working", "version": "2.1"}

@app.get("/tasks")
async def get_tasks():
    return tasks_db

@app.post("/tasks")
async def create_task(task: TaskCreate):
    task_id = str(uuid.uuid4())
    new_task = Task(
        id=task_id,
        title=task.title,
        description=task.description,
        status="pending"
    )
    tasks_db.append(new_task)
    return new_task

# Add sample task on startup
@app.on_event("startup")
async def startup_event():
    if not tasks_db:
        sample_task = Task(
            id=str(uuid.uuid4()),
            title="Welcome to RGA TaskDesk",
            description="Get started by creating new tasks!",
            status="pending"
        )
        tasks_db.append(sample_task)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
