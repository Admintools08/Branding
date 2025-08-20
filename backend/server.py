from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request, BackgroundTasks
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
import tempfile
import shutil
from ai_service import HRAIService
from auth_service import AuthService, UserRole, Permission, UserInvitation, PasswordResetToken, EmailVerification, AuditLog
from email_service import email_service

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
app = FastAPI(title="HR Onboarding & Exit System - Enhanced Security")
api_router = APIRouter(prefix="/api")

# Initialize services
try:
    ai_service = HRAIService()
except Exception as e:
    print(f"Warning: AI service initialization failed: {e}")
    ai_service = None

# Initialize Auth Service
auth_service = AuthService(db, SECRET_KEY, ALGORITHM)

# Security
security = HTTPBearer()

# Enums
class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    ONBOARDING = "onboarding"
    EXITING = "exiting"
    EXITED = "exited"
    INACTIVE = "inactive"

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class TaskType(str, Enum):
    ONBOARDING = "onboarding"
    EXIT = "exit"

# Enhanced Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: UserRole
    email_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole = UserRole.EMPLOYEE

class UserInvite(BaseModel):
    email: EmailStr
    role: UserRole
    message: Optional[str] = None

class AcceptInvitation(BaseModel):
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordReset(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

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
    birthday: Optional[datetime] = None
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
    birthday: Optional[datetime] = None
    status: EmployeeStatus = EmployeeStatus.ONBOARDING

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    employee_id: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    manager: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    start_date: Optional[datetime] = None
    birthday: Optional[datetime] = None
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

class BulkNotification(BaseModel):
    recipient_emails: List[EmailStr]
    subject: str
    message: str

# Default checklist templates (unchanged from original)
DEFAULT_ONBOARDING_TASKS = [
    # Pre-Onboarding (Before Day 1)
    {"title": "Offer letter shared & signed", "description": "Share and get signed offer letter from new employee", "default_due_days": 1},
    {"title": "Appointment/contract letter shared", "description": "Share formal appointment/contract letter", "default_due_days": 1},
    {"title": "Employee details form collected", "description": "Collect personal info, emergency contacts, bank details, etc.", "default_due_days": 3},
    {"title": "Background verification initiated/completed", "description": "Complete background verification process", "default_due_days": 5},
    {"title": "System/laptop allocation prepared", "description": "Prepare and allocate laptop and necessary hardware", "default_due_days": 5},
    {"title": "Official email ID created", "description": "Create email account for new employee", "default_due_days": 2},
    {"title": "Communication tools access created", "description": "Setup Slack/Teams/WhatsApp access", "default_due_days": 2},
    {"title": "HRMS/Payroll/Project tools access created", "description": "Provide access to HRMS and project management tools", "default_due_days": 7},
    {"title": "Drive folders, knowledge base access created", "description": "Setup access to shared drives and knowledge base", "default_due_days": 3},
    {"title": "Welcome kit prepared", "description": "Prepare welcome kit and company swag", "default_due_days": 5},
    
    # Day 1
    {"title": "Welcome & orientation session", "description": "Conduct welcome and orientation session", "default_due_days": 1},
    {"title": "Company vision, mission, and values explained", "description": "Share company culture and values", "default_due_days": 1},
    {"title": "HR policies & code of conduct shared", "description": "Share HR policies and code of conduct", "default_due_days": 1},
    {"title": "IT setup completed", "description": "Complete system login, email, tools access testing", "default_due_days": 1},
    {"title": "Introduction to reporting manager & team", "description": "Facilitate introduction to manager and team members", "default_due_days": 1},
    {"title": "Role overview given by manager", "description": "Manager provides detailed role overview", "default_due_days": 1},
    {"title": "Buddy/mentor assigned", "description": "Assign buddy or mentor for initial support", "default_due_days": 1},
    
    # First Week
    {"title": "Departmental introduction sessions", "description": "Introduce to various departments", "default_due_days": 7},
    {"title": "Training on core tools/software", "description": "Provide training on essential tools and software", "default_due_days": 7},
    {"title": "Initial goal-setting with manager", "description": "Set initial goals and expectations with manager", "default_due_days": 7},
    {"title": "Introduction to ongoing projects", "description": "Introduce to current projects and initiatives", "default_due_days": 7},
    {"title": "Compliance training", "description": "Complete data security, workplace safety, compliance training", "default_due_days": 7},
    
    # First Month
    {"title": "30-60-90 day goal review meeting", "description": "Conduct initial goal review and planning meeting", "default_due_days": 30},
    {"title": "Regular manager check-ins scheduled", "description": "Setup regular check-in meetings with manager", "default_due_days": 30},
    {"title": "Feedback session with HR", "description": "HR feedback session on settling in, challenges, improvements", "default_due_days": 30}
]

DEFAULT_EXIT_TASKS = [
    # Resignation/Separation Initiation
    {"title": "Resignation letter received", "description": "Receive and acknowledge resignation letter", "default_due_days": 1},
    {"title": "HR acknowledgement sent", "description": "Send HR acknowledgement of resignation", "default_due_days": 1},
    {"title": "Exit interview scheduled", "description": "Schedule exit interview with HR", "default_due_days": 3},
    {"title": "Manager notified", "description": "Notify reporting manager of resignation", "default_due_days": 1},
    {"title": "Knowledge transfer plan created", "description": "Create comprehensive knowledge transfer plan", "default_due_days": 5},
    
    # During Notice Period
    {"title": "Handover of tasks & responsibilities completed", "description": "Complete handover of all tasks and responsibilities", "default_due_days": 14},
    {"title": "Documentation updated & shared", "description": "Update and share all relevant documentation", "default_due_days": 10},
    {"title": "Client/project communications transitioned", "description": "Transition all client and project communications", "default_due_days": 10},
    {"title": "Final feedback/exit survey filled", "description": "Complete final feedback and exit survey", "default_due_days": 7},
    {"title": "No-dues clearance process initiated", "description": "Initiate no-dues clearance from all departments", "default_due_days": 7},
    
    # Last Working Day
    {"title": "Company laptop, ID card, SIM, and assets returned", "description": "Collect all company assets and equipment", "default_due_days": 1},
    {"title": "Access revoked", "description": "Disable email, tools, HRMS, drive, CRM access", "default_due_days": 1},
    {"title": "Final payroll calculation initiated", "description": "Process leave encashment, gratuity, F&F calculation", "default_due_days": 1},
    {"title": "HR conducts final exit interview", "description": "Conduct final exit interview session", "default_due_days": 1},
    {"title": "Farewell/team communication sent", "description": "Send farewell communication to team", "default_due_days": 1},
    
    # Post Exit
    {"title": "Relieving letter issued", "description": "Issue relieving letter to departing employee", "default_due_days": 7},
    {"title": "Experience/service certificate shared", "description": "Share experience and service certificate", "default_due_days": 7},
    {"title": "Final settlement processed", "description": "Process final salary settlement and payments", "default_due_days": 10}
]

# Helper functions
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

async def get_client_info(request: Request):
    """Extract client info for audit logging"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", None)
    }

# ============================================================================
# AUTHENTICATION & USER MANAGEMENT ROUTES
# ============================================================================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate, request: Request):
    """Register new user (Super Admin only for security)"""
    # For the first user, allow self-registration
    user_count = await db.users.count_documents({})
    if user_count > 0:
        raise HTTPException(status_code=403, detail="Registration disabled. Use invitation system.")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create first user as Super Admin
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=UserRole.SUPER_ADMIN,
        email_verified=True  # First user is auto-verified
    )
    
    user_dict = user.dict()
    user_dict["password"] = auth_service.hash_password(user_data.password)
    user_dict = prepare_for_mongo(user_dict)
    
    await db.users.insert_one(user_dict)
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=user.id,
        action="register",
        resource="user",
        details={"email": user_data.email, "role": user.role},
        **client_info
    )
    
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin, request: Request):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not auth_service.verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    access_token = auth_service.generate_token({"sub": user["email"]})
    user_obj = User(**parse_from_mongo(user))
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=user["id"],
        action="login",
        resource="auth",
        details={"email": login_data.email, "success": True},
        **client_info
    )
    
    # Send security notification
    try:
        await email_service.send_security_notification(
            recipient_email=user["email"],
            user_name=user["name"],
            event_type="login",
            event_details={
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": client_info.get("ip_address", "Unknown"),
                "user_agent": client_info.get("user_agent", "Unknown")[:50]
            }
        )
    except Exception as e:
        print(f"Failed to send login notification: {e}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_obj
    )

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(auth_service.get_current_user)):
    return User(**parse_from_mongo(current_user))

@api_router.post("/auth/invite-user", response_model=UserInvitation)
async def invite_user(
    invite_data: UserInvite,
    current_user: dict = Depends(auth_service.require_permission(Permission.INVITE_USER)),
    request: Request = None
):
    """Invite new user (Admin/HR Manager only)"""
    invitation = await auth_service.create_user_invitation(
        email=invite_data.email,
        role=invite_data.role,
        invited_by=current_user["id"]
    )
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="invite_user",
        resource="user",
        details={"invited_email": invite_data.email, "role": invite_data.role},
        **client_info
    )
    
    return invitation

@api_router.post("/auth/accept-invite", response_model=Token)
async def accept_invitation(token: str, user_data: AcceptInvitation, request: Request):
    """Accept user invitation and create account"""
    result = await auth_service.accept_invitation(token, user_data.dict())
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=result["user"]["id"],
        action="accept_invitation",
        resource="user",
        details={"email": result["user"]["email"]},
        **client_info
    )
    
    return result

@api_router.post("/auth/forgot-password")
async def forgot_password(reset_data: PasswordReset, request: Request):
    """Request password reset"""
    success = await auth_service.create_password_reset(reset_data.email)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}

@api_router.post("/auth/reset-password")
async def reset_password(reset_data: ResetPassword, request: Request):
    """Reset password using token"""
    success = await auth_service.reset_password(reset_data.token, reset_data.new_password)
    
    if success:
        return {"message": "Password reset successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@api_router.post("/auth/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: dict = Depends(auth_service.get_current_user),
    request: Request = None
):
    """Change password for authenticated user"""
    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    new_password_hash = auth_service.hash_password(password_data.new_password)
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"password": new_password_hash, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="change_password",
        resource="user",
        details={"user_id": current_user["id"]},
        **client_info
    )
    
    # Send security notification
    try:
        await email_service.send_security_notification(
            recipient_email=current_user["email"],
            user_name=current_user["name"],
            event_type="password_change",
            event_details={
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": client_info.get("ip_address", "Unknown")
            }
        )
    except Exception as e:
        print(f"Failed to send password change notification: {e}")
    
    return {"message": "Password changed successfully"}

@api_router.get("/auth/verify-email")
async def verify_email(token: str, request: Request):
    """Verify email address"""
    success = await auth_service.verify_email(token)
    
    if success:
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

# ============================================================================
# ADMIN PANEL ROUTES
# ============================================================================

@api_router.get("/admin/users")
async def get_all_users(
    current_user: dict = Depends(auth_service.require_permission(Permission.READ_USER))
):
    """Get all users (Admin only)"""
    users = await db.users.find({}, {"password": 0}).to_list(1000)
    return [User(**parse_from_mongo(user)) for user in users]

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: dict = Depends(auth_service.require_permission(Permission.MANAGE_ROLES)),
    request: Request = None
):
    """Update user role (Admin only)"""
    # Prevent non-super-admin from creating super-admin
    if (new_role == UserRole.SUPER_ADMIN and 
        current_user["role"] != UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Cannot assign super admin role")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user["role"]
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": new_role, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="update_user_role",
        resource="user",
        details={
            "target_user_id": user_id,
            "old_role": old_role,
            "new_role": new_role
        },
        **client_info
    )
    
    # Send notification to user
    try:
        await email_service.send_role_change_notification(
            recipient_email=user["email"],
            user_name=user["name"],
            old_role=old_role,
            new_role=new_role,
            changed_by=current_user["name"]
        )
    except Exception as e:
        print(f"Failed to send role change notification: {e}")
    
    return {"message": "User role updated successfully"}

@api_router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(auth_service.require_permission(Permission.DELETE_USER)),
    request: Request = None
):
    """Delete user (Admin only)"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deletion of super admin by non-super admin
    if (user["role"] == UserRole.SUPER_ADMIN and 
        current_user["role"] != UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Cannot delete super admin")
    
    await db.users.delete_one({"id": user_id})
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="delete_user",
        resource="user",
        details={
            "deleted_user_id": user_id,
            "deleted_email": user["email"]
        },
        **client_info
    )
    
    return {"message": "User deleted successfully"}

@api_router.get("/admin/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(auth_service.require_permission(Permission.VIEW_AUDIT_LOGS))
):
    """Get audit logs (Admin only)"""
    logs = await db.audit_logs.find().sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    return [AuditLog(**log) for log in logs]

@api_router.post("/admin/bulk-notification")
async def send_bulk_notification(
    notification: BulkNotification,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(auth_service.require_permission(Permission.MANAGE_SETTINGS)),
    request: Request = None
):
    """Send bulk notification to users (Admin only)"""
    # Send emails in background
    background_tasks.add_task(
        email_service.send_bulk_notification,
        notification.recipient_emails,
        notification.subject,
        notification.message,
        current_user["name"]
    )
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="send_bulk_notification",
        resource="notification",
        details={
            "recipients_count": len(notification.recipient_emails),
            "subject": notification.subject
        },
        **client_info
    )
    
    return {"message": "Bulk notification queued for delivery"}

# ============================================================================
# EMPLOYEE MANAGEMENT ROUTES (Enhanced with Permissions)
# ============================================================================

@api_router.post("/employees", response_model=Employee)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: dict = Depends(auth_service.require_permission(Permission.CREATE_EMPLOYEE)),
    request: Request = None
):
    # Check if employee_id already exists
    existing = await db.employees.find_one({"employee_id": employee_data.employee_id})
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    employee = Employee(**employee_data.dict())
    employee_dict = prepare_for_mongo(employee.dict())
    await db.employees.insert_one(employee_dict)
    
    # Create default onboarding tasks if status is onboarding
    if employee.status == EmployeeStatus.ONBOARDING:
        await create_default_tasks_for_employee(employee.id, TaskType.ONBOARDING, current_user["email"])
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="create_employee",
        resource="employee",
        details={"employee_id": employee_data.employee_id, "name": employee_data.name},
        **client_info
    )
    
    return employee

@api_router.get("/employees", response_model=List[Employee])
async def get_employees(
    current_user: dict = Depends(auth_service.require_permission(Permission.READ_EMPLOYEE))
):
    employees = await db.employees.find().to_list(1000)
    return [Employee(**parse_from_mongo(emp)) for emp in employees]

@api_router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(
    employee_id: str,
    current_user: dict = Depends(auth_service.require_permission(Permission.READ_EMPLOYEE))
):
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return Employee(**parse_from_mongo(employee))

@api_router.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(
    employee_id: str,
    update_data: EmployeeUpdate,
    current_user: dict = Depends(auth_service.require_permission(Permission.UPDATE_EMPLOYEE)),
    request: Request = None
):
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    # Check for email uniqueness if being updated
    if 'email' in update_dict and update_dict['email'] != employee.get('email'):
        existing_email = await db.employees.find_one({"email": update_dict['email'], "id": {"$ne": employee_id}})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Check for employee_id uniqueness if being updated
    if 'employee_id' in update_dict and update_dict['employee_id'] != employee.get('employee_id'):
        existing_emp_id = await db.employees.find_one({"employee_id": update_dict['employee_id'], "id": {"$ne": employee_id}})
        if existing_emp_id:
            raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    update_dict["updated_at"] = datetime.now(timezone.utc)
    update_dict = prepare_for_mongo(update_dict)
    
    # Create exit tasks if status is changing to exiting
    if update_data.status == EmployeeStatus.EXITING and employee.get("status") != EmployeeStatus.EXITING:
        await create_default_tasks_for_employee(employee_id, TaskType.EXIT, current_user["email"])
    
    await db.employees.update_one({"id": employee_id}, {"$set": update_dict})
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="update_employee",
        resource="employee",
        details={"employee_id": employee_id, "updates": update_dict},
        **client_info
    )
    
    updated_employee = await db.employees.find_one({"id": employee_id})
    return Employee(**parse_from_mongo(updated_employee))

@api_router.put("/employees/{employee_id}/profile", response_model=Employee)
async def update_employee_profile(
    employee_id: str,
    update_data: dict,
    current_user: dict = Depends(auth_service.require_permission(Permission.UPDATE_EMPLOYEE)),
    request: Request = None
):
    """Enhanced employee profile update endpoint"""
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Validate and process update fields
    valid_fields = {'name', 'employee_id', 'email', 'department', 'manager', 'start_date', 'status', 'exit_date'}
    update_dict = {}
    
    for field, value in update_data.items():
        if field in valid_fields and value is not None:
            # Handle date fields
            if field in ['start_date', 'exit_date'] and isinstance(value, str):
                try:
                    update_dict[field] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid date format for {field}")
            # Validate email format
            elif field == 'email':
                if '@' not in str(value) or '.' not in str(value):
                    raise HTTPException(status_code=400, detail="Invalid email format")
                update_dict[field] = value
            # Validate status enum
            elif field == 'status':
                try:
                    EmployeeStatus(value)  # This will raise ValueError if invalid
                    update_dict[field] = value
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join([s.value for s in EmployeeStatus])}")
            # Validate name is not empty
            elif field == 'name':
                if not str(value).strip():
                    raise HTTPException(status_code=400, detail="Name cannot be empty")
                update_dict[field] = value
            else:
                update_dict[field] = value
    
    # Check for email uniqueness if being updated
    if 'email' in update_dict and update_dict['email'] != employee.get('email'):
        existing_email = await db.employees.find_one({"email": update_dict['email'], "id": {"$ne": employee_id}})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Check for employee_id uniqueness if being updated
    if 'employee_id' in update_dict and update_dict['employee_id'] != employee.get('employee_id'):
        existing_emp_id = await db.employees.find_one({"employee_id": update_dict['employee_id'], "id": {"$ne": employee_id}})
        if existing_emp_id:
            raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    # Update timestamp
    update_dict["updated_at"] = datetime.now(timezone.utc)
    update_dict = prepare_for_mongo(update_dict)
    
    # Handle status changes and task creation
    old_status = employee.get("status")
    new_status = update_dict.get("status")
    
    # Create exit tasks if status is changing to exiting
    if new_status == EmployeeStatus.EXITING and old_status != EmployeeStatus.EXITING:
        await create_default_tasks_for_employee(employee_id, TaskType.EXIT, current_user["email"])
    
    # Update employee
    await db.employees.update_one({"id": employee_id}, {"$set": update_dict})
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="update_employee_profile",
        resource="employee",
        details={"employee_id": employee_id, "updates": update_dict},
        **client_info
    )
    
    # Get updated employee
    updated_employee = await db.employees.find_one({"id": employee_id})
    return Employee(**parse_from_mongo(updated_employee))

@api_router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user: dict = Depends(auth_service.require_permission(Permission.DELETE_EMPLOYEE)),
    request: Request = None
):
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Delete associated tasks
    await db.tasks.delete_many({"employee_id": employee_id})
    
    # Delete employee
    await db.employees.delete_one({"id": employee_id})
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="delete_employee",
        resource="employee",
        details={"employee_id": employee_id, "name": employee["name"]},
        **client_info
    )
    
    return {"message": f"Employee {employee['name']} and associated tasks deleted successfully"}

# Continue with existing employee import, task management, and other routes...
# [Rest of the original server.py routes with enhanced permissions]

@api_router.post("/employees/import-excel")
async def import_employees_from_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(auth_service.require_permission(Permission.IMPORT_EMPLOYEES)),
    request: Request = None
):
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Please upload an Excel (.xlsx, .xls) or CSV file")
    
    try:
        # Save uploaded file temporarily for AI analysis
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        # Read and save file content
        content = await file.read()
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(content)
        
        # AI Analysis of the Excel file
        ai_analysis = None
        if ai_service:
            try:
                ai_analysis = await ai_service.analyze_excel_file(temp_file_path, "excel")
            except Exception as e:
                print(f"AI analysis failed: {e}")
        
        # Parse Excel/CSV file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_file_path)
        else:
            df = pd.read_excel(temp_file_path)
        
        # Validate required columns
        required_columns = ['Name', 'Employee ID', 'Email', 'Department', 'Manager', 'Start Date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            shutil.rmtree(temp_dir)
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if employee ID already exists
                existing = await db.employees.find_one({"employee_id": str(row['Employee ID'])})
                if existing:
                    errors.append(f"Row {index + 2}: Employee ID {row['Employee ID']} already exists")
                    continue
                
                # Parse start date
                start_date = pd.to_datetime(row['Start Date']).to_pydatetime()
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                
                # Create employee object
                employee = Employee(
                    name=str(row['Name']).strip(),
                    employee_id=str(row['Employee ID']).strip(),
                    email=str(row['Email']).strip().lower(),
                    department=str(row['Department']).strip(),
                    manager=str(row['Manager']).strip(),
                    start_date=start_date,
                    status=EmployeeStatus.ONBOARDING
                )
                
                # Save to database
                employee_dict = prepare_for_mongo(employee.dict())
                await db.employees.insert_one(employee_dict)
                
                # Create default onboarding tasks
                await create_default_tasks_for_employee(employee.id, TaskType.ONBOARDING, current_user["email"])
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                continue
        
        # Clean up temp file
        shutil.rmtree(temp_dir)
        
        # Log action
        client_info = await get_client_info(request)
        await auth_service.log_action(
            user_id=current_user["id"],
            action="import_employees",
            resource="employee",
            details={
                "file_name": file.filename,
                "imported_count": imported_count,
                "total_rows": len(df),
                "errors_count": len(errors)
            },
            **client_info
        )
        
        result = {
            "message": f"Successfully imported {imported_count} employees",
            "imported_count": imported_count,
            "total_rows": len(df),
            "errors": errors,
            "ai_analysis": ai_analysis
        }
        
        return result
        
    except Exception as e:
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# Task routes with enhanced permissions
@api_router.post("/tasks", response_model=Task)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(auth_service.require_permission(Permission.CREATE_TASK)),
    request: Request = None
):
    task = Task(**task_data.dict(), assigned_by=current_user["email"])
    task_dict = prepare_for_mongo(task.dict())
    await db.tasks.insert_one(task_dict)
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="create_task",
        resource="task",
        details={"task_title": task_data.title, "employee_id": task_data.employee_id},
        **client_info
    )
    
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(
    employee_id: Optional[str] = None,
    task_type: Optional[TaskType] = None,
    current_user: dict = Depends(auth_service.require_permission(Permission.READ_TASK))
):
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if task_type:
        query["task_type"] = task_type.value
    
    tasks = await db.tasks.find(query).to_list(1000)
    return [Task(**parse_from_mongo(task)) for task in tasks]

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    current_user: dict = Depends(auth_service.require_permission(Permission.UPDATE_TASK)),
    request: Request = None
):
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
    
    # Log action
    client_info = await get_client_info(request)
    await auth_service.log_action(
        user_id=current_user["id"],
        action="update_task",
        resource="task",
        details={"task_id": task_id, "updates": update_dict},
        **client_info
    )
    
    updated_task = await db.tasks.find_one({"id": task_id})
    return Task(**parse_from_mongo(updated_task))

# AI Endpoints with enhanced permissions
@api_router.post("/ai/analyze-employee")
async def analyze_employee_with_ai(
    employee_id: str,
    current_user: dict = Depends(auth_service.require_permission(Permission.USE_AI_FEATURES))
):
    """Generate AI insights for a specific employee"""
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    # Get employee data
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get employee tasks
    tasks = await db.tasks.find({"employee_id": employee_id}).to_list(100)
    
    # Generate AI insights
    try:
        insights = await ai_service.generate_employee_insights(employee, tasks)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@api_router.post("/ai/validate-employee")
async def validate_employee_data(
    employee_data: dict,
    current_user: dict = Depends(auth_service.require_permission(Permission.USE_AI_FEATURES))
):
    """AI-powered validation of employee data"""
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        validation = await ai_service.validate_employee_data(employee_data)
        return validation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI validation failed: {str(e)}")

@api_router.get("/ai/task-suggestions")
async def get_ai_task_suggestions(
    current_user: dict = Depends(auth_service.require_permission(Permission.USE_AI_FEATURES))
):
    """Get AI-powered task and workflow suggestions"""
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    # Get current tasks and employees for analysis
    tasks = await db.tasks.find().to_list(1000)
    employees = await db.employees.find().to_list(1000)
    
    try:
        suggestions = await ai_service.suggest_task_improvements(tasks, employees)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI suggestions failed: {str(e)}")

# Dashboard and reporting routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(auth_service.require_permission(Permission.VIEW_ANALYTICS))
):
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
async def get_recent_activities(
    current_user: dict = Depends(auth_service.require_permission(Permission.VIEW_ANALYTICS))
):
    # Get recent employees
    recent_employees = await db.employees.find().sort("created_at", -1).limit(5).to_list(5)
    
    # Get recent tasks
    recent_tasks = await db.tasks.find().sort("updated_at", -1).limit(10).to_list(10)
    
    return {
        "recent_employees": [Employee(**parse_from_mongo(emp)) for emp in recent_employees],
        "recent_tasks": [Task(**parse_from_mongo(task)) for task in recent_tasks]
    }

# Report generation with enhanced permissions
def generate_employee_report_pdf(employees, reports_data):
    """Generate PDF report for employees (unchanged from original)"""
    # [Original PDF generation code here - keeping it as is for brevity]
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
async def export_employees_report(
    current_user: dict = Depends(auth_service.require_permission(Permission.EXPORT_DATA))
):
    """Export employee report as PDF"""
    # Get all employees
    employees = await db.employees.find().to_list(1000)
    
    # Get additional report data
    reports_data = {
        "generated_by": current_user["name"],
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "2.0.0-enhanced-security"
    }