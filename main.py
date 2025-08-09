import streamlit as st
import os
import base64
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
import tempfile
from nltk.tokenize import sent_tokenize
import nltk
from dotenv import load_dotenv
import re
from pathlib import Path

# Import your custom modules
from database import SessionLocal, Base, engine
from models import PYQ, PDFHistory
import crud
from rag_pipeline import semantic_search_db, infer_subtopic
from utils import extract_text_from_pdf
from langchain_openai import ChatOpenAI
# Add this at the top of main.py after imports
def ensure_database_setup():
    """Ensure database tables are created"""
    try:
        from database import engine
        from models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Add default subjects if empty
        from database import SessionLocal
        from crud import get_subjects, create_subject
        
        db = SessionLocal()
        try:
            subjects = get_subjects(db)
            if not subjects:
                default_subjects = [
                    "Computer Science",
                    "Mathematics", 
                    "Physics",
                    "Chemistry",
                    "Biology"
                ]
                
                for subject_name in default_subjects:
                    create_subject(db, subject_name)
                    print(f"✅ Created subject: {subject_name}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database setup error: {e}")

# Call this function at the start of your Streamlit app
if __name__ == "__main__":
    ensure_database_setup()
    # Your existing main() function call


# Initialize database on startup
def init_database():
    """Initialize database tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"❌ Database initialization error: {e}")
        return False

# Safe OpenAI API key configuration
def setup_openai_key():
    """Setup OpenAI API key from secrets or environment"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
            os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
            return True
    except:
        pass
    
    # Try environment variable (for local development)
    if os.getenv("OPENAI_API_KEY"):
        return True
    
    # If neither found, show error
    st.error("🚨 OpenAI API key not found!")
    st.info("💡 **For local development:** Add OPENAI_API_KEY to your .env file")
    st.info("💡 **For deployment:** Add OPENAI_API_KEY in Streamlit secrets")
    st.stop()
    return False

# Function to set background image
def set_background_image():
    """Set background image for Streamlit app - works without image file"""
    # Try to find background image in common locations
    possible_paths = [
        "assets/back.png",
        "back.png", 
        os.path.join("assets", "back.png")
    ]
    
    image_found = False
    encoded_string = ""
    
    for image_path in possible_paths:
        if os.path.exists(image_path):
            try:
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                image_found = True
                break
            except Exception as e:
                continue
    
    # CSS for Dark Academia Style (works with or without background image)
    if image_found:
        background_style = f"background: linear-gradient(rgba(20,16,28,0.7), rgba(39,31,25,0.8)), url(data:image/png;base64,{encoded_string});"
    else:
        background_style = "background: linear-gradient(135deg, rgba(20,16,28,0.95), rgba(39,31,25,0.9));"
    
    background_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=Playfair+Display:wght@400;700&display=swap');
    
    .stApp {{
        {background_style}
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: #f4f1e8;
    }}
    
    /* Dark Academia Sidebar */
    .css-1d391kg, .css-6qob1r {{
        background: linear-gradient(135deg, rgba(39,31,25,0.95), rgba(20,16,28,0.95));
        border-right: 2px solid #8b7355;
        backdrop-filter: blur(15px);
        box-shadow: inset -1px 0 0 rgba(139,115,85,0.3);
    }}
    
    /* Main content area - Parchment-like */
    .block-container {{
        background: linear-gradient(135deg, rgba(44,37,29,0.92), rgba(60,50,40,0.88));
        border: 1px solid #8b7355;
        border-radius: 12px;
        padding: 30px;
        margin: 20px;
        box-shadow: 
            0 10px 40px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(139,115,85,0.2);
        backdrop-filter: blur(20px);
    }}
    
    /* Dark Academia Typography */
    h1 {{
        font-family: 'Playfair Display', serif;
        color: #d4af37;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.7);
        font-weight: 700;
        letter-spacing: 1px;
        text-align: center;
        margin-bottom: 30px;
        border-bottom: 2px solid #8b7355;
        padding-bottom: 15px;
    }}
    
    /* Headers and subheaders */
    h2, h3, h4 {{
        font-family: 'Playfair Display', serif;
        color: #c9a876;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}
    
    /* Body text styling */
    .stMarkdown, .stSelectbox label, .stFileUploader label, p {{
        font-family: 'Crimson Text', serif;
        color: #f4f1e8;
        font-size: 16px;
        line-height: 1.6;
    }}
    
    /* Buttons - Vintage leather look */
    .stButton > button {{
        background: linear-gradient(145deg, #8b4513, #654321);
        color: #f4f1e8;
        border: 2px solid #8b7355;
        border-radius: 8px;
        padding: 12px 24px;
        font-family: 'Crimson Text', serif;
        font-weight: 600;
        font-size: 16px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
        box-shadow: 
            0 4px 15px rgba(0,0,0,0.3),
            inset 0 1px 0 rgba(139,115,85,0.3);
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(145deg, #a0522d, #8b4513);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }}
    
    /* File uploader styling */
    .stFileUploader {{
        background: rgba(44,37,29,0.6);
        border: 2px dashed #8b7355;
        border-radius: 10px;
        padding: 20px;
    }}
    
    /* Selectbox styling */
    .stSelectbox > div > div {{
        background: rgba(44,37,29,0.9);
        border: 1px solid #8b7355;
        color: #f4f1e8;
    }}
    
    /* Progress bar - Antique gold */
    .stProgress .st-bo {{
        background-color: #d4af37;
    }}
    
    /* Info, error, success messages */
    .stAlert {{
        background: rgba(44,37,29,0.9);
        border-left: 4px solid #8b7355;
        color: #f4f1e8;
        border-radius: 8px;
    }}
    
    /* Sidebar text */
    .css-1d391kg .stMarkdown {{
        color: #f4f1e8;
    }}
    
    /* Question styling */
    .stMarkdown h4 {{
        color: #d4af37;
        border-left: 4px solid #8b7355;
        padding-left: 15px;
        margin: 15px 0;
    }}
    
    /* Highlighted answers */
    .stMarkdown span[style*="color:#90ee90"] {{
        color: #c9a876 !important;
        background: rgba(212,175,55,0.1);
        padding: 8px;
        border-radius: 6px;
        border-left: 3px solid #d4af37;
    }}
    
    /* Dividers */
    hr {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #8b7355, transparent);
        margin: 20px 0;
    }}
    
    /* Scrollbars */
    ::-webkit-scrollbar {{
        width: 12px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: rgba(44,37,29,0.3);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: #8b7355;
        border-radius: 6px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: #a0522d;
    }}
    </style>
    """
    
    st.markdown(background_css, unsafe_allow_html=True)
    
    # Show info if background image not found (only in sidebar to avoid clutter)
    if not image_found:
        with st.sidebar:
            st.info("💡 Add background image to assets/back.png for enhanced visuals")

def fuzzy_text_search(pdf_page, search_text, threshold=0.7):
    """Enhanced text search that handles minor variations and formatting differences"""
    # Clean search text
    clean_search = re.sub(r'\s+', ' ', search_text.strip())
    
    # Try exact search first
    exact_results = pdf_page.search_for(clean_search)
    if exact_results:
        return exact_results
    
    # Split into words and try partial matches
    words = clean_search.split()
    if len(words) > 3:  # For longer phrases, try smaller chunks
        results = []
        
        # Try combinations of 3-4 consecutive words
        for i in range(len(words) - 2):
            chunk = ' '.join(words[i:i+3])
            chunk_results = pdf_page.search_for(chunk)
            results.extend(chunk_results)
            
            if i < len(words) - 3:
                chunk = ' '.join(words[i:i+4])
                chunk_results = pdf_page.search_for(chunk)
                results.extend(chunk_results)
        
        return results
    
    # For shorter phrases, try individual words
    results = []
    for word in words:
        if len(word) > 3:  # Skip very short words
            word_results = pdf_page.search_for(word)
            results.extend(word_results)
    
    return results

def highlight_text_in_pdf(pdf_page, text_to_highlight):
    """Improved function to highlight text in PDF with better text matching"""
    if not text_to_highlight or text_to_highlight.strip() == "(Answer not found)":
        return False
    
    highlighted = False
    
    # Clean the text
    clean_text = re.sub(r'\s+', ' ', text_to_highlight.strip())
    
    # Try to highlight the full text first
    text_instances = fuzzy_text_search(pdf_page, clean_text)
    for rect in text_instances:
        try:
            highlight = pdf_page.add_highlight_annot(rect)
            highlight.set_colors(stroke=[1, 1, 0])  # Yellow
            highlight.update()
            highlighted = True
        except Exception:
            continue
    
    # If full text highlighting failed, try sentence by sentence
    if not highlighted:
        try:
            sentences = sent_tokenize(clean_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 15:  # Only highlight substantial sentences
                    sentence_instances = fuzzy_text_search(pdf_page, sentence)
                    for rect in sentence_instances:
                        try:
                            highlight = pdf_page.add_highlight_annot(rect)
                            highlight.set_colors(stroke=[1, 1, 0])  # Yellow
                            highlight.update()
                            highlighted = True
                        except Exception:
                            continue
        except Exception:
            pass
    
    # If sentence highlighting failed, try key phrases
    if not highlighted:
        # Extract key phrases (noun phrases, important terms)
        words = clean_text.split()
        if len(words) > 4:
            # Try highlighting chunks of 3-5 words
            for i in range(0, len(words) - 2, 2):
                phrase = ' '.join(words[i:i+4])
                phrase_instances = fuzzy_text_search(pdf_page, phrase)
                for rect in phrase_instances:
                    try:
                        highlight = pdf_page.add_highlight_annot(rect)
                        highlight.set_colors(stroke=[1, 0.8, 0])  # Slightly orange yellow
                        highlight.update()
                        highlighted = True
                    except Exception:
                        continue
    
    return highlighted

# Initialize app
def main():
    """Main application function"""
    
    # Setup
    load_dotenv()
    
    # Initialize database
    if not init_database():
        st.stop()
    
    # Setup API key
    if not setup_openai_key():
        st.stop()
    
    # Download NLTK data
    try:
        nltk.download('punkt', quiet=True)
    except:
        pass

    # Streamlit UI setup
    st.set_page_config(page_title="IntelliJect", layout="wide")
    
    # Set background
    set_background_image()
    
    # Title
    st.title("📄 IntelliJect - Intelligent Integration of PYQ's into notes")
    
    # Get available subjects from database
    try:
        with SessionLocal() as db:
            available_subjects = db.query(PYQ.subject).distinct().all()
            subjects = [subject[0] for subject in available_subjects] if available_subjects else []
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        subjects = []
    
    if not subjects:
        st.warning("⚠️ No subjects found in database.")
        st.info("💡 Upload some PYQ data first or run the data loader script.")
        # Allow app to continue - user might be testing
        subjects = ["Demo Subject"]  # Fallback for testing
    
    # Main UI layout
    col1, col2 = st.columns(2)
    
    with col1:
        pdf_file = st.file_uploader("📑 Upload Notes PDF", type=["pdf"])
    
    with col2:
        selected_subject = st.selectbox("📚 Select Subject", subjects)
    
    # Sidebar for history
    with st.sidebar:
        st.markdown("## 📋 Recent Uploads")
        try:
            with SessionLocal() as db:
                recent_uploads = crud.get_pdf_history(db)[:5]
                if recent_uploads:
                    for upload in recent_uploads:
                        st.text(f"📄 {upload.filename[:20]}...")
                        st.caption(f"Subject: {upload.subject}")
                else:
                    st.info("No upload history yet")
        except Exception as e:
            st.error(f"Error loading history: {e}")
    
    # Main processing
    if st.button("🚀 Match PYQs"):
        if not pdf_file:
            st.error("❌ Please upload a Notes PDF.")
            st.stop()
    
        with st.spinner("Processing..."):
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_file.read())
                temp_pdf_path = tmp_file.name
    
            # Extract text from PDF
            try:
                pages_text = extract_text_from_pdf(temp_pdf_path)
            except Exception as e:
                st.error(f"❌ Could not extract text from PDF: {e}")
                os.unlink(temp_pdf_path)  # Cleanup
                st.stop()
                
            if not pages_text:
                st.error("❌ Could not extract text from PDF.")
                os.unlink(temp_pdf_path)  # Cleanup
                st.stop()
    
            # Initialize
            db_session = SessionLocal()
            
            try:
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            except Exception as e:
                st.error(f"❌ OpenAI configuration error: {e}")
                db_session.close()
                os.unlink(temp_pdf_path)
                st.stop()
    
            pdf_doc = fitz.open(temp_pdf_path)
            total_pages = len(pages_text)
    
            # Progress bar
            progress_bar = st.progress(0)
            
            # Cache for highlights
            highlight_cache = {}
            highlighted_pages = {}  # Track which pages have highlights
    
            def highlight_answer(note_text, question):
                cache_key = (note_text[:100], question[:50])
                if cache_key in highlight_cache:
                    return highlight_cache[cache_key]
                
                prompt = f"""
You are reading a note and a past year question. Identify the sentence(s) from the note that best answer the question.

Question:
"{question}"

Note:
\"\"\"{note_text[:2000]}\"\"\"

Instructions:
- Return ONLY the most relevant sentence(s) from the note that answer the question
- Use the EXACT wording from the note
- Do NOT rephrase or explain
- Do NOT include the question again
- If no relevant answer exists, return "Answer not found"
"""
                try:
                    result = llm.invoke(prompt).content.strip()
                    # Clean up the result
                    if result and not result.startswith("Answer not found"):
                        # Remove quotes if LLM added them
                        result = result.strip('"').strip("'")
                    highlight_cache[cache_key] = result
                    return result
                except Exception as e:
                    print(f"Error in highlight_answer: {e}")
                    return "Answer not found"
    
            st.info("🔍 Processing pages and highlighting answers...")
    
            # Process each page - FIRST PASS: Add all highlights
            for page_idx, page_text in enumerate(pages_text):
                progress = int(((page_idx + 1) / (total_pages * 2)) * 100)  # First half of progress
                progress_bar.progress(progress)
                
                if not page_text.strip():
                    continue
    
                # Get relevant PYQs for this page
                try:
                    relevant_docs = semantic_search_db(db_session, page_text, selected_subject, k=3)
                except Exception as e:
                    print(f"Error in semantic search for page {page_idx + 1}: {e}")
                    relevant_docs = []
    
                # Highlight answers in PDF
                if relevant_docs:
                    pdf_page = pdf_doc[page_idx]
                    page_highlighted = False
                    
                    for doc in relevant_docs:
                        question = doc.page_content
                        highlighted_text = highlight_answer(page_text, question)
                        
                        if highlighted_text and highlighted_text != "Answer not found":
                            # Try to highlight the text in PDF
                            success = highlight_text_in_pdf(pdf_page, highlighted_text)
                            if success:
                                page_highlighted = True
                    
                    highlighted_pages[page_idx] = page_highlighted
    
            st.success("✅ Highlighting completed! Now displaying results...")
    
            # SECOND PASS: Display results with highlighted PDFs
            for page_idx, page_text in enumerate(pages_text):
                progress = int(((page_idx + 1 + total_pages) / (total_pages * 2)) * 100)  # Second half
                progress_bar.progress(progress)
                
                # Get subtopic for this page
                try:
                    subtopic = infer_subtopic(page_text[:1000])
                except:
                    subtopic = "General"
    
                # Get relevant PYQs (same as before)
                try:
                    relevant_docs = semantic_search_db(db_session, page_text, selected_subject, k=3)
                except:
                    relevant_docs = []
    
                # Display page results
                col_img, col_pyqs = st.columns([1.2, 1])
                
                with col_img:
                    # Render PDF page with highlights
                    try:
                        pdf_page = pdf_doc[page_idx]
                        pix = pdf_page.get_pixmap(dpi=150)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        
                        img_bytes = BytesIO()
                        img.save(img_bytes, format="PNG")
                        img_bytes.seek(0)
                        
                        # Show highlighting status
                        highlight_status = "🟡 Highlighted" if highlighted_pages.get(page_idx, False) else "⚪ No highlights"
                        st.image(
                            img_bytes, 
                            caption=f"📄 Page {page_idx + 1} - {subtopic} ({highlight_status})", 
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"Could not render page {page_idx + 1}: {e}")
    
                with col_pyqs:
                    st.markdown(f"### 🔍 Relevant PYQs (Page {page_idx + 1}):")
                    if relevant_docs:
                        for i, qdoc in enumerate(relevant_docs, 1):
                            with st.expander(f"Question {i}", expanded=True):
                                st.markdown(f"**❓ Question:** {qdoc.page_content}")
                                metadata = qdoc.metadata
                                st.markdown(
                                    f"**📊 Details:** "
                                    f"Topic: `{metadata.get('sub_topic', 'N/A')}` | "
                                    f"Marks: `{metadata.get('marks', 'N/A')}` | "
                                    f"Year: `{metadata.get('year', 'N/A')}`"
                                )
                                
                                # Get and display highlighted answer
                                highlight = highlight_answer(page_text, qdoc.page_content)
                                
                                if highlight and highlight != "Answer not found":
                                    st.markdown(
                                        f'<div style="background: rgba(212,175,55,0.1); padding: 10px; '
                                        f'border-radius: 6px; border-left: 3px solid #d4af37; margin: 10px 0;">'
                                        f'<strong>💡 Highlighted Answer:</strong><br>{highlight}'
                                        f'</div>', 
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.info("❗ No specific answer found in this section")
                    else:
                        st.info("❗ No relevant PYQs found for this page.")
                
                st.divider()
    
            # Add to history
            try:
                crud.add_pdf_history(db_session, pdf_file.name, selected_subject)
                db_session.commit()
            except Exception as e:
                print(f"Error adding to history: {e}")
    
            # Cleanup
            db_session.close()
            pdf_doc.close()
            os.unlink(temp_pdf_path)
            progress_bar.progress(100)
            
            # Summary
            total_highlighted = sum(highlighted_pages.values())
            st.success(f"✅ Processing Complete! Highlighted answers found on {total_highlighted}/{total_pages} pages.")

if __name__ == "__main__":
    ensure_database_setup()  
    main()