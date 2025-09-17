"""
Retrieval service for RAG
"""

from typing import List, Dict, Any
import logging
from .embedding_service import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for retrieving relevant documents"""
    
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def retrieve(self, query: str, collection_name: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for query"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            # Query vector store
            results = self.vector_store.query(
                collection_name=collection_name,
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'document': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'id': results['ids'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            raise
