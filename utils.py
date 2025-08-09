"""
Utility functions for IntelliJect.
Provides PDF text extraction, text processing, and formatting utilities.
"""
import fitz  # PyMuPDF
import re
from typing import List, Optional
from pathlib import Path

def extract_text_from_pdf(pdf_path: str) -> List[str]:
    """
    Extract text from each page of a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of text strings, one per page
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF cannot be processed
    """
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        pages_text = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            
            # Clean up the extracted text
            cleaned_text = clean_extracted_text(text)
            pages_text.append(cleaned_text)
        
        doc.close()
        return pages_text
    
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text from PDF.
    
    Args:
        text: Raw text extracted from PDF
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers and headers/footers (simple heuristic)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip very short lines that might be page numbers
        if len(line) < 3:
            continue
        # Skip lines that are just numbers (likely page numbers)
        if line.isdigit():
            continue
        cleaned_lines.append(line)
    
    return ' '.join(cleaned_lines).strip()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with optional overlap.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or chunk_size <= 0:
        return [text] if text else []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # Try to break at word boundaries
        if end < text_length:
            # Find the last space within the chunk
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position considering overlap
        start = max(start + 1, end - overlap)
        
        # Prevent infinite loop
        if start >= text_length:
            break
    
    return chunks

def chunk_text_by_sentences(text: str, max_sentences: int = 5) -> List[str]:
    """
    Split text into chunks by sentence count.
    
    Args:
        text: Input text to chunk
        max_sentences: Maximum sentences per chunk
        
    Returns:
        List of text chunks
    """
    try:
        import nltk
        from nltk.tokenize import sent_tokenize
        
        # Download required NLTK data if not present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        sentences = sent_tokenize(text)
        chunks = []
        
        for i in range(0, len(sentences), max_sentences):
            chunk = ' '.join(sentences[i:i + max_sentences])
            chunks.append(chunk.strip())
        
        return chunks
    
    except ImportError:
        # Fallback to simple chunking if NLTK not available
        return chunk_text(text, chunk_size=1000)

def highlight_chunks(text: str, highlight_class: str = "highlight") -> str:
    """
    Add HTML highlighting to text chunks.
    
    Args:
        text: Text to highlight
        highlight_class: CSS class name for highlighting
        
    Returns:
        HTML string with highlighted text
    """
    if not text:
        return ""
    
    return f'<span class="{highlight_class}">{text}</span>'

def extract_metadata_from_filename(filename: str) -> dict:
    """
    Extract metadata from PDF filename using common naming patterns.
    
    Args:
        filename: PDF filename
        
    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        'subject': None,
        'year': None,
        'semester': None,
        'type': None
    }
    
    # Remove file extension
    name = Path(filename).stem.lower()
    
    # Extract year (4-digit number)
    year_match = re.search(r'\b(19|20)\d{2}\b', name)
    if year_match:
        metadata['year'] = year_match.group()
    
    # Extract semester
    semester_patterns = [
        r'\bsem[\s-]*([1-8])\b',
        r'\b([1-8])[\s-]*sem\b',
        r'\bsemester[\s-]*([1-8])\b'
    ]
    
    for pattern in semester_patterns:
        match = re.search(pattern, name)
        if match:
            metadata['semester'] = f"Semester {match.group(1)}"
            break
    
    # Extract common subject abbreviations
    subject_patterns = {
        'cs': 'Computer Science',
        'it': 'Information Technology',
        'ece': 'Electronics and Communication',
        'eee': 'Electrical and Electronics',
        'mech': 'Mechanical Engineering',
        'civil': 'Civil Engineering',
        'chem': 'Chemical Engineering',
        'math': 'Mathematics',
        'phys': 'Physics',
        'eng': 'Engineering'
    }
    
    for abbr, full_name in subject_patterns.items():
        if abbr in name:
            metadata['subject'] = full_name
            break
    
    # Extract document type
    type_patterns = {
        'pyq': 'Previous Year Questions',
        'notes': 'Study Notes',
        'lab': 'Laboratory Manual',
        'assign': 'Assignment',
        'quiz': 'Quiz',
        'exam': 'Examination'
    }
    
    for pattern, doc_type in type_patterns.items():
        if pattern in name:
            metadata['type'] = doc_type
            break
    
    return metadata

def validate_pdf_file(file_path: str) -> bool:
    """
    Validate if a file is a valid PDF.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if valid PDF, False otherwise
    """
    try:
        doc = fitz.open(file_path)
        is_valid = doc.page_count > 0
        doc.close()
        return is_valid
    except:
        return False

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"
