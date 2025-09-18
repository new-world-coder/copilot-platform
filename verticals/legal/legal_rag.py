"""
Legal RAG Module
Specialized RAG system for legal documents with citation support
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Import RAG components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from rag.embedder import Embedder
from rag.indexer import DocumentIndexer, load_documents_from_directory
from rag.retriever import DocumentRetriever

logger = logging.getLogger(__name__)


class LegalRAG:
    """Legal-specific RAG system with citation support"""
    
    def __init__(self, 
                 legal_data_dir: str = "verticals/legal/datasets",
                 index_dir: str = "data/legal_vector_store",
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize Legal RAG system
        
        Args:
            legal_data_dir: Directory containing legal datasets
            index_dir: Directory to store/load FAISS index
            model_name: Embedding model name
        """
        self.legal_data_dir = legal_data_dir
        self.index_dir = index_dir
        self.model_name = model_name
        
        # Create directories
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.embedder = Embedder(model_name)
        self.indexer = None
        self.retriever = None
        
        # Legal document metadata
        self.document_types = {
            'case_law': 'Case Law',
            'statutes': 'Statutes',
            'contracts': 'Contracts'
        }
        
        # Load or create index
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or load the legal document index"""
        index_path = os.path.join(self.index_dir, "legal_faiss_index.bin")
        metadata_path = os.path.join(self.index_dir, "legal_metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            logger.info("Loading existing legal document index...")
            self._load_index(index_path, metadata_path)
        else:
            logger.info("Creating new legal document index...")
            self._build_index()
    
    def _load_index(self, index_path: str, metadata_path: str):
        """Load existing index"""
        try:
            self.retriever = DocumentRetriever(index_path, metadata_path, self.embedder)
            logger.info(f"Legal index loaded successfully. Documents: {len(self.retriever.indexer.documents)}")
        except Exception as e:
            logger.error(f"Error loading legal index: {e}")
            logger.info("Rebuilding index...")
            self._build_index()
    
    def _build_index(self):
        """Build index from legal documents"""
        try:
            # Load all legal documents
            all_documents = []
            
            for doc_type, doc_type_name in self.document_types.items():
                doc_dir = os.path.join(self.legal_data_dir, doc_type)
                if os.path.exists(doc_dir):
                    docs = load_documents_from_directory(doc_dir)
                    
                    # Add legal-specific metadata
                    for doc in docs:
                        doc['legal_type'] = doc_type
                        doc['legal_type_name'] = doc_type_name
                        doc['indexed_date'] = datetime.now().isoformat()
                    
                    all_documents.extend(docs)
                    logger.info(f"Loaded {len(docs)} {doc_type_name} documents")
            
            if not all_documents:
                logger.warning("No legal documents found to index")
                return
            
            # Create indexer
            self.indexer = DocumentIndexer(self.embedder, "flat")
            
            # Add documents to index
            self.indexer.add_documents(all_documents)
            
            # Save index
            index_path = os.path.join(self.index_dir, "legal_faiss_index.bin")
            metadata_path = os.path.join(self.index_dir, "legal_metadata.json")
            self.indexer.save_index(index_path, metadata_path)
            
            # Create retriever
            self.retriever = DocumentRetriever(index_path, metadata_path, self.embedder)
            
            logger.info(f"Legal index built successfully. Total documents: {len(all_documents)}")
            
        except Exception as e:
            logger.error(f"Error building legal index: {e}")
            raise
    
    def query_legal_docs(self, 
                        query: str, 
                        top_k: int = 3, 
                        doc_types: Optional[List[str]] = None,
                        min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Query legal documents with citation support
        
        Args:
            query: Legal query
            top_k: Number of results to return
            doc_types: Filter by document types (case_law, statutes, contracts)
            min_score: Minimum similarity score
            
        Returns:
            List of legal documents with citations
        """
        if not self.retriever:
            logger.error("Legal RAG system not initialized")
            return []
        
        try:
            # Get base results
            results = self.retriever.retrieve(query, top_k * 2, min_score)  # Get more to filter
            
            # Filter by document types if specified
            if doc_types:
                filtered_results = [
                    result for result in results
                    if result.get('legal_type') in doc_types
                ]
                results = filtered_results[:top_k]
            else:
                results = results[:top_k]
            
            # Add legal citations
            enhanced_results = []
            for result in results:
                enhanced_result = result.copy()
                
                # Add legal citation
                enhanced_result['legal_citation'] = self._generate_citation(result)
                
                # Add legal context
                enhanced_result['legal_context'] = {
                    'query': query,
                    'document_type': result.get('legal_type_name', 'Unknown'),
                    'retrieval_method': 'semantic_search',
                    'confidence_score': result['similarity_score'],
                    'retrieval_timestamp': datetime.now().isoformat()
                }
                
                enhanced_results.append(enhanced_result)
            
            logger.info(f"Retrieved {len(enhanced_results)} legal documents for query: '{query[:50]}...'")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error querying legal documents: {e}")
            return []
    
    def _generate_citation(self, document: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate legal citation for a document
        
        Args:
            document: Document with metadata
            
        Returns:
            Citation dictionary
        """
        doc_type = document.get('legal_type', 'unknown')
        source = document.get('source', 'unknown')
        
        citation = {
            'source_file': source,
            'document_type': doc_type,
            'similarity_score': f"{document['similarity_score']:.4f}",
            'retrieval_method': 'semantic_search'
        }
        
        # Add type-specific citation information
        if doc_type == 'case_law':
            citation['citation_type'] = 'Case Law'
            citation['case_name'] = source.replace('.txt', '').replace('_', ' ').title()
        elif doc_type == 'statutes':
            citation['citation_type'] = 'Statute'
            citation['statute_name'] = source.replace('.txt', '').replace('_', ' ').title()
        elif doc_type == 'contracts':
            citation['citation_type'] = 'Contract'
            citation['contract_type'] = source.replace('.txt', '').replace('_', ' ').title()
        
        return citation
    
    def query_case_law(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query case law documents specifically"""
        return self.query_legal_docs(query, top_k, doc_types=['case_law'])
    
    def query_statutes(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query statute documents specifically"""
        return self.query_legal_docs(query, top_k, doc_types=['statutes'])
    
    def query_contracts(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query contract documents specifically"""
        return self.query_legal_docs(query, top_k, doc_types=['contracts'])
    
    def get_legal_document_types(self) -> Dict[str, str]:
        """Get available legal document types"""
        return self.document_types.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get legal RAG system statistics"""
        if not self.retriever:
            return {'status': 'not_initialized'}
        
        stats = self.retriever.get_stats()
        stats['legal_document_types'] = self.document_types
        stats['legal_data_directory'] = self.legal_data_dir
        stats['index_directory'] = self.index_dir
        
        return stats
    
    def rebuild_index(self):
        """Rebuild the legal document index"""
        logger.info("Rebuilding legal document index...")
        
        # Remove existing index files
        index_path = os.path.join(self.index_dir, "legal_faiss_index.bin")
        metadata_path = os.path.join(self.index_dir, "legal_metadata.json")
        
        for path in [index_path, metadata_path]:
            if os.path.exists(path):
                os.remove(path)
        
        # Rebuild index
        self._build_index()
        
        logger.info("Legal document index rebuilt successfully")


# Convenience functions
def create_legal_rag(legal_data_dir: str = "verticals/legal/datasets") -> LegalRAG:
    """Create a Legal RAG instance"""
    return LegalRAG(legal_data_dir)


def query_legal_docs(query: str, 
                    top_k: int = 3, 
                    legal_data_dir: str = "verticals/legal/datasets") -> List[Dict[str, Any]]:
    """
    Quick function to query legal documents
    
    Args:
        query: Legal query
        top_k: Number of results
        legal_data_dir: Legal datasets directory
        
    Returns:
        List of legal documents with citations
    """
    legal_rag = create_legal_rag(legal_data_dir)
    return legal_rag.query_legal_docs(query, top_k)


def query_case_law(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Quick function to query case law"""
    legal_rag = create_legal_rag()
    return legal_rag.query_case_law(query, top_k)


def query_statutes(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Quick function to query statutes"""
    legal_rag = create_legal_rag()
    return legal_rag.query_statutes(query, top_k)


def query_contracts(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Quick function to query contracts"""
    legal_rag = create_legal_rag()
    return legal_rag.query_contracts(query, top_k)


if __name__ == "__main__":
    # Test the Legal RAG system
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("🧪 Testing Legal RAG System")
        print("=" * 50)
        
        # Create Legal RAG
        legal_rag = create_legal_rag()
        
        # Print stats
        stats = legal_rag.get_stats()
        print(f"📊 Legal RAG Stats: {stats}")
        
        # Test queries
        test_queries = [
            "constitutional right to privacy",
            "employment discrimination",
            "contract termination clause",
            "judicial review power"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = legal_rag.query_legal_docs(query, top_k=2)
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result['similarity_score']:.4f}")
                print(f"     Type: {result.get('legal_type_name', 'Unknown')}")
                print(f"     Source: {result['source']}")
                print(f"     Citation: {result['legal_citation']}")
                print(f"     Text: {result['text'][:100]}...")
                print()
        
        # Test specific document types
        print("\n📚 Testing Case Law Query:")
        case_results = legal_rag.query_case_law("constitutional interpretation", top_k=1)
        for result in case_results:
            print(f"  Case: {result['legal_citation']['case_name']}")
            print(f"  Score: {result['similarity_score']:.4f}")
        
        print("\n✅ Legal RAG test completed successfully!")
        
    except Exception as e:
        print(f"❌ Legal RAG test failed: {e}")
        sys.exit(1)
