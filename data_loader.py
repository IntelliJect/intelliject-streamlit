"""
Database configuration and session management for IntelliJect.
Enhanced version with better path handling and connection management.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables
load_dotenv()

# Database configuration with absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
default_db = os.path.join(BASE_DIR, "intelliject.db")
DEFAULT_URL = f"sqlite:///{default_db}"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)

# Create engine with enhanced settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Prevents stale connections
    pool_recycle=3600    # Recycle connections every hour
)

# Session factory with improved settings
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevents attributes being expired after commit
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_database():
    """
    Dependency function to get database session.
    Yields database session and ensures proper cleanup.
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