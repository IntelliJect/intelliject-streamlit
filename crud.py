"""
CRUD operations for PYQ and PDF history management.
Provides database interaction functions for the IntelliJect application.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import models

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
