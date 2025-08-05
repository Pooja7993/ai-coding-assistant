"""
Memory management module for RAG (Retrieval-Augmented Generation) functionality.
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import json
import re

logger = logging.getLogger(__name__)


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add documents to the memory."""
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from memory."""
        pass


class SimpleMemoryBackend(MemoryBackend):
    """Simple in-memory backend for text similarity search using keyword matching."""
    
    def __init__(self):
        self.documents = []
        self.metadata = []
        
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add documents to the simple memory."""
        if not documents:
            return
            
        # Store documents and metadata
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))
            
        logger.info(f"Added {len(documents)} documents to memory. Total: {len(self.documents)}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using simple keyword matching."""
        if len(self.documents) == 0:
            return []
            
        # Simple keyword-based scoring
        query_words = set(query.lower().split())
        scored_docs = []
        
        for i, doc in enumerate(self.documents):
            doc_words = set(re.findall(r'\w+', doc.lower()))
            # Calculate simple overlap score
            common_words = query_words.intersection(doc_words)
            score = len(common_words) / max(len(query_words), 1)
            
            if score > 0:  # Only include documents with some relevance
                scored_docs.append((score, i, doc))
        
        # Sort by score (descending) and take top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for i, (score, idx, doc) in enumerate(scored_docs[:k]):
            result = {
                'document': doc,
                'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                'score': score,
                'rank': i + 1
            }
            results.append(result)
        
        return results
    
    def clear(self) -> None:
        """Clear all documents from memory."""
        self.documents = []
        self.metadata = []
        logger.info("Cleared all documents from memory")


class RAGMemory:
    """Main RAG Memory interface that handles different backends."""
    
    def __init__(self, backend_type: str = "simple"):
        if backend_type == "simple":
            self.backend = SimpleMemoryBackend()
        else:
            # Fallback to simple backend if others not available
            logger.warning(f"Backend {backend_type} not available, using simple backend")
            self.backend = SimpleMemoryBackend()
        
        self.max_size = 1000  # Default max size
        logger.info(f"Initialized RAG memory with {backend_type} backend")
    
    def add_conversation(self, user_message: str, assistant_response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a conversation to memory."""
        conversation = f"User: {user_message}\nAssistant: {assistant_response}"
        metadata = metadata or {}
        metadata.update({
            'type': 'conversation',
            'user_message': user_message,
            'assistant_response': assistant_response
        })
        
        self.backend.add_documents([conversation], [metadata])
    
    def add_code_context(self, code: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add code context to memory."""
        document = f"Code: {code}\nDescription: {description}"
        metadata = metadata or {}
        metadata.update({
            'type': 'code_context',
            'code': code,
            'description': description
        })
        
        self.backend.add_documents([document], [metadata])
    
    def search_relevant_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant context based on query."""
        return self.backend.search(query, k)
    
    def clear_memory(self) -> None:
        """Clear all memory."""
        self.backend.clear()


# Global memory instance
memory = RAGMemory()