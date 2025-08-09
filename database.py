"""
Database configuration and session management for IntelliJect.
Enhanced to support both SQLite (local) and PostgreSQL (production).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration - supports both SQLite and PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production: Use PostgreSQL (Render provides DATABASE_URL)
    if DATABASE_URL.startswith("postgres://"):
        # Fix for newer SQLAlchemy versions
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
else:
    # Local development: Use SQLite
    DATABASE_URL = "sqlite:///./intelliject.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for model definitions
Base = declarative_base()

def get_database():
    """
    Dependency function to get database session.
    Yields:
        Database session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """
    Direct function to get database session for non-FastAPI usage.
    Returns a session that should be closed manually.
    """
    return SessionLocal()

# Print database info for debugging
if DATABASE_URL:
    if "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
        print("🐘 Using PostgreSQL database")
    else:
        print("🗃️ Using SQLite database")
