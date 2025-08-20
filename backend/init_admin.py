"""
Enhanced Admin Initialization Script
Creates a super admin user with email verification and comprehensive permissions
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid
from auth_service import AuthService, UserRole

# Load environment variables
load_dotenv()

async def init_super_admin():
    """Initialize super admin user if no users exist"""
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Initialize auth service
    secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
    auth_service = AuthService(db, secret_key)
    
    try:
        # Check if any users exist
        user_count = await db.users.count_documents({})
        
        if user_count == 0:
            print("No users found. Creating super admin user...")
            
            # Default super admin credentials
            super_admin_data = {
                "id": str(uuid.uuid4()),
                "email": "admin@brandingpioneers.com",
                "name": "Super Administrator",
                "password": auth_service.hash_password("SuperAdmin2024!"),
                "role": UserRole.SUPER_ADMIN.value,
                "email_verified": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.users.insert_one(super_admin_data)
            
            print("✅ Super Admin user created successfully!")
            print("📧 Email: admin@brandingpioneers.com")
            print("🔐 Password: SuperAdmin2024!")
            print("⚠️  Please change the password after first login!")
            
        else:
            print(f"Found {user_count} existing users. No initialization needed.")
            
        # Ensure database indexes for performance
        await create_indexes(db)
        
    except Exception as e:
        print(f"❌ Error initializing admin: {e}")
        
    finally:
        client.close()

async def create_indexes(db):
    """Create database indexes for better performance"""
    try:
        # User collection indexes
        await db.users.create_index([("email", 1)], unique=True)
        await db.users.create_index([("id", 1)], unique=True)
        
        # Employee collection indexes
        await db.employees.create_index([("employee_id", 1)], unique=True)
        await db.employees.create_index([("id", 1)], unique=True)
        await db.employees.create_index([("email", 1)])
        await db.employees.create_index([("status", 1)])
        
        # Task collection indexes
        await db.tasks.create_index([("id", 1)], unique=True)
        await db.tasks.create_index([("employee_id", 1)])
        await db.tasks.create_index([("status", 1)])
        await db.tasks.create_index([("task_type", 1)])
        await db.tasks.create_index([("due_date", 1)])
        
        # Invitation collection indexes
        await db.user_invitations.create_index([("invitation_token", 1)], unique=True)
        await db.user_invitations.create_index([("email", 1)])
        await db.user_invitations.create_index([("expires_at", 1)])
        
        # Password reset collection indexes
        await db.password_resets.create_index([("token", 1)], unique=True)
        await db.password_resets.create_index([("user_id", 1)])
        await db.password_resets.create_index([("expires_at", 1)])
        
        # Email verification collection indexes
        await db.email_verifications.create_index([("token", 1)], unique=True)
        await db.email_verifications.create_index([("user_id", 1)])
        await db.email_verifications.create_index([("expires_at", 1)])
        
        # Audit logs collection indexes
        await db.audit_logs.create_index([("user_id", 1)])
        await db.audit_logs.create_index([("timestamp", -1)])
        await db.audit_logs.create_index([("action", 1)])
        await db.audit_logs.create_index([("resource", 1)])
        
        print("✅ Database indexes created successfully!")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not create some indexes: {e}")

async def create_sample_data():
    """Create sample data for development/testing"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Check if sample data already exists
        employee_count = await db.employees.count_documents({})
        
        if employee_count == 0:
            print("Creating sample employees for demonstration...")
            
            sample_employees = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Alice Johnson",
                    "employee_id": "NIN001",
                    "email": "alice.johnson@brandingpioneers.com",
                    "department": "Engineering",
                    "manager": "Tech Lead",
                    "start_date": datetime(2024, 1, 15, tzinfo=timezone.utc).isoformat(),
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Bob Smith",
                    "employee_id": "NIN002",
                    "email": "bob.smith@brandingpioneers.com",
                    "department": "Design",
                    "manager": "Design Lead",
                    "start_date": datetime(2024, 2, 1, tzinfo=timezone.utc).isoformat(),
                    "status": "onboarding",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Carol Brown",
                    "employee_id": "NIN003",
                    "email": "carol.brown@brandingpioneers.com",
                    "department": "HR",
                    "manager": "HR Director",
                    "start_date": datetime(2023, 6, 10, tzinfo=timezone.utc).isoformat(),
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ]
            
            await db.employees.insert_many(sample_employees)
            print(f"✅ Created {len(sample_employees)} sample employees")
            
        else:
            print(f"Found {employee_count} existing employees. Skipping sample data creation.")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not create sample data: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Initializing HR System Database...")
    asyncio.run(init_super_admin())
    
    # Automatically create sample data for demonstration
    print("Creating sample data...")
    asyncio.run(create_sample_data())
    
    print("\n🎉 Database initialization complete!")
    print("\n🔗 Access your HR system at: https://user-data-update.preview.emergentagent.com")
    print("📧 Login with: admin@brandingpioneers.com")
    print("🔐 Password: SuperAdmin2024!")