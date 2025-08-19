#!/usr/bin/env python3
"""
Script to create a demo admin user for the HR system
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import bcrypt
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def create_admin_user():
    # MongoDB connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": "admin@company.com"})
    if existing_admin:
        print("Admin user already exists!")
        return
    
    # Create admin user
    password = "admin123"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    admin_user = {
        "id": "admin-001",
        "email": "admin@company.com",
        "name": "System Administrator",
        "role": "admin",
        "password": hashed_password,
        "created_at": "2024-01-01T00:00:00+00:00"
    }
    
    await db.users.insert_one(admin_user)
    print("Demo admin user created successfully!")
    print("Email: admin@company.com")
    print("Password: admin123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())