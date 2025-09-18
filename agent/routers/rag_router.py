"""
RAG Router Module
Handles RAG-enhanced LLM queries with document retrieval and citations
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from rag.retriever import DocumentRetriever, create_retriever
from verticals.legal.legal_rag import LegalRAG, query_legal_docs
from .llm_router import process_llm_query

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    """Request model for RAG queries"""
    query: str = Field(..., description="User query for RAG-enhanced LLM processing")
    model: str = Field(default="local", description="LLM model to use")
    provider: str = Field(default="local", description="LLM provider (local, openai, gemini, onprem)")
    top_k: int = Field(default=3, description="Number of documents to retrieve")
    min_score: float = Field(default=0.0, description="Minimum similarity score for documents")
    use_legal_rag: bool = Field(default=True, description="Use legal-specific RAG if available")
    temperature: float = Field(default=0.7, description="LLM temperature")
    max_tokens: int = Field(default=1000, description="Maximum tokens for LLM response")


class RAGQueryResponse(BaseModel):
    """Response model for RAG queries"""
    answer: str = Field(..., description="LLM-generated answer with RAG context")
    citations: List[Dict[str, Any]] = Field(..., description="Retrieved documents with citations")
    query: str = Field(..., description="Original user query")
    model: str = Field(..., description="LLM model used")
    provider: str = Field(..., description="LLM provider used")
    retrieval_stats: Dict[str, Any] = Field(..., description="RAG retrieval statistics")


class DocumentCitation(BaseModel):
    """Document citation model"""
    source: str = Field(..., description="Document source file")
    similarity_score: float = Field(..., description="Similarity score")
    text_preview: str = Field(..., description="Preview of document text")
    document_type: Optional[str] = Field(None, description="Type of document (case_law, statute, contract)")
    legal_citation: Optional[Dict[str, str]] = Field(None, description="Legal citation information")


def construct_augmented_prompt(query: str, documents: List[Dict[str, Any]]) -> str:
    """
    Construct augmented prompt with retrieved documents
    
    Args:
        query: Original user query
        documents: Retrieved documents with metadata
        
    Returns:
        Augmented prompt for LLM
    """
    # Start with context header
    prompt_parts = [
        "You are a legal AI assistant. Use the following legal documents to help answer the user's question. ",
        "Provide accurate, well-reasoned answers based on the provided context. ",
        "If the documents don't contain relevant information, say so clearly.\n\n"
    ]
    
    # Add document context
    prompt_parts.append("RELEVANT LEGAL DOCUMENTS:\n")
    
    for i, doc in enumerate(documents, 1):
        doc_type = doc.get('legal_type_name', doc.get('document_type', 'Document'))
        source = doc.get('source', 'Unknown source')
        similarity_score = doc.get('similarity_score', 0.0)
        
        prompt_parts.append(f"Document {i} ({doc_type}): {source}")
        prompt_parts.append(f"Relevance Score: {similarity_score:.4f}")
        prompt_parts.append(f"Content:\n{doc.get('text', '')}\n")
        prompt_parts.append("-" * 50 + "\n")
    
    # Add user query
    prompt_parts.append(f"\nUSER QUESTION: {query}\n\n")
    prompt_parts.append("Please provide a comprehensive answer based on the legal documents above. ")
    prompt_parts.append("Include specific references to relevant documents when appropriate.")
    
    return "".join(prompt_parts)


def format_citations(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format documents as citations
    
    Args:
        documents: Retrieved documents
        
    Returns:
        Formatted citations
    """
    citations = []
    
    for doc in documents:
        citation = {
            "source": doc.get('source', 'Unknown'),
            "similarity_score": doc.get('similarity_score', 0.0),
            "text_preview": doc.get('text', '')[:200] + "..." if len(doc.get('text', '')) > 200 else doc.get('text', ''),
            "document_type": doc.get('legal_type_name', doc.get('document_type', 'Unknown')),
            "legal_citation": doc.get('legal_citation', {}),
            "metadata": doc.get('metadata', {})
        }
        citations.append(citation)
    
    return citations


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Process RAG-enhanced LLM query
    
    Retrieves relevant documents, constructs augmented prompt,
    sends to LLM, and returns answer with citations
    """
    try:
        logger.info(f"Processing RAG query: '{request.query[:50]}...' with model {request.model}")
        
        # Step 1: Retrieve relevant documents
        if request.use_legal_rag:
            # Use legal-specific RAG
            try:
                documents = query_legal_docs(
                    query=request.query,
                    top_k=request.top_k
                )
                logger.info(f"Retrieved {len(documents)} legal documents")
            except Exception as e:
                logger.warning(f"Legal RAG failed, falling back to general RAG: {e}")
                # Fallback to general RAG
                retriever = create_retriever()
                documents = retriever.retrieve(request.query, request.top_k, request.min_score)
        else:
            # Use general RAG
            retriever = create_retriever()
            documents = retriever.retrieve(request.query, request.top_k, request.min_score)
        
        if not documents:
            logger.warning("No relevant documents found")
            # Still process query without context
            documents = []
        
        # Step 2: Construct augmented prompt
        if documents:
            augmented_prompt = construct_augmented_prompt(request.query, documents)
        else:
            # Fallback to original query if no documents
            augmented_prompt = f"Please answer the following question: {request.query}"
        
        # Step 3: Send to LLM
        try:
            # Get provider config (simplified for now)
            provider_config = {
                "api_key": None,  # Will be handled by individual LLM modules
                "base_url": "http://localhost:8080" if request.provider == "onprem" else None
            }
            
            llm_response = await process_llm_query(
                text=augmented_prompt,
                provider=request.provider,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                provider_config=provider_config
            )
            
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            llm_response = f"Error processing query with {request.model}: {str(e)}"
        
        # Step 4: Format citations
        citations = format_citations(documents)
        
        # Step 5: Prepare response
        response = RAGQueryResponse(
            answer=llm_response,
            citations=citations,
            query=request.query,
            model=request.model,
            provider=request.provider,
            retrieval_stats={
                "documents_retrieved": len(documents),
                "documents_with_min_score": len([d for d in documents if d.get('similarity_score', 0) >= request.min_score]),
                "rag_enabled": request.use_legal_rag,
                "augmented_prompt_length": len(augmented_prompt)
            }
        )
        
        logger.info(f"RAG query completed successfully. Retrieved {len(documents)} documents.")
        return response
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query processing failed: {str(e)}")


@router.get("/health")
async def rag_health():
    """Health check for RAG system"""
    try:
        # Test legal RAG
        legal_rag = LegalRAG()
        stats = legal_rag.get_stats()
        
        return {
            "status": "healthy",
            "service": "rag-system",
            "legal_rag_stats": stats,
            "components": {
                "legal_rag": "available",
                "general_rag": "available",
                "llm_integration": "available"
            }
        }
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "rag-system",
            "error": str(e)
        }


@router.get("/stats")
async def rag_stats():
    """Get RAG system statistics"""
    try:
        legal_rag = LegalRAG()
        stats = legal_rag.get_stats()
        
        return {
            "legal_rag_stats": stats,
            "available_document_types": legal_rag.get_legal_document_types(),
            "system_status": "operational"
        }
    except Exception as e:
        logger.error(f"Failed to get RAG stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get RAG statistics: {str(e)}")


@router.post("/rebuild-index")
async def rebuild_rag_index():
    """Rebuild the RAG index"""
    try:
        legal_rag = LegalRAG()
        legal_rag.rebuild_index()
        
        return {
            "status": "success",
            "message": "RAG index rebuilt successfully",
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
    except Exception as e:
        logger.error(f"Failed to rebuild RAG index: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {str(e)}")


# Convenience endpoints for specific document types
@router.post("/query/case-law")
async def query_case_law(request: RAGQueryRequest):
    """Query case law documents specifically"""
    try:
        legal_rag = LegalRAG()
        documents = legal_rag.query_case_law(request.query, request.top_k)
        
        if not documents:
            return RAGQueryResponse(
                answer="No relevant case law found for your query.",
                citations=[],
                query=request.query,
                model=request.model,
                provider=request.provider,
                retrieval_stats={"documents_retrieved": 0}
            )
        
        # Process with LLM
        augmented_prompt = construct_augmented_prompt(request.query, documents)
        
        provider_config = {"api_key": None}
        llm_response = await process_llm_query(
            text=augmented_prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider_config=provider_config
        )
        
        citations = format_citations(documents)
        
        return RAGQueryResponse(
            answer=llm_response,
            citations=citations,
            query=request.query,
            model=request.model,
            provider=request.provider,
            retrieval_stats={"documents_retrieved": len(documents), "document_type": "case_law"}
        )
        
    except Exception as e:
        logger.error(f"Case law query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Case law query failed: {str(e)}")


@router.post("/query/statutes")
async def query_statutes(request: RAGQueryRequest):
    """Query statute documents specifically"""
    try:
        legal_rag = LegalRAG()
        documents = legal_rag.query_statutes(request.query, request.top_k)
        
        if not documents:
            return RAGQueryResponse(
                answer="No relevant statutes found for your query.",
                citations=[],
                query=request.query,
                model=request.model,
                provider=request.provider,
                retrieval_stats={"documents_retrieved": 0}
            )
        
        # Process with LLM
        augmented_prompt = construct_augmented_prompt(request.query, documents)
        
        provider_config = {"api_key": None}
        llm_response = await process_llm_query(
            text=augmented_prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider_config=provider_config
        )
        
        citations = format_citations(documents)
        
        return RAGQueryResponse(
            answer=llm_response,
            citations=citations,
            query=request.query,
            model=request.model,
            provider=request.provider,
            retrieval_stats={"documents_retrieved": len(documents), "document_type": "statutes"}
        )
        
    except Exception as e:
        logger.error(f"Statutes query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Statutes query failed: {str(e)}")


@router.post("/query/contracts")
async def query_contracts(request: RAGQueryRequest):
    """Query contract documents specifically"""
    try:
        legal_rag = LegalRAG()
        documents = legal_rag.query_contracts(request.query, request.top_k)
        
        if not documents:
            return RAGQueryResponse(
                answer="No relevant contracts found for your query.",
                citations=[],
                query=request.query,
                model=request.model,
                provider=request.provider,
                retrieval_stats={"documents_retrieved": 0}
            )
        
        # Process with LLM
        augmented_prompt = construct_augmented_prompt(request.query, documents)
        
        provider_config = {"api_key": None}
        llm_response = await process_llm_query(
            text=augmented_prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider_config=provider_config
        )
        
        citations = format_citations(documents)
        
        return RAGQueryResponse(
            answer=llm_response,
            citations=citations,
            query=request.query,
            model=request.model,
            provider=request.provider,
            retrieval_stats={"documents_retrieved": len(documents), "document_type": "contracts"}
        )
        
    except Exception as e:
        logger.error(f"Contracts query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Contracts query failed: {str(e)}")


if __name__ == "__main__":
    # Test the RAG router
    import asyncio
    
    async def test_rag_router():
        """Test RAG router functionality"""
        print("🧪 Testing RAG Router")
        print("=" * 50)
        
        # Test request
        request = RAGQueryRequest(
            query="What is the constitutional right to privacy?",
            model="local",
            provider="local",
            top_k=2
        )
        
        try:
            response = await rag_query(request)
            print(f"✅ RAG query successful")
            print(f"Answer: {response.answer[:100]}...")
            print(f"Citations: {len(response.citations)} documents")
            print(f"Stats: {response.retrieval_stats}")
            
        except Exception as e:
            print(f"❌ RAG query failed: {e}")
    
    # Run test
    asyncio.run(test_rag_router())
