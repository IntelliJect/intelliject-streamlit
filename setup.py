"""
Database setup script for IntelliJect.
Creates database tables and initializes the application.
"""
import os
from database import Base, engine
from models import PYQ, PDFHistory

def setup_database():
    """Create all database tables."""
    print("🔧 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    setup_database()