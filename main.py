from datetime import datetime, date
from typing import Optional, List
import os
import csv
import io
import sqlite3
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

# ===== DATABASE SETUP =====
DB_DIR = "/data"
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "taskdesk_cloud.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT DEFAULT '',
            legal_name TEXT DEFAULT '',
            particular TEXT NOT NULL,
            alloted_to TEXT NOT NULL,
            status TEXT DEFAULT 'OPEN',
            remarks TEXT DEFAULT '',
            billing_done BOOLEAN DEFAULT FALSE,
            last_follow_up DATE,
            deadline DATE,
            deadline_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Default data
    cursor.execute("SELECT COUNT(*) FROM staff")
    if cursor.fetchone()[0] == 0:
        default_staff = ["Anil Mandal", "Rutik B.", "Pooja G.", "Pranita N."]
        for name in default_staff:
            cursor.execute("INSERT INTO staff (name) VALUES (?)", (name,))
    
    cursor.execute("SELECT COUNT(*) FROM category")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            "Director Change", "Shop Act New", "MSME Update", "IEC Certificate New",
            "MSME New", "IEC Certificate Update", "Name Run", "Incorporation",
            "GST Registration", "Company Closure", "DSC Application"
        ]
        for category in default_categories:
            cursor.execute("INSERT INTO category (name) VALUES (?)", (category,))
    
    conn.commit()
    conn.close()

init_db()

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

# ===== API ROUTES =====
@app.get("/")
def root():
    return {"status": "running", "app": "RGA TaskDesk", "version": "2.1"}

@app.get("/staff")
def get_staff():
    conn = get_db()
    staff = conn.execute("SELECT * FROM staff ORDER BY name").fetchall()
    conn.close()
    return [dict(row) for row in staff]

@app.post("/staff")
def create_staff(data: dict):
    name = data.get('name')
    phone = data.get('phone')
    
    if not name:
        raise HTTPException(400, "Name is required")
    
    conn = get_db()
    existing = conn.execute("SELECT id FROM staff WHERE name = ?", (name,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Staff member already exists")
    
    cursor = conn.execute(
        "INSERT INTO staff (name, phone) VALUES (?, ?)", 
        (name, phone)
    )
    new_id = cursor.lastrowid
    conn.commit()
    
    new_staff = conn.execute("SELECT * FROM staff WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return dict(new_staff)

@app.delete("/staff/{staff_id}")
def delete_staff(staff_id: int):
    conn = get_db()
    staff = conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
    if not staff:
        conn.close()
        raise HTTPException(404, "Staff not found")
    
    conn.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    conn.commit()
    conn.close()
    return {"message": "Staff deleted successfully"}

@app.get("/categories")
def get_categories():
    conn = get_db()
    categories = conn.execute("SELECT * FROM category ORDER BY name").fetchall()
    conn.close()
    return [dict(row) for row in categories]

@app.post("/categories")
def create_category(data: dict):
    name = data.get('name')
    
    if not name:
        raise HTTPException(400, "Name is required")
    
    conn = get_db()
    existing = conn.execute("SELECT id FROM category WHERE name = ?", (name,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Category already exists")
    
    cursor = conn.execute("INSERT INTO category (name) VALUES (?)", (name,))
    new_id = cursor.lastrowid
    conn.commit()
    
    new_category = conn.execute("SELECT * FROM category WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return dict(new_category)

@app.delete("/categories/{category_id}")
def delete_category(category_id: int):
    conn = get_db()
    category = conn.execute("SELECT * FROM category WHERE id = ?", (category_id,)).fetchone()
    if not category:
        conn.close()
        raise HTTPException(404, "Category not found")
    
    conn.execute("DELETE FROM category WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    return {"message": "Category deleted successfully"}

@app.get("/tasks")
def get_tasks(status: str = None, staff: str = None, search: str = None):
    conn = get_db()
    query = "SELECT * FROM task"
    params = []
    
    if status and status != "ALL":
        query += " WHERE status = ?"
        params.append(status)
    
    if staff and staff != "ALL":
        if "WHERE" in query:
            query += " AND alloted_to = ?"
        else:
            query += " WHERE alloted_to = ?"
        params.append(staff)
    
    if search:
        search_term = f"%{search}%"
        if "WHERE" in query:
            query += " AND (client_name LIKE ? OR legal_name LIKE ? OR particular LIKE ? OR remarks LIKE ?)"
        else:
            query += " WHERE (client_name LIKE ? OR legal_name LIKE ? OR particular LIKE ? OR remarks LIKE ?)"
        params.extend([search_term, search_term, search_term, search_term])
    
    query += " ORDER BY updated_at DESC"
    tasks = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in tasks]

@app.post("/tasks")
def create_task(data: dict):
    required_fields = ['particular', 'alloted_to']
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(400, f"{field} is required")
    
    conn = get_db()
    cursor = conn.execute('''
        INSERT INTO task (
            client_name, legal_name, particular, alloted_to, status, remarks,
            billing_done, last_follow_up, deadline
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('client_name', ''),
        data.get('legal_name', ''),
        data.get('particular'),
        data.get('alloted_to'),
        data.get('status', 'OPEN'),
        data.get('remarks', ''),
        data.get('billing_done', False),
        data.get('last_follow_up'),
        data.get('deadline')
    ))
    new_id = cursor.lastrowid
    conn.commit()
    
    new_task = conn.execute("SELECT * FROM task WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return dict(new_task)

@app.put("/tasks/{task_id}")
def update_task(task_id: int, data: dict):
    conn = get_db()
    task = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")
    
    conn.execute('''
        UPDATE task SET
            client_name = ?, legal_name = ?, particular = ?, alloted_to = ?,
            status = ?, remarks = ?, billing_done = ?, last_follow_up = ?,
            deadline = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        data.get('client_name', ''),
        data.get('legal_name', ''),
        data.get('particular'),
        data.get('alloted_to'),
        data.get('status', 'OPEN'),
        data.get('remarks', ''),
        data.get('billing_done', False),
        data.get('last_follow_up'),
        data.get('deadline'),
        task_id
    ))
    conn.commit()
    
    updated_task = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(updated_task)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")
    
    conn.execute("DELETE FROM task WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"message": "Task deleted successfully"}

@app.put("/tasks/{task_id}/deadline")
def update_task_deadline(task_id: int, deadline: date, reason: str = None):
    conn = get_db()
    task = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")
    
    # Check if extending missed deadline
    if task['deadline'] and task['deadline'] < date.today() and deadline > task['deadline']:
        if not reason:
            conn.close()
            raise HTTPException(400, "Reason required for extending missed deadline")
        deadline_reason = reason
    else:
        deadline_reason = task['deadline_reason']
    
    conn.execute('''
        UPDATE task SET deadline = ?, deadline_reason = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (deadline, deadline_reason, task_id))
    conn.commit()
    conn.close()
    
    return {"message": "Deadline updated successfully"}

@app.get("/export/tasks")
def export_tasks_to_csv():
    conn = get_db()
    tasks = conn.execute("SELECT * FROM task").fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', 'Client Name', 'Legal Name', 'Particular', 'Assigned To',
        'Status', 'Remarks', 'Billing Done', 'Last Follow Up', 'Deadline',
        'Deadline Reason', 'Created At', 'Updated At'
    ])
    
    for task in tasks:
        writer.writerow([
            task['id'],
            task['client_name'],
            task['legal_name'],
            task['particular'],
            task['alloted_to'],
            task['status'],
            task['remarks'],
            'Yes' if task['billing_done'] else 'No',
            task['last_follow_up'],
            task['deadline'],
            task['deadline_reason'],
            task['created_at'],
            task['updated_at']
        ])
    
    csv_content = output.getvalue()
    filename = f"RGA_Tasks_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ===== WEB INTERFACE =====
@app.get("/app")
def web_interface():
    # [PASTE YOUR ENTIRE EXISTING HTML CODE HERE]
    # Your complete HTML interface with all CSS and JavaScript
    html_content = """
    <!DOCTYPE html>
    <html>
    <!-- YOUR COMPLETE HTML CODE GOES HERE -->
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
