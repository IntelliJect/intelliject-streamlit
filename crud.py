"""
CRUD operations for PYQ and PDF history management.
Provides database interaction functions for the IntelliJect application.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import models

def get_subjects(db: Session = None) -> List[str]:
    """
    Get all unique subjects from database or JSON file.
    """
    from database import get_database_mode, load_subjects_from_json
    
    database_mode = get_database_mode()
    
    # If JSON mode or no database session, use JSON fallback
    if database_mode == "json" or db is None:
        return load_subjects_from_json()
    
    # Try database first
    try:
        subjects = db.query(models.PYQ.subject).distinct().all()
        result = [subject[0] for subject in subjects if subject[0]]
        
        # If no subjects in database, fallback to JSON
        if not result:
            print("📁 No subjects in database, falling back to JSON")
            return load_subjects_from_json()
            
        return result
    except Exception as e:
        print(f"❌ Error getting subjects from database: {e}")
        print("📁 Falling back to JSON file")
        return load_subjects_from_json()


def create_subject(db: Session, subject_name: str) -> bool:
    """
    Create a dummy PYQ entry for a subject to ensure it appears in subjects list.
    
    Args:
        db: Database session
        subject_name: Name of the subject to create
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if subject already exists
        existing = db.query(models.PYQ).filter(models.PYQ.subject == subject_name).first()
        if existing:
            return True
            
        # Create a placeholder PYQ entry for this subject
        placeholder_pyq = models.PYQ(
            subject=subject_name,
            sub_topic="General",
            question=f"Sample question for {subject_name}",
            marks=1,
            year="2024",
            semester="1",
            branch="General",
            unit="1"
        )
        
        db.add(placeholder_pyq)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating subject {subject_name}: {e}")
        return False

def get_pyqs_by_subject(db: Session, subject: str) -> List[models.PYQ]:
    """
    Retrieve all PYQ entries for the given subject.
    
    Args:
        db: Database session
        subject: Subject name to filter by
        
    Returns:
        List of PYQ objects
    """
    return db.query(models.PYQ).filter(models.PYQ.subject == subject).all()

def store_pyqs(db: Session, pyqs: List[Dict], subject: str) -> int:
    """
    Store a list of PYQs in the database under the given subject.
    
    Args:
        db: Database session
        pyqs: List of PYQ dictionaries
        subject: Subject name
        
    Returns:
        Number of successfully stored PYQs
    """
    if not pyqs:
        return 0

    pyq_objects = []
    for entry in pyqs:
        question = entry.get("question")
        if not question:
            continue

        pyq_obj = models.PYQ(
            subject=subject,
            sub_topic=entry.get("sub_topic", ""),
            question=question,
            marks=entry.get("marks", 0),
            year=entry.get("year", ""),
            semester=entry.get("semester", ""),
            branch=entry.get("branch", ""),
            unit=entry.get("unit", "")
        )
        pyq_objects.append(pyq_obj)

    try:
        db.add_all(pyq_objects)
        db.commit()
        return len(pyq_objects)
    except Exception as e:
        db.rollback()
        print(f"❌ Error storing PYQs: {e}")
        return 0

def get_all_pyqs(db: Session) -> List[models.PYQ]:
    """
    Get all PYQs from database.
    
    Args:
        db: Database session
        
    Returns:
        List of all PYQ objects
    """
    return db.query(models.PYQ).all()

def add_pdf_history(db: Session, filename: str, subject: str) -> Optional[models.PDFHistory]:
    """
    Add PDF upload history.
    
    Args:
        db: Database session
        filename: Name of uploaded PDF file
        subject: Subject associated with the PDF
        
    Returns:
        PDFHistory object if successful, None otherwise
    """
    try:
        history = models.PDFHistory(filename=filename, subject=subject)
        db.add(history)
        db.commit()
        db.refresh(history)
        return history
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding PDF history: {e}")
        return None

def get_pdf_history(db: Session) -> List[models.PDFHistory]:
    """
    Get PDF upload history ordered by most recent first.
    
    Args:
        db: Database session
        
    Returns:
        List of PDFHistory objects
    """
    return db.query(models.PDFHistory).order_by(models.PDFHistory.timestamp.desc()).all()
