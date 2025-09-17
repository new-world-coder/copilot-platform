"""
Vector store for storing and retrieving embeddings
"""

import chromadb
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./data/vector_store"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collections = {}
    
    def create_collection(self, name: str, metadata: Optional[Dict] = None):
        """Create a new collection"""
        try:
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            self.collections[name] = collection
            return collection
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            raise
    
    def get_collection(self, name: str):
        """Get existing collection"""
        if name not in self.collections:
            self.collections[name] = self.client.get_collection(name)
        return self.collections[name]
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     embeddings: List[List[float]], metadatas: List[Dict] = None,
                     ids: List[str] = None):
        """Add documents to collection"""
        collection = self.get_collection(collection_name)
        
        try:
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas or [{}] * len(documents),
                ids=ids or [f"doc_{i}" for i in range(len(documents))]
            )
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def query(self, collection_name: str, query_embeddings: List[List[float]], 
              n_results: int = 5, where: Optional[Dict] = None) -> Dict[str, Any]:
        """Query collection for similar documents"""
        collection = self.get_collection(collection_name)
        
        try:
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            raise
