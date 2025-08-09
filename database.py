"""
Database configuration and session management for IntelliJect.
PostgreSQL-first with JSON fallback support.
"""

import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration - PostgreSQL first, SQLite second, JSON fallback
DATABASE_URL = os.getenv("DATABASE_URL")

def load_subjects_from_json():
    """Load subjects from JSON file as fallback"""
    try:
        with open("subjects.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("subjects", [])
    except FileNotFoundError:
        print("⚠️ subjects.json not found, creating default file")
        create_default_subjects_json()
        return ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"]
    except Exception as e:
        print(f"❌ Error reading subjects.json: {e}")
        return ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"]

def create_default_subjects_json():
    """Create default subjects.json file"""
    default_data = {
        "subjects": [
            "Cyber Security",
            "Probability and Statistics",
            "Environmental Sciences",
            "Computer Science",
            "Mathematics", 
            "Physics",
            "Chemistry",
            "Biology"
        ],
        "metadata": {
            "created": "auto-generated",
            "description": "Default subjects for IntelliJect application",
            "mode": "fallback"
        }
    }
    
    try:
        with open("subjects.json", "w", encoding="utf-8") as file:
            json.dump(default_data, file, indent=2, ensure_ascii=False)
        print("✅ Created default subjects.json file")
    except Exception as e:
        print(f"❌ Error creating subjects.json: {e}")

# Database setup with PostgreSQL-first approach
engine = None
DATABASE_MODE = "json"

if DATABASE_URL:
    # Try PostgreSQL first
    try:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=20,
            pool_reset_on_return='commit',
            echo=False
        )
        
        # Test connection with a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        print("🐘 Using PostgreSQL database")
        DATABASE_MODE = "postgresql"
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("📁 Falling back to JSON file storage")
        engine = None
        DATABASE_MODE = "json"
else:
    # Try SQLite for local development
    try:
        DATABASE_URL = "sqlite:///./intelliject.db"
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        print("🗃️ Using SQLite database")
        DATABASE_MODE = "sqlite"
        
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        print("📁 Falling back to JSON file storage")
        engine = None
        DATABASE_MODE = "json"

# Create SessionLocal class for database sessions (only if engine exists)
if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

# Create Base class for model definitions
Base = declarative_base()

def get_database_mode():
    """Returns current database mode: 'postgresql', 'sqlite', or 'json'"""
    return DATABASE_MODE

def get_db_session():
    """Direct function to get database session. Returns None if using JSON fallback."""
    if SessionLocal:
        try:
            return SessionLocal()
        except Exception as e:
            print(f"❌ Failed to create database session: {e}")
            return None
    return None
