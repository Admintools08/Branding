#!/usr/bin/env python3
"""
Script to create the updated admin user for the HR system
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
    
    # Remove old admin if exists
    await db.users.delete_many({"email": {"$in": ["admin@company.com", "omnathtripathi1@gmail.com"]}})
    
    # Create new admin user
    password = "BrandingPioneers2024!"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    admin_user = {
        "id": "admin-branding-pioneers",
        "email": "omnathtripathi1@gmail.com",
        "name": "Omnath Tripathi",
        "role": "admin",
        "password": hashed_password,
        "created_at": "2024-01-01T00:00:00+00:00"
    }
    
    await db.users.insert_one(admin_user)
    print("✅ New admin user created successfully!")
    print("🚀 Company: Branding Pioneers (Digital Ninjas)")
    print("📧 Email: omnathtripathi1@gmail.com")
    print("🔑 Password: BrandingPioneers2024!")
    print("🎯 Role: Super Admin with all permissions")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())