from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from enum import Enum
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import pandas as pd

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app
app = FastAPI(title="HR Onboarding & Exit System")
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    ONBOARDING = "onboarding"
    EXITING = "exiting"
    EXITED = "exited"

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class TaskType(str, Enum):
    ONBOARDING = "onboarding"
    EXIT = "exit"

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole = UserRole.MANAGER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    employee_id: str
    email: EmailStr
    department: str
    manager: str
    start_date: datetime
    exit_date: Optional[datetime] = None
    status: EmployeeStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmployeeCreate(BaseModel):
    name: str
    employee_id: str
    email: EmailStr
    department: str
    manager: str
    start_date: datetime
    status: EmployeeStatus = EmployeeStatus.ONBOARDING

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    manager: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    exit_date: Optional[datetime] = None

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    assigned_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskCreate(BaseModel):
    employee_id: str
    title: str
    description: str
    task_type: TaskType
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

class ChecklistTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    task_type: TaskType
    default_due_days: Optional[int] = None
    is_active: bool = True

# Default checklist templates
DEFAULT_ONBOARDING_TASKS = [
    {"title": "Offer letter shared & signed", "description": "Share and get signed offer letter from new employee", "default_due_days": 1},
    {"title": "Employee details form submitted", "description": "Collect all required personal and professional details", "default_due_days": 3},
    {"title": "Laptop/system allocation", "description": "Allocate laptop and necessary hardware to employee", "default_due_days": 5},
    {"title": "Email & communication tools created", "description": "Create email account and setup communication tools", "default_due_days": 2},
    {"title": "HRMS/project access setup", "description": "Provide access to HRMS and relevant project management tools", "default_due_days": 7},
    {"title": "Welcome kit shared", "description": "Share welcome kit and company swag", "default_due_days": 5},
    {"title": "Induction/training scheduled", "description": "Schedule orientation and initial training sessions", "default_due_days": 7}
]

DEFAULT_EXIT_TASKS = [
    {"title": "Exit interview scheduled & completed", "description": "Conduct exit interview to gather feedback", "default_due_days": 7},
    {"title": "Knowledge transfer session", "description": "Complete knowledge transfer to replacement or team", "default_due_days": 14},
    {"title": "IT assets returned", "description": "Collect all company laptops, devices, and accessories", "default_due_days": 3},
    {"title": "Email access disabled", "description": "Disable email and revoke system access", "default_due_days": 1},
    {"title": "HR clearance completed", "description": "Complete HR clearance and documentation", "default_due_days": 5},
    {"title": "Full & Final settlement initiated", "description": "Process final salary and settlements", "default_due_days": 10},
    {"title": "Relieving letter issued", "description": "Issue relieving letter and experience certificate", "default_due_days": 7}
]

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and key.endswith(('_date', '_at')) and 'T' in value:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

async def create_default_tasks_for_employee(employee_id: str, task_type: TaskType, user_email: str):
    """Create default tasks when an employee starts onboarding or exit process"""
    templates = DEFAULT_ONBOARDING_TASKS if task_type == TaskType.ONBOARDING else DEFAULT_EXIT_TASKS
    
    for template in templates:
        due_date = None
        if template.get("default_due_days"):
            due_date = datetime.now(timezone.utc) + timedelta(days=template["default_due_days"])
        
        task = Task(
            employee_id=employee_id,
            title=template["title"],
            description=template["description"],
            task_type=task_type,
            due_date=due_date,
            assigned_by=user_email
        )
        task_dict = prepare_for_mongo(task.dict())
        await db.tasks.insert_one(task_dict)

# Routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role
    )
    
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict = prepare_for_mongo(user_dict)
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user["email"]})
    user_obj = User(**parse_from_mongo(user))
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_obj
    )

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Employee routes
@api_router.post("/employees", response_model=Employee)
async def create_employee(employee_data: EmployeeCreate, current_user: User = Depends(get_current_user)):
    # Check if employee_id already exists
    existing = await db.employees.find_one({"employee_id": employee_data.employee_id})
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    employee = Employee(**employee_data.dict())
    employee_dict = prepare_for_mongo(employee.dict())
    await db.employees.insert_one(employee_dict)
    
    # Create default onboarding tasks if status is onboarding
    if employee.status == EmployeeStatus.ONBOARDING:
        await create_default_tasks_for_employee(employee.id, TaskType.ONBOARDING, current_user.email)
    
    return employee

@api_router.get("/employees", response_model=List[Employee])
async def get_employees(current_user: User = Depends(get_current_user)):
    employees = await db.employees.find().to_list(1000)
    return [Employee(**parse_from_mongo(emp)) for emp in employees]

@api_router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str, current_user: User = Depends(get_current_user)):
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return Employee(**parse_from_mongo(employee))

@api_router.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, update_data: EmployeeUpdate, current_user: User = Depends(get_current_user)):
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc)
    update_dict = prepare_for_mongo(update_dict)
    
    # Create exit tasks if status is changing to exiting
    if update_data.status == EmployeeStatus.EXITING and employee.get("status") != EmployeeStatus.EXITING:
        await create_default_tasks_for_employee(employee_id, TaskType.EXIT, current_user.email)
    
    await db.employees.update_one({"id": employee_id}, {"$set": update_dict})
    
    updated_employee = await db.employees.find_one({"id": employee_id})
    return Employee(**parse_from_mongo(updated_employee))

# Task routes
@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    task = Task(**task_data.dict(), assigned_by=current_user.email)
    task_dict = prepare_for_mongo(task.dict())
    await db.tasks.insert_one(task_dict)
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(employee_id: Optional[str] = None, task_type: Optional[TaskType] = None, current_user: User = Depends(get_current_user)):
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if task_type:
        query["task_type"] = task_type.value
    
    tasks = await db.tasks.find(query).to_list(1000)
    return [Task(**parse_from_mongo(task)) for task in tasks]

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, update_data: TaskUpdate, current_user: User = Depends(get_current_user)):
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Set completed_date if task is being marked as completed
    if update_data.status == TaskStatus.COMPLETED and not update_data.completed_date:
        update_dict["completed_date"] = datetime.now(timezone.utc)
    
    update_dict = prepare_for_mongo(update_dict)
    await db.tasks.update_one({"id": task_id}, {"$set": update_dict})
    
    updated_task = await db.tasks.find_one({"id": task_id})
    return Task(**parse_from_mongo(updated_task))

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    # Get employee counts by status
    employee_stats = {}
    for status in EmployeeStatus:
        count = await db.employees.count_documents({"status": status.value})
        employee_stats[status.value] = count
    
    # Get task stats
    total_tasks = await db.tasks.count_documents({})
    pending_tasks = await db.tasks.count_documents({"status": TaskStatus.PENDING.value})
    completed_tasks = await db.tasks.count_documents({"status": TaskStatus.COMPLETED.value})
    
    # Get overdue tasks
    current_date = datetime.now(timezone.utc)
    overdue_tasks = await db.tasks.count_documents({
        "status": TaskStatus.PENDING.value,
        "due_date": {"$lt": current_date.isoformat()}
    })
    
    # Get upcoming tasks (next 7 days)
    upcoming_date = current_date + timedelta(days=7)
    upcoming_tasks = await db.tasks.count_documents({
        "status": TaskStatus.PENDING.value,
        "due_date": {
            "$gte": current_date.isoformat(),
            "$lte": upcoming_date.isoformat()
        }
    })
    
    return {
        "employee_stats": employee_stats,
        "task_stats": {
            "total": total_tasks,
            "pending": pending_tasks,
            "completed": completed_tasks,
            "overdue": overdue_tasks,
            "upcoming": upcoming_tasks
        }
    }

@api_router.get("/dashboard/recent-activities")
async def get_recent_activities(current_user: User = Depends(get_current_user)):
    # Get recent employees
    recent_employees = await db.employees.find().sort("created_at", -1).limit(5).to_list(5)
    
    # Get recent tasks
    recent_tasks = await db.tasks.find().sort("updated_at", -1).limit(10).to_list(10)
    
    return {
        "recent_employees": [Employee(**parse_from_mongo(emp)) for emp in recent_employees],
        "recent_tasks": [Task(**parse_from_mongo(task)) for task in recent_tasks]
    }

def generate_employee_report_pdf(employees, reports_data):
    """Generate PDF report for employees"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#374151')
    )
    
    # Title
    title = Paragraph("HR Employee Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Report date
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 20))
    
    # Summary Statistics
    elements.append(Paragraph("Employee Summary", heading_style))
    summary_data = [
        ['Status', 'Count'],
        ['Total Employees', str(len(employees))],
        ['Active', str(len([e for e in employees if e.get('status') == 'active']))],
        ['Onboarding', str(len([e for e in employees if e.get('status') == 'onboarding']))],
        ['Exiting', str(len([e for e in employees if e.get('status') == 'exiting']))],
        ['Exited', str(len([e for e in employees if e.get('status') == 'exited']))]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Employee Details
    elements.append(Paragraph("Employee Details", heading_style))
    
    # Employee table headers
    employee_data = [['Name', 'ID', 'Department', 'Status', 'Start Date']]
    
    for emp in employees:
        start_date = emp.get('start_date', '')
        if isinstance(start_date, str) and 'T' in start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            except:
                pass
        
        employee_data.append([
            emp.get('name', ''),
            emp.get('employee_id', ''),
            emp.get('department', ''),
            emp.get('status', '').capitalize(),
            str(start_date)
        ])
    
    employee_table = Table(employee_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch, 1*inch])
    employee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    
    elements.append(employee_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

@api_router.get("/reports/employees")
async def export_employees_report(current_user: User = Depends(get_current_user)):
    """Export employee report as PDF"""
    # Get all employees
    employees = await db.employees.find().to_list(1000)
    
    # Get additional report data
    reports_data = {
        "generated_by": current_user.name,
        "generated_at": datetime.now(timezone.utc)
    }
    
    # Generate PDF
    pdf_buffer = generate_employee_report_pdf(employees, reports_data)
    
    # Return PDF response
    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=employee_report.pdf"}
    )

def generate_tasks_report_pdf(tasks, employees):
    """Generate PDF report for tasks"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#374151')
    )
    
    # Title
    title = Paragraph("HR Tasks Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Report date
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 20))
    
    # Task Summary
    elements.append(Paragraph("Task Summary", heading_style))
    
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    pending_tasks = len([t for t in tasks if t.get('status') == 'pending'])
    onboarding_tasks = len([t for t in tasks if t.get('task_type') == 'onboarding'])
    exit_tasks = len([t for t in tasks if t.get('task_type') == 'exit'])
    
    summary_data = [
        ['Metric', 'Count'],
        ['Total Tasks', str(total_tasks)],
        ['Completed Tasks', str(completed_tasks)],
        ['Pending Tasks', str(pending_tasks)],
        ['Onboarding Tasks', str(onboarding_tasks)],
        ['Exit Tasks', str(exit_tasks)]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Task Details
    elements.append(Paragraph("Task Details", heading_style))
    
    # Create employee lookup
    employee_lookup = {emp.get('id'): emp.get('name', 'Unknown') for emp in employees}
    
    # Task table
    task_data = [['Task', 'Employee', 'Type', 'Status', 'Due Date']]
    
    for task in tasks:
        due_date = task.get('due_date', '')
        if isinstance(due_date, str) and 'T' in due_date:
            try:
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            except:
                pass
        
        employee_name = employee_lookup.get(task.get('employee_id', ''), 'Unknown')
        
        task_data.append([
            task.get('title', '')[:30] + ('...' if len(task.get('title', '')) > 30 else ''),
            employee_name[:20],
            task.get('task_type', '').capitalize(),
            task.get('status', '').capitalize(),
            str(due_date) if due_date else 'N/A'
        ])
    
    task_table = Table(task_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
    task_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8)
    ]))
    
    elements.append(task_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

@api_router.get("/reports/tasks")
async def export_tasks_report(current_user: User = Depends(get_current_user)):
    """Export tasks report as PDF"""
    # Get all tasks and employees
    tasks = await db.tasks.find().to_list(1000)
    employees = await db.employees.find().to_list(1000)
    
    # Generate PDF
    pdf_buffer = generate_tasks_report_pdf(tasks, employees)
    
    # Return PDF response
    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=tasks_report.pdf"}
    )

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()