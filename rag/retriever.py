"""
RAG Retriever Module
Handles query retrieval from FAISS index with similarity scores
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from embedder import Embedder
from indexer import DocumentIndexer

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Retrieves relevant documents from FAISS index"""
    
    def __init__(self, index_path: str, metadata_path: str, embedder: Embedder):
        """
        Initialize the retriever
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
            embedder: Embedder instance for query embedding
        """
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embedder = embedder
        self.indexer = None
        
        # Load index and metadata
        self._load_index()
    
    def _load_index(self):
        """Load the FAISS index and metadata"""
        try:
            # Create indexer instance
            self.indexer = DocumentIndexer(self.embedder, "flat")  # Type doesn't matter for loading
            
            # Load index and metadata
            self.indexer.load_index(self.index_path, self.metadata_path)
            
            logger.info(f"Retriever loaded successfully. Documents: {len(self.indexer.documents)}")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Query text
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of relevant documents with similarity scores
        """
        try:
            # Search the index
            results = self.indexer.search(query, top_k)
            
            # Filter by minimum score
            filtered_results = [
                result for result in results 
                if result['similarity_score'] >= min_score
            ]
            
            logger.info(f"Retrieved {len(filtered_results)} documents for query: '{query[:50]}...'")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            raise
    
    def retrieve_with_context(self, query: str, top_k: int = 3, context_window: int = 200) -> List[Dict[str, Any]]:
        """
        Retrieve documents with additional context information
        
        Args:
            query: Query text
            top_k: Number of results to return
            context_window: Number of characters to include around matches
            
        Returns:
            List of documents with enhanced context
        """
        results = self.retrieve(query, top_k)
        
        enhanced_results = []
        for result in results:
            enhanced_result = result.copy()
            
            # Add context information
            enhanced_result['context'] = {
                'query': query,
                'retrieval_timestamp': self._get_timestamp(),
                'context_window': context_window
            }
            
            # Add text preview
            text = result['text']
            if len(text) > context_window:
                enhanced_result['text_preview'] = text[:context_window] + "..."
            else:
                enhanced_result['text_preview'] = text
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    def retrieve_by_source(self, query: str, source_pattern: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve documents filtered by source pattern
        
        Args:
            query: Query text
            source_pattern: Pattern to match in source field
            top_k: Number of results to return
            
        Returns:
            List of documents from matching sources
        """
        results = self.retrieve(query, top_k * 2)  # Get more results to filter
        
        filtered_results = [
            result for result in results
            if source_pattern.lower() in result.get('source', '').lower()
        ]
        
        return filtered_results[:top_k]
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        if 0 <= doc_id < len(self.indexer.documents):
            return self.indexer.documents[doc_id]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            'total_documents': len(self.indexer.documents),
            'index_path': self.index_path,
            'metadata_path': self.metadata_path,
            'embedding_model': self.embedder.model_name,
            'embedding_dimension': self.embedder.get_embedding_dimension()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


def create_retriever(
    index_dir: str = "data/vector_store",
    model_name: str = "all-MiniLM-L6-v2"
) -> DocumentRetriever:
    """
    Create a retriever instance
    
    Args:
        index_dir: Directory containing index files
        model_name: Embedding model name
        
    Returns:
        DocumentRetriever instance
    """
    index_path = os.path.join(index_dir, "faiss_index.bin")
    metadata_path = os.path.join(index_dir, "metadata.json")
    
    # Check if files exist
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file not found: {index_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    # Create embedder
    embedder = Embedder(model_name)
    
    # Create retriever
    retriever = DocumentRetriever(index_path, metadata_path, embedder)
    
    return retriever


def retrieve(query: str, top_k: int = 3, index_dir: str = "data/vector_store") -> List[Dict[str, Any]]:
    """
    Quick function to retrieve documents
    
    Args:
        query: Query text
        top_k: Number of results to return
        index_dir: Directory containing index files
        
    Returns:
        List of relevant documents
    """
    retriever = create_retriever(index_dir)
    return retriever.retrieve(query, top_k)


def retrieve_with_scores(query: str, top_k: int = 3, index_dir: str = "data/vector_store") -> List[Tuple[Dict[str, Any], float]]:
    """
    Retrieve documents with explicit similarity scores
    
    Args:
        query: Query text
        top_k: Number of results to return
        index_dir: Directory containing index files
        
    Returns:
        List of (document, score) tuples
    """
    retriever = create_retriever(index_dir)
    results = retriever.retrieve(query, top_k)
    
    return [(result, result['similarity_score']) for result in results]


# Legal-specific retrieval functions
def retrieve_legal_documents(query: str, top_k: int = 3, index_dir: str = "data/vector_store") -> List[Dict[str, Any]]:
    """
    Retrieve legal documents with enhanced context
    
    Args:
        query: Legal query
        top_k: Number of results
        index_dir: Index directory
        
    Returns:
        List of legal documents with citations
    """
    retriever = create_retriever(index_dir)
    results = retriever.retrieve_with_context(query, top_k)
    
    # Add legal-specific metadata
    for result in results:
        result['legal_citation'] = {
            'source': result['source'],
            'similarity_score': result['similarity_score'],
            'retrieval_method': 'semantic_search'
        }
    
    return results


def retrieve_case_law(query: str, top_k: int = 3, index_dir: str = "data/vector_store") -> List[Dict[str, Any]]:
    """
    Retrieve case law documents specifically
    
    Args:
        query: Case law query
        top_k: Number of results
        index_dir: Index directory
        
    Returns:
        List of case law documents
    """
    retriever = create_retriever(index_dir)
    
    # Search for case law sources
    case_results = retriever.retrieve_by_source(query, "case", top_k)
    
    # If no case-specific results, fall back to general search
    if not case_results:
        case_results = retriever.retrieve(query, top_k)
    
    return case_results


def retrieve_contracts(query: str, top_k: int = 3, index_dir: str = "data/vector_store") -> List[Dict[str, Any]]:
    """
    Retrieve contract documents specifically
    
    Args:
        query: Contract query
        top_k: Number of results
        index_dir: Index directory
        
    Returns:
        List of contract documents
    """
    retriever = create_retriever(index_dir)
    
    # Search for contract sources
    contract_results = retriever.retrieve_by_source(query, "contract", top_k)
    
    # If no contract-specific results, fall back to general search
    if not contract_results:
        contract_results = retriever.retrieve(query, top_k)
    
    return contract_results


if __name__ == "__main__":
    # Test the retriever
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Create retriever
        retriever = create_retriever()
        
        print("Testing retriever...")
        print(f"Stats: {retriever.get_stats()}")
        
        # Test queries
        test_queries = [
            "contract termination clause",
            "liability limitation",
            "intellectual property rights",
            "dispute resolution"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = retriever.retrieve(query, top_k=2)
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result['similarity_score']:.4f}")
                print(f"     Source: {result['source']}")
                print(f"     Text: {result['text'][:100]}...")
                print()
        
        print("✅ Retriever test completed successfully!")
        
    except Exception as e:
        print(f"❌ Retriever test failed: {e}")
        sys.exit(1)
