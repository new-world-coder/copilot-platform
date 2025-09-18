"""
RAG Embedder Module
Handles text embedding using sentence-transformers
"""

import numpy as np
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class Embedder:
    """Text embedder using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: Optional[str] = None):
        """
        Initialize the embedder
        
        Args:
            model_name: Name of the sentence-transformer model to use
            cache_dir: Directory to cache the model (default: ~/.cache/sentence_transformers)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/sentence_transformers")
        
        # Create cache directory if it doesn't exist
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Loading sentence-transformer model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name, cache_folder=self.cache_dir)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array of embeddings
        """
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)
            return embedding[0]
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed multiple text strings
        
        Args:
            texts: List of input texts to embed
            batch_size: Batch size for processing
            
        Returns:
            numpy array of embeddings (shape: [len(texts), embedding_dim])
        """
        try:
            embeddings = self.model.encode(
                texts, 
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            logger.info(f"Embedded {len(texts)} texts successfully")
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            raise
    
    def embed_documents(self, documents: List[dict], text_field: str = "text") -> List[dict]:
        """
        Embed a list of documents
        
        Args:
            documents: List of documents (dicts) to embed
            text_field: Field name containing the text to embed
            
        Returns:
            List of documents with added 'embedding' field
        """
        try:
            # Extract texts
            texts = [doc[text_field] for doc in documents if text_field in doc]
            
            if not texts:
                logger.warning("No texts found in documents")
                return documents
            
            # Embed texts
            embeddings = self.embed_texts(texts)
            
            # Add embeddings to documents
            result_docs = []
            embedding_idx = 0
            
            for doc in documents:
                if text_field in doc:
                    doc_copy = doc.copy()
                    doc_copy['embedding'] = embeddings[embedding_idx].tolist()
                    result_docs.append(doc_copy)
                    embedding_idx += 1
                else:
                    result_docs.append(doc)
            
            logger.info(f"Embedded {len(result_docs)} documents")
            return result_docs
            
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.embedding_dim
    
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "cache_dir": self.cache_dir
        }


# Convenience functions for direct use
def create_embedder(model_name: str = "all-MiniLM-L6-v2") -> Embedder:
    """Create a new embedder instance"""
    return Embedder(model_name)


def embed_text(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Quick function to embed a single text"""
    embedder = create_embedder(model_name)
    return embedder.embed_text(text)


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Quick function to embed multiple texts"""
    embedder = create_embedder(model_name)
    return embedder.embed_texts(texts)


# Available models for legal text
LEGAL_MODELS = {
    "all-MiniLM-L6-v2": "Fast, general-purpose model (384 dim)",
    "all-mpnet-base-v2": "Higher quality, slower model (768 dim)",
    "paraphrase-multilingual-MiniLM-L12-v2": "Multilingual support (384 dim)",
    "sentence-transformers/all-MiniLM-L6-v2": "Explicit sentence-transformers prefix",
    "sentence-transformers/all-mpnet-base-v2": "Explicit sentence-transformers prefix"
}


def list_available_models() -> dict:
    """List available embedding models"""
    return LEGAL_MODELS


if __name__ == "__main__":
    # Test the embedder
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample legal text
    sample_texts = [
        "The plaintiff filed a motion for summary judgment.",
        "The court granted the defendant's motion to dismiss.",
        "The contract shall be governed by the laws of California.",
        "The parties agree to binding arbitration for all disputes."
    ]
    
    try:
        embedder = create_embedder()
        
        print("Testing embedder...")
        print(f"Model: {embedder.get_model_info()}")
        
        # Test single text
        single_embedding = embedder.embed_text(sample_texts[0])
        print(f"Single text embedding shape: {single_embedding.shape}")
        
        # Test multiple texts
        multiple_embeddings = embedder.embed_texts(sample_texts)
        print(f"Multiple texts embedding shape: {multiple_embeddings.shape}")
        
        # Test documents
        documents = [
            {"id": 1, "text": sample_texts[0], "source": "case1.txt"},
            {"id": 2, "text": sample_texts[1], "source": "case2.txt"},
            {"id": 3, "text": sample_texts[2], "source": "contract1.txt"},
            {"id": 4, "text": sample_texts[3], "source": "contract2.txt"}
        ]
        
        embedded_docs = embedder.embed_documents(documents)
        print(f"Embedded {len(embedded_docs)} documents")
        print(f"First document embedding shape: {len(embedded_docs[0]['embedding'])}")
        
        print("✅ Embedder test completed successfully!")
        
    except Exception as e:
        print(f"❌ Embedder test failed: {e}")
        sys.exit(1)
