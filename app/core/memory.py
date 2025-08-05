"""
Enhanced memory management module with FAISS + Redis hybrid support.
Provides semantic search capabilities and fast short-term state management.
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import json
import re
import pickle
import hashlib

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


class FAISMemoryBackend(MemoryBackend):
    """FAISS-based vector similarity search backend."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.embedding_model_name = embedding_model
        self.dimension = dimension
        self.documents = []
        self.metadata = []
        self.index = None
        self.model = None
        
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
            
            # Initialize FAISS index
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Initialize embedding model
            self.model = SentenceTransformer(embedding_model)
            logger.info(f"Initialized FAISS backend with {embedding_model}")
            
        except ImportError as e:
            logger.error(f"FAISS dependencies not available: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add documents to FAISS index."""
        if not documents or not self.model:
            return
        
        # Generate embeddings
        embeddings = self.model.encode(documents, normalize_embeddings=True)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store documents and metadata
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))
        
        logger.info(f"Added {len(documents)} documents to FAISS index. Total: {len(self.documents)}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search using FAISS vector similarity."""
        if not self.model or len(self.documents) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        
        # Search FAISS index
        scores, indices = self.index.search(query_embedding, min(k, len(self.documents)))
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx >= 0:  # Valid index
                result = {
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                    'score': float(score),
                    'rank': i + 1
                }
                results.append(result)
        
        return results
    
    def clear(self) -> None:
        """Clear FAISS index and documents."""
        if self.index:
            self.index.reset()
        self.documents = []
        self.metadata = []
        logger.info("Cleared FAISS index and documents")


class HybridMemoryBackend(MemoryBackend):
    """Hybrid memory backend combining FAISS for semantic search and Redis for fast state."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", redis_url: str = "redis://localhost:6379/0"):
        self.faiss_backend = None
        self.redis_client = None
        self.redis_url = redis_url
        
        # Initialize FAISS backend
        try:
            self.faiss_backend = FAISMemoryBackend(embedding_model)
        except Exception as e:
            logger.warning(f"FAISS backend not available, using simple backend: {e}")
            self.faiss_backend = SimpleMemoryBackend()
        
        # Initialize Redis client
        try:
            import redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for hybrid memory")
        except Exception as e:
            logger.warning(f"Redis not available for hybrid memory: {e}")
    
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add documents to both FAISS and Redis."""
        # Add to FAISS for semantic search
        self.faiss_backend.add_documents(documents, metadata)
        
        # Add to Redis for fast access (last N documents)
        if self.redis_client:
            try:
                for i, doc in enumerate(documents):
                    doc_id = hashlib.md5(doc.encode()).hexdigest()
                    doc_data = {
                        'content': doc,
                        'metadata': metadata[i] if metadata and i < len(metadata) else {},
                        'timestamp': 'now'  # In production, use proper timestamp
                    }
                    
                    # Store in Redis with expiration (24 hours)
                    self.redis_client.setex(
                        f"doc:{doc_id}", 
                        86400,  # 24 hours
                        json.dumps(doc_data)
                    )
                    
                    # Add to recent documents list
                    self.redis_client.lpush("recent_docs", doc_id)
                    self.redis_client.ltrim("recent_docs", 0, 999)  # Keep last 1000
                    
            except Exception as e:
                logger.warning(f"Failed to add documents to Redis: {e}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search using FAISS, with Redis for recent documents boost."""
        # Get FAISS results
        faiss_results = self.faiss_backend.search(query, k)
        
        # If Redis is available, boost recent documents
        if self.redis_client:
            try:
                # Get recent document IDs
                recent_doc_ids = self.redis_client.lrange("recent_docs", 0, 49)  # Last 50
                
                # Check if query matches recent documents
                query_lower = query.lower()
                recent_matches = []
                
                for doc_id in recent_doc_ids:
                    doc_data_str = self.redis_client.get(f"doc:{doc_id}")
                    if doc_data_str:
                        doc_data = json.loads(doc_data_str)
                        if query_lower in doc_data['content'].lower():
                            recent_matches.append({
                                'document': doc_data['content'],
                                'metadata': doc_data['metadata'],
                                'score': 0.9,  # High score for recent matches
                                'rank': 0,
                                'source': 'redis_recent'
                            })
                
                # Combine results, prioritizing recent matches
                combined_results = recent_matches + faiss_results
                
                # Re-rank and limit
                seen_docs = set()
                final_results = []
                
                for result in combined_results:
                    doc_hash = hashlib.md5(result['document'].encode()).hexdigest()
                    if doc_hash not in seen_docs and len(final_results) < k:
                        seen_docs.add(doc_hash)
                        result['rank'] = len(final_results) + 1
                        final_results.append(result)
                
                return final_results
                
            except Exception as e:
                logger.warning(f"Failed to use Redis for search boost: {e}")
        
        return faiss_results
    
    def clear(self) -> None:
        """Clear both FAISS and Redis."""
        self.faiss_backend.clear()
        
        if self.redis_client:
            try:
                # Clear recent documents
                self.redis_client.delete("recent_docs")
                
                # Clear document data (scan and delete)
                for key in self.redis_client.scan_iter(match="doc:*"):
                    self.redis_client.delete(key)
                    
                logger.info("Cleared Redis memory data")
            except Exception as e:
                logger.warning(f"Failed to clear Redis: {e}")


class RAGMemory:
    """Enhanced RAG Memory interface with hybrid backend support."""
    
    def __init__(self, backend_type: str = "simple"):
        self.backend_type = backend_type
        
        if backend_type == "faiss":
            try:
                self.backend = FAISMemoryBackend()
            except Exception as e:
                logger.warning(f"FAISS backend not available: {e}, falling back to simple")
                self.backend = SimpleMemoryBackend()
        elif backend_type == "hybrid":
            try:
                from app.core.config import settings
                self.backend = HybridMemoryBackend(redis_url=settings.redis_url)
            except Exception as e:
                logger.warning(f"Hybrid backend not available: {e}, falling back to simple")
                self.backend = SimpleMemoryBackend()
        else:
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "backend_type": self.backend_type,
            "backend_class": self.backend.__class__.__name__,
            "document_count": len(getattr(self.backend, 'documents', [])),
            "max_size": self.max_size
        }


# Global memory instance - now uses hybrid by default if available
from app.core.config import settings
memory = RAGMemory(settings.memory_type)