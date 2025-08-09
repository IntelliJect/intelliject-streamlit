"""
Database configuration with proper error handling and JSON fallback.
"""

import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def load_subjects_from_json():
    """Load subjects from JSON file as fallback"""
    try:
        with open("subjects.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("subjects", [])
    except FileNotFoundError:
        return ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"]
    except Exception as e:
        print(f"❌ Error reading subjects.json: {e}")
        return ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"]

# Initialize variables
engine = None
SessionLocal = None
DATABASE_MODE = "json"

# Database setup with proper error handling
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        # Fix postgres:// URL format
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        # Create and test PostgreSQL engine
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=20,
            echo=False
        )
        
        # Test connection with a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DATABASE_MODE = "postgresql"
        print("🐘 Using PostgreSQL database")
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("📁 Falling back to JSON mode")
        engine = None
        SessionLocal = None
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
        
        # Test SQLite connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DATABASE_MODE = "sqlite"
        print("🗃️ Using SQLite database")
        
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        print("📁 Using JSON fallback mode")
        engine = None
        SessionLocal = None
        DATABASE_MODE = "json"

# Create Base class for model definitions
Base = declarative_base()

def get_database_mode():
    """Returns current database mode: 'postgresql', 'sqlite', or 'json'"""
    return DATABASE_MODE

def get_db_session():
    """Get database session. Returns None if using JSON fallback."""
    if SessionLocal:
        try:
            return SessionLocal()
        except Exception as e:
            print(f"❌ Failed to create database session: {e}")
            return None
    return None
