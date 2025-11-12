import streamlit as st
import json
import datetime
from datetime import timedelta
import io
import base64
from auth import authenticate

# Page configuration
st.set_page_config(
    page_title="RGA Task Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
def inject_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        .task-item {
            background-color: #f0f2f6;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .task-item.overdue {
            border-left-color: #ff4b4b;
            background-color: #ffe6e6;
        }
        .task-item.due-soon {
            border-left-color: #ffa500;
            background-color: #fff2e6;
        }
        .task-text {
            font-weight: bold;
            font-size: 1.1rem;
        }
        .task-deadline {
            color: #666;
            font-size: 0.9rem;
        }
        .completed-task {
            text-decoration: line-through;
            opacity: 0.7;
        }
        .stats-container {
            background-color: #e8f4fd;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .scrollable-container {
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #e6e6e6;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 20px;
        }
        @media (max-width: 768px) {
            .scrollable-container {
                max-height: 400px;
            }
        }
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background: white;
        }
        .stButton button {
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

class TaskManager:
    def __init__(self):
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from session state or initialize"""
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
    
    def save_tasks(self):
        """Save tasks to session state"""
        pass
    
    def add_task(self, particular, deadline=None, client_name="", legal_name="", assigned_to="", remarks=""):
        """Add a new task"""
        task = {
            'ID': len(st.session_state.tasks) + 1,
            'Client Name': client_name,
            'Legal Name': legal_name,
            'Particular': particular,
            'Assigned To': assigned_to,
            'Status': 'OPEN',
            'Remarks': remarks,
            'Billing Done': 'No',
            'Last Follow Up': datetime.datetime.now().strftime('%d/%m/%Y'),
            'Deadline': deadline.strftime('%d/%m/%Y') if deadline else '',
            'Deadline Reason': '',
            'Created At': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
            'Updated At': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
            'Completed': False
        }
        st.session_state.tasks.append(task)
        self.save_tasks()
        self.schedule_reminders(task)
    
    def schedule_reminders(self, task):
        """Schedule reminders for task deadline"""
        if task['Deadline']:
            try:
                deadline_date = datetime.datetime.strptime(task['Deadline'], '%d/%m/%Y')
                
                # Calculate reminder dates
                one_week_before = deadline_date - timedelta(days=7)
                one_day_before = deadline_date - timedelta(days=1)
                
                # Store reminder dates
                task['reminders'] = {
                    'one_week_before': one_week_before.strftime('%d/%m/%Y'),
                    'one_day_before': one_day_before.strftime('%d/%m/%Y'),
                    'deadline_day': deadline_date.strftime('%d/%m/%Y')
                }
            except ValueError:
                pass
    
    def check_reminders(self):
        """Check and display due reminders"""
        today = datetime.datetime.now().date()
        reminders = []
        
        for task in st.session_state.tasks:
            if 'reminders' in task and task['reminders']:
                for reminder_type, reminder_date in task['reminders'].items():
                    try:
                        reminder_dt = datetime.datetime.strptime(reminder_date, '%d/%m/%Y').date()
                        if reminder_dt == today:
                            reminders.append({
                                'task': task['Particular'],
                                'type': reminder_type.replace('_', ' ').title(),
                                'date': reminder_date
                            })
                    except ValueError:
                        continue
        
        return reminders
    
    def edit_task(self, task_id, new_particular):
        """Edit task particulars"""
        for task in st.session_state.tasks:
            if task['ID'] == task_id:
                task['Particular'] = new_particular
                task['Updated At'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
                break
        self.save_tasks()
    
    def toggle_complete(self, task_id):
        """Toggle task completion status"""
        for task in st.session_state.tasks:
            if task['ID'] == task_id:
                task['Completed'] = not task['Completed']
                task['Status'] = 'COMPLETED' if task['Completed'] else 'OPEN'
                task['Updated At'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
                break
        self.save_tasks()
    
    def delete_task(self, task_id):
        """Delete a task"""
        st.session_state.tasks = [task for task in st.session_state.tasks if task['ID'] != task_id]
        self.save_tasks()
    
    def export_to_csv(self):
        """Export tasks to CSV format"""
        if not st.session_state.tasks:
            return None
        
        df = pd.DataFrame(st.session_state.tasks)
        
        # Define column order to match your format
        columns_order = ['ID', 'Client Name', 'Legal Name', 'Particular', 'Assigned To', 
                        'Status', 'Remarks', 'Billing Done', 'Last Follow Up', 
                        'Deadline', 'Deadline Reason', 'Created At', 'Updated At']
        
        # Ensure all columns are present
        for col in columns_order:
            if col not in df.columns:
                df[col] = ''
        
        # Reorder columns
        df = df[columns_order]
        return df
    
    def import_from_csv(self, csv_file):
        """Import tasks from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            
            # Ensure all required columns exist
            required_columns = ['ID', 'Client Name', 'Legal Name', 'Particular', 'Assigned To', 
                              'Status', 'Remarks', 'Billing Done', 'Last Follow Up', 
                              'Deadline', 'Deadline Reason', 'Created At', 'Updated At']
            
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            # Add completion status
            df['Completed'] = df['Status'] == 'COMPLETED'
            
            # Convert to list of dictionaries
            imported_tasks = df.to_dict('records')
            
            # Merge with existing tasks (don't replace)
            existing_ids = {task['ID'] for task in st.session_state.tasks}
            max_id = max(existing_ids) if existing_ids else 0
            
            imported_count = 0
            for task in imported_tasks:
                if task['ID'] not in existing_ids:
                    st.session_state.tasks.append(task)
                    imported_count += 1
                else:
                    max_id += 1
                    task['ID'] = max_id
                    st.session_state.tasks.append(task)
                    imported_count += 1
            
            self.save_tasks()
            return True, f"Successfully imported {imported_count} tasks"
            
        except Exception as e:
            return False, f"Error importing CSV: {str(e)}"

def main_app():
    """Main application after login"""
    task_manager = TaskManager()
    inject_css()
    st.markdown('<div class="main-header">📝 RGA Task Manager</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("📊 Data Management")
        st.subheader("Export Tasks")
        if st.button("📥 Export to CSV"):
            df = task_manager.export_to_csv()
            if df is not None:
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                filename = f"RGA_Tasks_Export_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
                href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.warning("No tasks to export")
        
        st.subheader("Import Tasks")
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'], key="csv_uploader")
        if uploaded_file is not None:
            if st.button("📤 Import from CSV"):
                success, message = task_manager.import_from_csv(uploaded_file)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        reminders = task_manager.check_reminders()
        if reminders:
            st.header("🔔 Reminders")
            for reminder in reminders:
                st.warning(f"**{reminder['type']}**: {reminder['task']} - {reminder['date']}")
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header("Add New Task")
        with st.form("task_form", clear_on_submit=True):
            particular = st.text_input("Task Particulars*", placeholder="Enter task details...")
            c1, c2 = st.columns(2)
            with c1:
                deadline = st.date_input("Deadline", min_value=datetime.date.today())
            with c2:
                assigned_to = st.text_input("Assigned To", placeholder="Person responsible")
            client_name = st.text_input("Client Name", placeholder="Client name")
            legal_name = st.text_input("Legal Name", placeholder="Legal entity name")
            remarks = st.text_area("Remarks", placeholder="Additional notes...")
            submitted = st.form_submit_button("➕ Add Task")
            if submitted:
                if particular.strip():
                    task_manager.add_task(
                        particular=particular.strip(),
                        deadline=deadline,
                        client_name=client_name,
                        legal_name=legal_name,
                        assigned_to=assigned_to,
                        remarks=remarks
                    )
                    st.success("✅ Task added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Please enter task particulars!")
    with col2:
        st.header("📈 Statistics")
        total_tasks = len(st.session_state.tasks)
        completed_tasks = sum(1 for task in st.session_state.tasks if task['Completed'])
        pending_tasks = total_tasks - completed_tasks
        st.markdown(f"""
        <div class="stats-container">
            <h4>📋 Total Tasks: {total_tasks}</h4>
            <h4>✅ Completed: {completed_tasks}</h4>
            <h4>⏳ Pending: {pending_tasks}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    st.header("📋 Task List")
    st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
    if not st.session_state.tasks:
        st.info("ℹ️ No tasks yet. Add your first task above!")
    else:
        for task in st.session_state.tasks:
            task_class = "task-item"
            if task['Completed']:
                task_class += " completed-task"
            elif task['Deadline']:
                try:
                    deadline_date = datetime.datetime.strptime(task['Deadline'], '%d/%m/%Y').date()
                    days_until_deadline = (deadline_date - datetime.date.today()).days
                    if days_until_deadline < 0:
                        task_class += " overdue"
                    elif days_until_deadline <= 3:
                        task_class += " due-soon"
                except ValueError:
                    pass
            colA, colB = st.columns([3, 1])
            with colA:
                st.markdown(f"""
                <div class="{task_class}">
                    <div class="task-text">{task['Particular']}</div>
                    <div class="task-deadline">
                        📅 <strong>Deadline:</strong> {task['Deadline'] if task['Deadline'] else 'Not set'} | 
                        👤 <strong>Assigned:</strong> {task['Assigned To'] if task['Assigned To'] else 'Not assigned'} |
                        💬 <strong>Remarks:</strong> {task['Remarks'] if task['Remarks'] else 'None'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with colB:
                cE, cC, cD = st.columns(3)
                with cE:
                    if st.button("✏️", key=f"edit_{task['ID']}"):
                        st.session_state[f'edit_{task["ID"]}'] = True
                with cC:
                    status_text = "✅" if task['Completed'] else "⚪"
                    if st.button(status_text, key=f"complete_{task['ID']}"):
                        task_manager.toggle_complete(task['ID'])
                        st.rerun()
                with cD:
                    if st.button("🗑️", key=f"delete_{task['ID']}"):
                        task_manager.delete_task(task['ID'])
                        st.rerun()
            if st.session_state.get(f'edit_{task["ID"]}', False):
                with st.form(key=f"edit_form_{task['ID']}"):
                    new_particular = st.text_input("Edit Task", value=task['Particular'], key=f"edit_input_{task['ID']}")
                    cS, cX = st.columns(2)
                    with cS:
                        if st.form_submit_button("💾 Save"):
                            if new_particular.strip():
                                task_manager.edit_task(task['ID'], new_particular.strip())
                                st.session_state[f'edit_{task["ID"]}'] = False
                                st.rerun()
                            else:
                                st.error("❌ Task particulars cannot be empty!")
                    with cX:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state[f'edit_{task["ID"]}'] = False
                            st.rerun()
            st.markdown("---")
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main function with authentication"""
    if not authenticate():
        st.stop()
    main_app()

if __name__ == "__main__":
    main()
