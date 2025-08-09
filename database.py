"""
Database configuration and session management for IntelliJect.
Sets up SQLAlchemy engine, session, and base model class.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./intelliject.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite specific
    )
else:
    engine = create_engine(DATABASE_URL)

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
