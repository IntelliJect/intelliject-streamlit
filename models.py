"""
SQLAlchemy database models for IntelliJect.
Defines the database schema for PYQs and PDF upload history.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class PYQ(Base):
    """
    Previous Year Questions model.
    
    Stores academic questions with metadata including subject, year, marks, etc.
    """
    __tablename__ = "pyqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False, index=True)
    year = Column(String, index=True)
    semester = Column(String)
    branch = Column(String)
    unit = Column(String)
    marks = Column(Float, default=0.0)  # Supports decimal marks like 2.5
    sub_topic = Column(String, index=True)
    subject = Column(String, nullable=False, index=True)
    
    def __repr__(self):
        return f"<PYQ(id={self.id}, subject='{self.subject}', marks={self.marks})>"
    
    def to_dict(self):
        """Convert PYQ instance to dictionary."""
        return {
            'id': self.id,
            'question': self.question,
            'year': self.year,
            'semester': self.semester,
            'branch': self.branch,
            'unit': self.unit,
            'marks': self.marks,
            'sub_topic': self.sub_topic,
            'subject': self.subject
        }

class PDFHistory(Base):
    """
    PDF upload history model.
    
    Tracks PDF files uploaded by users with timestamps and subject associations.
    """
    __tablename__ = "pdf_history"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<PDFHistory(id={self.id}, filename='{self.filename}', subject='{self.subject}')>"
    
    def to_dict(self):
        """Convert PDFHistory instance to dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'subject': self.subject,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
