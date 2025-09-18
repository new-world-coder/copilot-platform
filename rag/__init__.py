"""
RAG (Retrieval-Augmented Generation) module for the Copilot Platform.

This module provides:
- Document embedding using sentence-transformers
- FAISS-based document indexing and retrieval
- Legal document processing and citation generation
"""

from .embedder import Embedder
from .indexer import DocumentIndexer
from .retriever import DocumentRetriever, create_retriever

__all__ = [
    "Embedder",
    "DocumentIndexer", 
    "DocumentRetriever",
    "create_retriever"
]