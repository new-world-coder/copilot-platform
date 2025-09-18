"""
RAG Indexer Module
Builds FAISS index from text documents for efficient similarity search
"""

import os
import json
import pickle
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging
import numpy as np
import faiss
from tqdm import tqdm

from embedder import Embedder

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Builds and manages FAISS index for document retrieval"""
    
    def __init__(self, embedder: Embedder, index_type: str = "flat"):
        """
        Initialize the indexer
        
        Args:
            embedder: Embedder instance for generating embeddings
            index_type: Type of FAISS index ("flat", "ivf", "hnsw")
        """
        self.embedder = embedder
        self.index_type = index_type
        self.index = None
        self.documents = []
        self.metadata = {}
        
        # Initialize FAISS index
        self._create_index()
    
    def _create_index(self):
        """Create FAISS index based on type"""
        embedding_dim = self.embedder.get_embedding_dimension()
        
        if self.index_type == "flat":
            # Exact search, slower but most accurate
            self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product (cosine similarity)
        elif self.index_type == "ivf":
            # Inverted file index, faster but approximate
            quantizer = faiss.IndexFlatIP(embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, embedding_dim, 100)  # 100 clusters
        elif self.index_type == "hnsw":
            # Hierarchical Navigable Small World, good balance
            self.index = faiss.IndexHNSWFlat(embedding_dim, 32)  # 32 connections per node
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        logger.info(f"Created FAISS index: {self.index_type} (dim: {embedding_dim})")
    
    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """
        Add documents to the index
        
        Args:
            documents: List of documents with 'text' field
            batch_size: Batch size for processing
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        logger.info(f"Adding {len(documents)} documents to index...")
        
        # Process documents in batches
        for i in tqdm(range(0, len(documents), batch_size), desc="Indexing documents"):
            batch = documents[i:i + batch_size]
            
            # Extract texts
            texts = [doc.get('text', '') for doc in batch]
            
            # Generate embeddings
            embeddings = self.embedder.embed_texts(texts)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings.astype('float32'))
            
            # Store documents and metadata
            for j, doc in enumerate(batch):
                doc_id = len(self.documents)
                doc_with_id = {
                    'id': doc_id,
                    'text': doc.get('text', ''),
                    'source': doc.get('source', ''),
                    'metadata': doc.get('metadata', {}),
                    'embedding_id': i + j
                }
                self.documents.append(doc_with_id)
        
        # Train index if needed (for IVF)
        if self.index_type == "ivf" and not self.index.is_trained:
            logger.info("Training IVF index...")
            self.index.train(self.index.reconstruct_n(0, self.index.ntotal))
        
        logger.info(f"Index built successfully. Total documents: {len(self.documents)}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the index for similar documents
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of similar documents with similarity scores
        """
        if not self.documents:
            logger.warning("Index is empty")
            return []
        
        # Embed query
        query_embedding = self.embedder.embed_text(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
        
        # Format results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:  # Valid index
                doc = self.documents[idx].copy()
                doc['similarity_score'] = float(score)
                results.append(doc)
        
        return results
    
    def save_index(self, index_path: str, metadata_path: str):
        """
        Save the index and metadata to disk
        
        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save document metadata
        """
        try:
            # Save FAISS index
            faiss.write_index(self.index, index_path)
            
            # Save metadata
            metadata = {
                'documents': self.documents,
                'index_type': self.index_type,
                'embedding_dim': self.embedder.get_embedding_dimension(),
                'model_name': self.embedder.model_name,
                'total_documents': len(self.documents)
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Index saved to {index_path}")
            logger.info(f"Metadata saved to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def load_index(self, index_path: str, metadata_path: str):
        """
        Load the index and metadata from disk
        
        Args:
            index_path: Path to FAISS index
            metadata_path: Path to document metadata
        """
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.documents = metadata['documents']
            self.index_type = metadata['index_type']
            
            logger.info(f"Index loaded from {index_path}")
            logger.info(f"Loaded {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'total_documents': len(self.documents),
            'index_type': self.index_type,
            'embedding_dimension': self.embedder.get_embedding_dimension(),
            'model_name': self.embedder.model_name,
            'index_size': self.index.ntotal if self.index else 0
        }


def load_documents_from_directory(directory: str, file_extensions: List[str] = None) -> List[Dict[str, Any]]:
    """
    Load documents from a directory
    
    Args:
        directory: Directory path
        file_extensions: List of file extensions to process (default: ['.txt', '.md', '.json'])
        
    Returns:
        List of documents
    """
    if file_extensions is None:
        file_extensions = ['.txt', '.md', '.json']
    
    documents = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory does not exist: {directory}")
        return documents
    
    logger.info(f"Loading documents from {directory}")
    
    for file_path in tqdm(directory_path.rglob('*'), desc="Loading files"):
        if file_path.is_file() and file_path.suffix.lower() in file_extensions:
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:  # Only add non-empty files
                    doc = {
                        'text': content,
                        'source': str(file_path.relative_to(directory_path)),
                        'metadata': {
                            'file_path': str(file_path),
                            'file_size': file_path.stat().st_size,
                            'file_extension': file_path.suffix
                        }
                    }
                    documents.append(doc)
                    
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
    
    logger.info(f"Loaded {len(documents)} documents")
    return documents


def create_index_from_directory(
    directory: str, 
    output_dir: str = "data/vector_store",
    model_name: str = "all-MiniLM-L6-v2",
    index_type: str = "flat"
) -> DocumentIndexer:
    """
    Create index from directory of documents
    
    Args:
        directory: Directory containing documents
        output_dir: Directory to save index files
        model_name: Embedding model name
        index_type: FAISS index type
        
    Returns:
        DocumentIndexer instance
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load documents
    documents = load_documents_from_directory(directory)
    
    if not documents:
        raise ValueError(f"No documents found in {directory}")
    
    # Create embedder
    embedder = Embedder(model_name)
    
    # Create indexer
    indexer = DocumentIndexer(embedder, index_type)
    
    # Add documents to index
    indexer.add_documents(documents)
    
    # Save index
    index_path = os.path.join(output_dir, "faiss_index.bin")
    metadata_path = os.path.join(output_dir, "metadata.json")
    indexer.save_index(index_path, metadata_path)
    
    return indexer


def main():
    """CLI interface for indexing documents"""
    parser = argparse.ArgumentParser(description="Build FAISS index from documents")
    parser.add_argument("directory", help="Directory containing documents to index")
    parser.add_argument("--output-dir", default="data/vector_store", help="Output directory for index files")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model name")
    parser.add_argument("--index-type", default="flat", choices=["flat", "ivf", "hnsw"], help="FAISS index type")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print(f"🚀 Building FAISS index from {args.directory}")
        print(f"📁 Output directory: {args.output_dir}")
        print(f"🤖 Model: {args.model}")
        print(f"🔍 Index type: {args.index_type}")
        
        # Create index
        indexer = create_index_from_directory(
            directory=args.directory,
            output_dir=args.output_dir,
            model_name=args.model,
            index_type=args.index_type
        )
        
        # Print stats
        stats = indexer.get_stats()
        print("\n📊 Index Statistics:")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Embedding dimension: {stats['embedding_dimension']}")
        print(f"   Model: {stats['model_name']}")
        print(f"   Index type: {stats['index_type']}")
        
        # Test search
        print("\n🧪 Testing search...")
        test_query = "legal contract terms"
        results = indexer.search(test_query, top_k=3)
        
        print(f"Query: '{test_query}'")
        print("Top 3 results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['similarity_score']:.4f}")
            print(f"     Source: {result['source']}")
            print(f"     Text: {result['text'][:100]}...")
            print()
        
        print("✅ Indexing completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Indexing failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
