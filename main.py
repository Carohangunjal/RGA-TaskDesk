from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import os

# Initialize FastAPI app
app = FastAPI(
    title="RGA TaskDesk API",
    description="Task Management System for RGA",
    version="2.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class Task(BaseModel):
    id: str
    title: str
    description: str
    status: str = "pending"
    priority: str = "medium"
    assignee: str = ""
    created_at: str
    updated_at: str

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    assignee: str = ""

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None

# In-memory storage (replace with database in production)
tasks_db = []

# Utility functions
def get_current_time():
    return datetime.now().isoformat()

def find_task(task_id: str):
    for task in tasks_db:
        if task.id == task_id:
            return task
    return None

# Routes
@app.get("/")
async def root():
    return {
        "message": "RGA TaskDesk API is running!",
        "status": "active", 
        "version": "2.1",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "tasks": "/tasks",
            "app": "/app"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "RGA TaskDesk",
        "timestamp": get_current_time(),
        "environment": os.getenv("RENDER", "development")
    }

@app.get("/app")
async def app_dashboard():
    return {
        "message": "RGA TaskDesk Application Dashboard",
        "version": "2.1",
        "available_features": [
            "Task Management",
            "User Assignment", 
            "Priority Tracking",
            "Status Updates"
        ]
    }

# Task Management Routes
@app.get("/tasks", response_model=List[Task])
async def get_all_tasks():
    """Get all tasks"""
    return tasks_db

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a specific task by ID"""
    task = find_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    task_id = str(uuid.uuid4())
    current_time = get_current_time()
    
    new_task = Task(
        id=task_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        assignee=task_data.assignee,
        created_at=current_time,
        updated_at=current_time
    )
    
    tasks_db.append(new_task)
    return new_task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_data: TaskUpdate):
    """Update an existing task"""
    task = find_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields if provided
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.assignee is not None:
        task.assignee = task_data.assignee
    
    task.updated_at = get_current_time()
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    task = find_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tasks_db.remove(task)
    return {"message": "Task deleted successfully"}

# Statistics endpoint
@app.get("/stats")
async def get_stats():
    """Get task statistics"""
    total_tasks = len(tasks_db)
    pending = len([t for t in tasks_db if t.status == "pending"])
    in_progress = len([t for t in tasks_db if t.status == "in_progress"])
    completed = len([t for t in tasks_db if t.status == "completed"])
    
    return {
        "total_tasks": total_tasks,
        "by_status": {
            "pending": pending,
            "in_progress": in_progress, 
            "completed": completed
        },
        "by_priority": {
            "high": len([t for t in tasks_db if t.priority == "high"]),
            "medium": len([t for t in tasks_db if t.priority == "medium"]),
            "low": len([t for t in tasks_db if t.priority == "low"])
        }
    }

# Add some sample data
@app.on_event("startup")
async def startup_event():
    """Add sample tasks on startup"""
    if not tasks_db:
        sample_tasks = [
            {
                "id": str(uuid.uuid4()),
                "title": "Welcome to RGA TaskDesk",
                "description": "This is your first task. Edit or delete it to get started!",
                "status": "pending",
                "priority": "high",
                "assignee": "Admin",
                "created_at": get_current_time(),
                "updated_at": get_current_time()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Set up project structure",
                "description": "Organize the project folders and files",
                "status": "in_progress",
                "priority": "medium",
                "assignee": "Team Lead",
                "created_at": get_current_time(),
                "updated_at": get_current_time()
            }
        ]
        
        for task_data in sample_tasks:
            task = Task(**task_data)
            tasks_db.append(task)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
