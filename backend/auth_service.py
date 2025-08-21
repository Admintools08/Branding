"""
Enhanced Authentication Service with Multi-level Access Control
Handles user invitations, password reset, email verification, and role-based permissions
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
import jwt
import bcrypt
import secrets
import uuid
from pydantic import BaseModel, EmailStr
from enum import Enum
from email_service import email_service

# Enhanced Role System with Hierarchical Permissions
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"  # Full system access, can manage other admins
    ADMIN = "admin"              # Can manage users, view all data, system settings
    HR_MANAGER = "hr_manager"    # Can manage employees and tasks, limited admin features
    MANAGER = "manager"          # Can manage team members and their tasks
    EMPLOYEE = "employee"        # Basic access to own data and tasks

class Permission(str, Enum):
    # User Management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MANAGE_ROLES = "manage_roles"
    INVITE_USER = "invite_user"
    
    # Employee Management
    CREATE_EMPLOYEE = "create_employee"
    READ_EMPLOYEE = "read_employee"
    UPDATE_EMPLOYEE = "update_employee"
    DELETE_EMPLOYEE = "delete_employee"
    IMPORT_EMPLOYEES = "import_employees"
    
    # Task Management
    CREATE_TASK = "create_task"
    READ_TASK = "read_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    MANAGE_TASK_TEMPLATES = "manage_task_templates"
    
    # Reporting & Analytics
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    VIEW_ANALYTICS = "view_analytics"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    
    # System Administration
    MANAGE_SETTINGS = "manage_settings"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_INTEGRATIONS = "manage_integrations"
    
    # AI Features
    USE_AI_FEATURES = "use_ai_features"
    CONFIGURE_AI = "configure_ai"

# Role-Permission Mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SUPER_ADMIN: {
        # All permissions
        Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER, Permission.DELETE_USER,
        Permission.MANAGE_ROLES, Permission.INVITE_USER,
        Permission.CREATE_EMPLOYEE, Permission.READ_EMPLOYEE, Permission.UPDATE_EMPLOYEE, Permission.DELETE_EMPLOYEE,
        Permission.IMPORT_EMPLOYEES,
        Permission.CREATE_TASK, Permission.READ_TASK, Permission.UPDATE_TASK, Permission.DELETE_TASK,
        Permission.MANAGE_TASK_TEMPLATES,
        Permission.VIEW_REPORTS, Permission.EXPORT_DATA, Permission.VIEW_ANALYTICS, Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_SETTINGS, Permission.VIEW_SYSTEM_LOGS, Permission.MANAGE_INTEGRATIONS,
        Permission.USE_AI_FEATURES, Permission.CONFIGURE_AI
    },
    UserRole.ADMIN: {
        Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER, Permission.DELETE_USER,
        Permission.INVITE_USER,  # Cannot manage super admin roles
        Permission.CREATE_EMPLOYEE, Permission.READ_EMPLOYEE, Permission.UPDATE_EMPLOYEE, Permission.DELETE_EMPLOYEE,
        Permission.IMPORT_EMPLOYEES,
        Permission.CREATE_TASK, Permission.READ_TASK, Permission.UPDATE_TASK, Permission.DELETE_TASK,
        Permission.MANAGE_TASK_TEMPLATES,
        Permission.VIEW_REPORTS, Permission.EXPORT_DATA, Permission.VIEW_ANALYTICS, Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_SETTINGS, Permission.VIEW_SYSTEM_LOGS,
        Permission.USE_AI_FEATURES, Permission.CONFIGURE_AI
    },
    UserRole.HR_MANAGER: {
        Permission.READ_USER, Permission.UPDATE_USER, Permission.INVITE_USER,
        Permission.CREATE_EMPLOYEE, Permission.READ_EMPLOYEE, Permission.UPDATE_EMPLOYEE, Permission.DELETE_EMPLOYEE,
        Permission.IMPORT_EMPLOYEES,
        Permission.CREATE_TASK, Permission.READ_TASK, Permission.UPDATE_TASK, Permission.DELETE_TASK,
        Permission.MANAGE_TASK_TEMPLATES,
        Permission.VIEW_REPORTS, Permission.EXPORT_DATA, Permission.VIEW_ANALYTICS,
        Permission.USE_AI_FEATURES
    },
    UserRole.MANAGER: {
        Permission.READ_USER,  # Can only read users in their department
        Permission.READ_EMPLOYEE, Permission.UPDATE_EMPLOYEE,  # Limited to their team
        Permission.CREATE_TASK, Permission.READ_TASK, Permission.UPDATE_TASK,
        Permission.VIEW_REPORTS, Permission.EXPORT_DATA,  # Limited to their team
        Permission.USE_AI_FEATURES
    },
    UserRole.EMPLOYEE: {
        Permission.READ_USER,  # Can only read own profile
        Permission.UPDATE_USER,  # Can only update own profile
        Permission.READ_EMPLOYEE,  # Can only read own employee data
        Permission.READ_TASK, Permission.UPDATE_TASK,  # Can only manage own tasks
        Permission.USE_AI_FEATURES
    }
}

# Enhanced User Models
class UserInvitation(BaseModel):
    id: str = None
    email: EmailStr
    role: UserRole
    invited_by: str
    invitation_token: str
    expires_at: datetime
    accepted: bool = False
    created_at: datetime = None

class PasswordResetToken(BaseModel):
    id: str = None
    user_id: str
    token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = None

class EmailVerification(BaseModel):
    id: str = None
    user_id: str
    token: str
    expires_at: datetime
    verified: bool = False
    created_at: datetime = None

class AuditLog(BaseModel):
    id: str = None
    user_id: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = None

class AuthService:
    def __init__(self, db, secret_key: str, algorithm: str = "HS256"):
        self.db = db
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer()
    
    def generate_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Generate JWT token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_secure_token(self) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        return permission in ROLE_PERMISSIONS.get(user_role, set())
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""
        def permission_checker(current_user: dict = Depends(self.get_current_user)):
            if not self.has_permission(UserRole(current_user["role"]), permission):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Insufficient permissions. Required: {permission.value}"
                )
            return current_user
        return permission_checker
    
    def require_role(self, required_roles: List[UserRole]):
        """Decorator to require specific roles"""
        def role_checker(current_user: dict = Depends(self.get_current_user)):
            user_role = UserRole(current_user["role"])
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient role. Required one of: {[r.value for r in required_roles]}"
                )
            return current_user
        return role_checker
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Get current authenticated user"""
        try:
            payload = self.verify_token(credentials.credentials)
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await self.db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    
    async def log_action(self, user_id: str, action: str, resource: str, 
                        details: Dict[str, Any], ip_address: str = None, 
                        user_agent: str = None):
        """Log user action for audit trail"""
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self.db.audit_logs.insert_one(audit_log.dict())
    
    async def create_user_invitation(self, email: str, role: UserRole, 
                                   invited_by: str, expires_hours: int = 48) -> UserInvitation:
        """Create user invitation with email"""
        # Check if user already exists
        existing_user = await self.db.users.find_one({"email": email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Check for existing pending invitation
        existing_invitation = await self.db.user_invitations.find_one({
            "email": email, 
            "accepted": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        if existing_invitation:
            raise HTTPException(status_code=400, detail="Pending invitation already exists")
        
        invitation = UserInvitation(
            id=str(uuid.uuid4()),
            email=email,
            role=role,
            invited_by=invited_by,
            invitation_token=self.generate_secure_token(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
            created_at=datetime.now(timezone.utc)
        )
        
        # Save to database
        await self.db.user_invitations.insert_one(invitation.dict())
        
        # Send invitation email
        invite_url = f"https://perf-boost-6.preview.emergentagent.com/accept-invite?token={invitation.invitation_token}"
        
        try:
            inviter = await self.db.users.find_one({"id": invited_by})
            inviter_name = inviter.get("name", "Admin") if inviter else "Admin"
            
            await email_service.send_user_invitation(
                recipient_email=email,
                inviter_name=inviter_name,
                role=role.value,
                invitation_token=invitation.invitation_token,
                invite_url=invite_url
            )
        except Exception as e:
            # Log email error but don't fail the invitation
            print(f"Failed to send invitation email: {e}")
        
        return invitation
    
    async def accept_invitation(self, token: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Accept user invitation and create account"""
        invitation = await self.db.user_invitations.find_one({
            "invitation_token": token,
            "accepted": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not invitation:
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")
        
        # Create user account
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": invitation["email"],
            "name": user_data["name"],
            "password": self.hash_password(user_data["password"]),
            "role": invitation["role"],
            "email_verified": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.db.users.insert_one(user)
        
        # Mark invitation as accepted
        await self.db.user_invitations.update_one(
            {"_id": invitation["_id"]},
            {"$set": {"accepted": True}}
        )
        
        # Create email verification
        await self.create_email_verification(user_id, invitation["email"])
        
        # Generate access token
        access_token = self.generate_token({"sub": invitation["email"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    
    async def create_password_reset(self, email: str) -> bool:
        """Create password reset token and send email"""
        user = await self.db.users.find_one({"email": email})
        if not user:
            # Don't reveal if email exists
            return True
        
        # Invalidate existing reset tokens
        await self.db.password_resets.update_many(
            {"user_id": user["id"], "used": False},
            {"$set": {"used": True}}
        )
        
        reset_token = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user["id"],
            token=self.generate_secure_token(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc)
        )
        
        await self.db.password_resets.insert_one(reset_token.dict())
        
        # Send reset email
        reset_url = f"https://perf-boost-6.preview.emergentagent.com/reset-password?token={reset_token.token}"
        
        try:
            await email_service.send_password_reset(
                recipient_email=email,
                user_name=user["name"],
                reset_token=reset_token.token,
                reset_url=reset_url
            )
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
        
        return True
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        reset_token = await self.db.password_resets.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Update password
        new_password_hash = self.hash_password(new_password)
        await self.db.users.update_one(
            {"id": reset_token["user_id"]},
            {"$set": {"password": new_password_hash, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Mark token as used
        await self.db.password_resets.update_one(
            {"_id": reset_token["_id"]},
            {"$set": {"used": True}}
        )
        
        return True
    
    async def create_email_verification(self, user_id: str, email: str) -> EmailVerification:
        """Create email verification token"""
        verification = EmailVerification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=self.generate_secure_token(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            created_at=datetime.now(timezone.utc)
        )
        
        await self.db.email_verifications.insert_one(verification.dict())
        
        # Send verification email
        user = await self.db.users.find_one({"id": user_id})
        verification_url = f"https://perf-boost-6.preview.emergentagent.com/verify-email?token={verification.token}"
        
        try:
            await email_service.send_email_verification(
                recipient_email=email,
                user_name=user["name"],
                verification_token=verification.token,
                verification_url=verification_url
            )
        except Exception as e:
            print(f"Failed to send verification email: {e}")
        
        return verification
    
    async def verify_email(self, token: str) -> bool:
        """Verify email using token"""
        verification = await self.db.email_verifications.find_one({
            "token": token,
            "verified": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not verification:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        # Mark email as verified
        await self.db.users.update_one(
            {"id": verification["user_id"]},
            {"$set": {"email_verified": True, "updated_at": datetime.now(timezone.utc)}}
        )
        
        await self.db.email_verifications.update_one(
            {"_id": verification["_id"]},
            {"$set": {"verified": True}}
        )
        
        return True