from datetime import datetime, date
from typing import Optional, List
import os
import csv
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, select, create_engine

# ===== DATABASE SETUP =====
DB_DIR = "/data"
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "taskdesk_cloud.db")

# DON'T DELETE EXISTING DATABASE - PRESERVE YOUR DATA!
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# ===== DATA MODELS =====
class Staff(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = ""
    legal_name: str = ""
    particular: str
    alloted_to: str
    status: str = "OPEN"
    remarks: str = ""
    billing_done: bool = False
    last_follow_up: Optional[date] = None
    deadline: Optional[date] = None
    deadline_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ===== FASTAPI APP =====
app = FastAPI(
    title="RGA TaskDesk",
    description="Professional Task Management for RGA",
    version="2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== DEFAULT DATA =====
DEFAULT_STAFF = ["Anil Mandal", "Rutik B.", "Pooja G.", "Pranita N."]
DEFAULT_CATEGORIES = [
    "Director Change", "Shop Act New", "MSME Update", "IEC Certificate New",
    "MSME New", "IEC Certificate Update", "Name Run", "Incorporation",
    "GST Registration", "Company Closure", "DSC Application"
]

# Create tables only if they don't exist - PRESERVE DATA
SQLModel.metadata.create_all(engine)

# Only add default data if tables are empty
with Session(engine) as session:
    if not session.exec(select(Staff)).first():
        for name in DEFAULT_STAFF:
            session.add(Staff(name=name))
        session.commit()
    
    if not session.exec(select(Category)).first():
        for category_name in DEFAULT_CATEGORIES:
            session.add(Category(name=category_name))
        session.commit()

# ===== API SCHEMAS =====
class StaffIn(BaseModel):
    name: str
    phone: Optional[str] = None

class StaffOut(StaffIn):
    id: int
    created_at: datetime

class CategoryIn(BaseModel):
    name: str

class CategoryOut(CategoryIn):
    id: int
    created_at: datetime

class TaskIn(BaseModel):
    client_name: str = ""
    legal_name: str = ""
    particular: str
    alloted_to: str
    status: str = "OPEN"
    remarks: str = ""
    billing_done: bool = False
    last_follow_up: Optional[date] = None
    deadline: Optional[date] = None

class TaskOut(TaskIn):
    id: int
    deadline_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

def tasks_to_csv(tasks):
    """Convert tasks to CSV using built-in csv module (NO PANDAS)"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Client Name', 'Legal Name', 'Particular', 'Assigned To',
        'Status', 'Remarks', 'Billing Done', 'Last Follow Up', 'Deadline',
        'Deadline Reason', 'Created At', 'Updated At'
    ])
    
    # Write data
    for task in tasks:
        writer.writerow([
            task.id,
            task.client_name,
            task.legal_name,
            task.particular,
            task.alloted_to,
            task.status,
            task.remarks,
            'Yes' if task.billing_done else 'No',
            task.last_follow_up,
            task.deadline,
            task.deadline_reason,
            task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            task.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return output.getvalue()

# ===== API ROUTES =====
@app.get("/")
def root():
    return {"status": "running", "app": "RGA TaskDesk", "version": "2.1"}

@app.get("/staff", response_model=List[StaffOut])
def get_staff():
    with Session(engine) as session:
        return session.exec(select(Staff).order_by(Staff.name)).all()

@app.post("/staff", response_model=StaffOut)
def create_staff(staff: StaffIn):
    with Session(engine) as session:
        existing = session.exec(select(Staff).where(Staff.name == staff.name)).first()
        if existing:
            raise HTTPException(400, "Staff member already exists")
        
        new_staff = Staff(**staff.dict())
        session.add(new_staff)
        session.commit()
        session.refresh(new_staff)
        return new_staff

@app.delete("/staff/{staff_id}")
def delete_staff(staff_id: int):
    with Session(engine) as session:
        staff = session.get(Staff, staff_id)
        if not staff:
            raise HTTPException(404, "Staff not found")
        
        session.delete(staff)
        session.commit()
        return {"message": "Staff deleted successfully"}

@app.get("/categories", response_model=List[CategoryOut])
def get_categories():
    with Session(engine) as session:
        return session.exec(select(Category).order_by(Category.name)).all()

@app.post("/categories", response_model=CategoryOut)
def create_category(category: CategoryIn):
    with Session(engine) as session:
        existing = session.exec(select(Category).where(Category.name == category.name)).first()
        if existing:
            raise HTTPException(400, "Category already exists")
        
        new_category = Category(**category.dict())
        session.add(new_category)
        session.commit()
        session.refresh(new_category)
        return new_category

@app.delete("/categories/{category_id}")
def delete_category(category_id: int):
    with Session(engine) as session:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(404, "Category not found")
        
        session.delete(category)
        session.commit()
        return {"message": "Category deleted successfully"}

@app.get("/tasks", response_model=List[TaskOut])
def get_tasks(status: Optional[str] = None, staff: Optional[str] = None, search: Optional[str] = None):
    with Session(engine) as session:
        query = select(Task)
        
        if status and status != "ALL":
            query = query.where(Task.status == status)
        
        if staff and staff != "ALL":
            query = query.where(Task.alloted_to == staff)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Task.client_name.ilike(search_term)) |
                (Task.legal_name.ilike(search_term)) |
                (Task.particular.ilike(search_term)) |
                (Task.remarks.ilike(search_term))
            )
        
        tasks = session.exec(query.order_by(Task.updated_at.desc())).all()
        return tasks

@app.post("/tasks", response_model=TaskOut)
def create_task(task: TaskIn):
    with Session(engine) as session:
        new_task = Task(**task.dict())
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return new_task

@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskIn):
    with Session(engine) as session:
        existing_task = session.get(Task, task_id)
        if not existing_task:
            raise HTTPException(404, "Task not found")
        
        if (existing_task.deadline and task.deadline and 
            existing_task.deadline != task.deadline and 
            existing_task.deadline < date.today()):
            raise HTTPException(400, "Please provide reason for missed deadline before setting new deadline")
        
        for field, value in task.dict().items():
            setattr(existing_task, field, value)
        
        existing_task.updated_at = datetime.utcnow()
        session.add(existing_task)
        session.commit()
        session.refresh(existing_task)
        return existing_task

@app.put("/tasks/{task_id}/deadline")
def update_task_deadline(task_id: int, deadline: date, reason: Optional[str] = None):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(404, "Task not found")
        
        if task.deadline and task.deadline < date.today() and deadline > task.deadline:
            if not reason:
                raise HTTPException(400, "Reason required for extending missed deadline")
            task.deadline_reason = reason
        
        task.deadline = deadline
        task.updated_at = datetime.utcnow()
        session.add(task)
        session.commit()
        
        return {"message": "Deadline updated successfully"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(404, "Task not found")
        
        session.delete(task)
        session.commit()
        return {"message": "Task deleted successfully"}

@app.get("/export/tasks")
def export_tasks_to_csv():
    with Session(engine) as session:
        tasks = session.exec(select(Task)).all()
        
        csv_content = tasks_to_csv(tasks)
        
        filename = f"RGA_Tasks_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

# ===== WEB INTERFACE =====
@app.get("/app")
def web_interface():
    # [KEEP YOUR EXISTING HTML CODE EXACTLY AS IS - NO CHANGES NEEDED]
    # Your complete HTML interface code goes here (unchanged)
    html_content = """
    <!DOCTYPE html>
    <html>
    <!-- YOUR EXACT EXISTING HTML CODE -->
    </html>
    """
    return HTMLResponse(content=html_content)

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
