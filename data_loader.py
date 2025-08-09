"""
Data loader for IntelliJect PYQ database.
Loads PYQ data from JSON files with PostgreSQL-first, JSON-fallback approach.
"""

import json
import os
from pathlib import Path
from sqlalchemy.orm import Session
from database import SessionLocal, engine, get_database_mode
from models import Base, PYQ
import crud

def load_pyqs_from_json(json_file_path: str, subject_name: str) -> list:
    """
    Load PYQs from a JSON file.
    
    Args:
        json_file_path: Path to the JSON file
        subject_name: Name of the subject
        
    Returns:
        List of PYQ dictionaries
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        pyqs = []
        for item in data:
            pyq_data = {
                "subject": subject_name,
                "sub_topic": item.get("sub_topic", item.get("topic", "General")),
                "question": item.get("question", ""),
                "marks": int(item.get("marks", 0)) if str(item.get("marks", 0)).replace('.', '').isdigit() else 0,
                "year": str(item.get("year", "2024")),
                "semester": item.get("semester", ""),
                "branch": item.get("branch", ""),
                "unit": item.get("unit", "")
            }
            
            if pyq_data["question"].strip():  # Only add if question exists
                pyqs.append(pyq_data)
                
        return pyqs
        
    except Exception as e:
        print(f"❌ Error loading {json_file_path}: {e}")
        return []

def create_json_subjects_file(subject_files: dict):
    """
    Create/update subjects.json with available subjects from JSON files.
    
    Args:
        subject_files: Dictionary mapping filenames to subject names
    """
    available_subjects = []
    possible_paths = ["subjects/", "./", "data/"]
    
    # Check which JSON files actually exist
    for filename, subject_name in subject_files.items():
        for base_path in possible_paths:
            file_path = os.path.join(base_path, filename)
            if os.path.exists(file_path):
                available_subjects.append(subject_name)
                break
    
    # Create subjects.json with available subjects
    subjects_data = {
        "subjects": available_subjects,
        "metadata": {
            "created": "auto-generated",
            "description": "Available subjects from JSON files (PostgreSQL fallback)",
            "data_source": "JSON files in subjects folder",
            "mode": "postgresql-with-json-fallback"
        }
    }
    
    try:
        with open("subjects.json", "w", encoding="utf-8") as file:
            json.dump(subjects_data, file, indent=2, ensure_ascii=False)
        print(f"✅ Created subjects.json with {len(available_subjects)} subjects")
        return True
    except Exception as e:
        print(f"❌ Error creating subjects.json: {e}")
        return False

def load_all_subjects():
    """
    Load all PYQ data with PostgreSQL-first, JSON-fallback approach.
    """
    # Subject mappings: filename -> subject name
    subject_files = {
        "cyber_security.json": "Cyber Security",
        "Probability-and-Statistics.json": "Probability and Statistics", 
        "environmental_sciences.json": "Environmental Sciences"
    }
    
    # Always create/update subjects.json for fallback
    create_json_subjects_file(subject_files)
    
    database_mode = get_database_mode()
    print(f"🔧 Database mode detected: {database_mode}")
    
    if database_mode == "json":
        print("📁 JSON mode: Using subjects.json, no database population needed")
        return
    
    # Try to use PostgreSQL/SQLite
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Look for JSON files in subjects folder and current directory
        possible_paths = ["subjects/", "./", "data/"]
        
        db = SessionLocal()
        total_loaded = 0
        successfully_loaded_subjects = []
        
        try:
            for filename, subject_name in subject_files.items():
                file_found = False
                
                # Try different possible paths
                for base_path in possible_paths:
                    file_path = os.path.join(base_path, filename)
                    
                    if os.path.exists(file_path):
                        print(f"📚 Loading {subject_name} from {file_path}")
                        
                        pyqs = load_pyqs_from_json(file_path, subject_name)
                        
                        if pyqs:
                            try:
                                # Clear existing PYQs for this subject
                                db.query(PYQ).filter(PYQ.subject == subject_name).delete()
                                
                                # Store new PYQs
                                count = crud.store_pyqs(db, pyqs, subject_name)
                                total_loaded += count
                                successfully_loaded_subjects.append(subject_name)
                                print(f"✅ Loaded {count} PYQs for {subject_name}")
                            except Exception as e:
                                print(f"❌ Failed to store PYQs for {subject_name}: {e}")
                                db.rollback()
                        
                        file_found = True
                        break
                
                if not file_found:
                    print(f"⚠️ File {filename} not found in any of: {possible_paths}")
            
            db.commit()
            
            if total_loaded > 0:
                print(f"🎉 Successfully loaded {total_loaded} total PYQs across {len(successfully_loaded_subjects)} subjects")
                print(f"📊 Subjects in database: {successfully_loaded_subjects}")
            else:
                print("⚠️ No PYQs loaded into database")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error during database operations: {e}")
            print("📁 Fallback: subjects.json will be used instead")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("📁 Application will use JSON fallback mode")

def test_database_connection():
    """
    Test if database connection is working.
    
    Returns:
        bool: True if database is working, False otherwise
    """
    try:
        database_mode = get_database_mode()
        
        if database_mode == "json":
            print("📁 Database test: Using JSON fallback mode")
            return False
        
        # Test database connection
        db = SessionLocal()
        try:
            # Try a simple query
            result = db.execute("SELECT 1").fetchone()
            print(f"✅ Database connection test passed ({database_mode})")
            return True
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def create_subject_structure():
    """
    Create the subjects folder structure and move JSON files.
    """
    subjects_dir = Path("subjects")
    subjects_dir.mkdir(exist_ok=True)
    
    print("📁 Created subjects/ directory")
    print("💡 Place your JSON files in the subjects/ folder:")
    print("   - subjects/cyber_security.json")
    print("   - subjects/Probability-and-Statistics.json") 
    print("   - subjects/environmental_sciences.json")

if __name__ == "__main__":
    print("🚀 IntelliJect Data Loader (PostgreSQL + JSON Fallback)")
    print("=" * 60)
    
    # Test database connection
    db_working = test_database_connection()
    
    # Create subjects directory structure
    create_subject_structure()
    
    # Load all PYQ data (PostgreSQL first, JSON fallback)
    load_all_subjects()
    
    print("=" * 60)
    
    if db_working:
        print("✅ Data loading complete! Using PostgreSQL database.")
    else:
        print("✅ Data loading complete! Using JSON fallback mode.")
        print("📁 Subjects available from subjects.json file.")
    
    print("🎯 Your IntelliJect app will work in both modes automatically!")
