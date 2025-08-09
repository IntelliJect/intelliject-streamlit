"""
RAG (Retrieval-Augmented Generation) pipeline for IntelliJect.
Implements semantic search, subtopic inference, and PYQ matching functionality.
"""
import os
from typing import List, Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from sqlalchemy.orm import Session
from models import PYQ

# Load environment variables
load_dotenv()

class RAGPipeline:
    """Main RAG pipeline class for PYQ processing."""
    
    def __init__(self):
        """Initialize embeddings and LLM."""
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    
    def load_vectorstore_from_db(self, session: Session, subject: str = None) -> Optional[FAISS]:
        """
        Dynamically builds a FAISS vectorstore from PYQs stored in the database.
        
        Args:
            session: Database session
            subject: Optional subject filter
            
        Returns:
            FAISS vectorstore or None if no PYQs found
        """
        query_set = session.query(PYQ)
        if subject:
            query_set = query_set.filter(PYQ.subject == subject)
        
        pyqs = query_set.all()
        if not pyqs:
            return None
        
        # Convert PYQs to documents
        documents = [
            Document(
                page_content=pyq.question,
                metadata={
                    "year": pyq.year,
                    "subject": pyq.subject,
                    "sub_topic": pyq.sub_topic,
                    "marks": pyq.marks,
                    "semester": pyq.semester,
                    "branch": pyq.branch,
                    "unit": pyq.unit
                }
            )
            for pyq in pyqs
        ]
        
        try:
            vectorstore = FAISS.from_documents(documents, self.embeddings)
            return vectorstore
        except Exception as e:
            print(f"❌ Error creating vectorstore: {e}")
            return None
    
    def semantic_search_db(self, session: Session, query: str, subject: str = None, k: int = 5) -> List[Document]:
        """
        Perform semantic search over PYQs stored in the database using FAISS.
        
        Args:
            session: Database session
            query: Search query text
            subject: Optional subject filter
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        vectorstore = self.load_vectorstore_from_db(session, subject)
        if not vectorstore:
            return []
        
        try:
            results = vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Semantic search error: {e}")
            return []
    
    def infer_subtopic(self, text: str) -> str:
        """
        Infer subtopic from given text using OpenAI LLM.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Inferred subtopic string
        """
        prompt = (
            f"Read the following academic content and suggest the most relevant subtopic "
            f"(like 'Firewall', 'Water Pollution', etc.) in 2-3 words:\n\n{text}\n\nSubtopic:"
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"❌ Subtopic inference failed: {e}")
            return "General"
    
    def get_relevant_pyqs(self, session: Session, query: str, subject: str = None, k: int = 3) -> List[Document]:
        """
        Get relevant PYQs from database using semantic similarity search.
        
        Args:
            session: Database session
            query: Search query
            subject: Optional subject filter
            k: Number of results to return
            
        Returns:
            List of relevant PYQ documents
        """
        return self.semantic_search_db(session, query, subject, k)
    
    def nlp_chunk_text(self, text: str, max_sentences: int = 5) -> List[str]:
        """
        Simple text chunking by sentence count.
        
        Args:
            text: Input text to chunk
            max_sentences: Maximum sentences per chunk
            
        Returns:
            List of text chunks
        """
        try:
            import nltk
            from nltk.tokenize import sent_tokenize
            
            sentences = sent_tokenize(text)
            chunks = []
            
            for i in range(0, len(sentences), max_sentences):
                chunk = ' '.join(sentences[i:i + max_sentences])
                chunks.append(chunk)
            
            return chunks
        except Exception as e:
            print(f"❌ Text chunking error: {e}")
            # Fallback: simple splitting
            chunk_size = 1000
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    
    def process_notes_and_match_pyqs(self, text: str, subject: str, session: Session, k: int = 3) -> List[dict]:
        """
        Process notes text: chunk, infer subtopic, and get matching PYQs from database.
        
        Args:
            text: Notes text to process
            subject: Subject for filtering PYQs
            session: Database session
            k: Number of matches per chunk
            
        Returns:
            List of processing results with chunks, subtopics, and matches
        """
        chunks = self.nlp_chunk_text(text)
        results = []
        
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            subtopic = self.infer_subtopic(chunk)
            matches = self.get_relevant_pyqs(session, chunk, subject, k=k)
            
            results.append({
                "chunk": chunk,
                "subtopic": subtopic,
                "matches": matches,
                "match_count": len(matches)
            })
        
        return results

# Initialize global RAG pipeline instance
rag_pipeline = RAGPipeline()

# Backward compatibility functions
def load_vectorstore_from_db(session: Session, subject: str = None) -> Optional[FAISS]:
    """Backward compatibility wrapper."""
    return rag_pipeline.load_vectorstore_from_db(session, subject)

def semantic_search_db(session: Session, query: str, subject: str = None, k: int = 5) -> List[Document]:
    """Backward compatibility wrapper."""
    return rag_pipeline.semantic_search_db(session, query, subject, k)

def infer_subtopic(text: str) -> str:
    """Backward compatibility wrapper."""
    return rag_pipeline.infer_subtopic(text)

def get_relevant_pyqs(session: Session, query: str, subject: str = None, k: int = 3) -> List[Document]:
    """Backward compatibility wrapper."""
    return rag_pipeline.get_relevant_pyqs(session, query, subject, k)

def nlp_chunk_text(text: str, max_sentences: int = 5) -> List[str]:
    """Backward compatibility wrapper."""
    return rag_pipeline.nlp_chunk_text(text, max_sentences)

def process_notes_and_match_pyqs(text: str, subject: str, session: Session, k: int = 3) -> List[dict]:
    """Backward compatibility wrapper."""
    return rag_pipeline.process_notes_and_match_pyqs(text, subject, session, k)
