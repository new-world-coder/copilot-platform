"""
Tasks Router Module
Handles task extraction from legal documents
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from libs.task_extraction.llm_task_parser import TaskExtractor

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskExtractionRequest(BaseModel):
    """Request model for task extraction"""
    text: str = Field(..., description="Text to extract tasks from")
    llm_provider: str = Field(default="local", description="LLM provider for extraction")
    llm_model: str = Field(default="local", description="LLM model name")
    document_type: str = Field(default="legal", description="Type of document")
    use_llm: bool = Field(default=True, description="Use LLM extraction (fallback to regex if False)")


class TaskExtractionResponse(BaseModel):
    """Response model for task extraction"""
    tasks: List[Dict[str, Any]] = Field(..., description="Extracted tasks")
    extraction_method: str = Field(..., description="Method used for extraction")
    summary: Dict[str, Any] = Field(..., description="Task summary statistics")
    metadata: Dict[str, Any] = Field(..., description="Extraction metadata")


@router.post("/extract", response_model=TaskExtractionResponse)
async def extract_tasks(request: TaskExtractionRequest):
    """
    Extract tasks from text using LLM with regex fallback
    
    Args:
        request: Task extraction request
        
    Returns:
        Extracted tasks with metadata
    """
    try:
        logger.info(f"Extracting tasks from text (length: {len(request.text)})")
        
        # Create task extractor
        extractor = TaskExtractor(
            llm_provider=request.llm_provider,
            llm_model=request.llm_model
        )
        
        # Extract tasks
        result = await extractor.extract_tasks(
            text=request.text,
            document_type=request.document_type
        )
        
        # Get task summary
        summary = extractor.get_task_summary(result.get('tasks', []))
        
        # Prepare response
        response = TaskExtractionResponse(
            tasks=result.get('tasks', []),
            extraction_method=result.get('extraction_method', 'unknown'),
            summary=summary,
            metadata=result.get('metadata', {})
        )
        
        logger.info(f"Task extraction completed. Found {len(response.tasks)} tasks using {response.extraction_method}")
        return response
        
    except Exception as e:
        logger.error(f"Task extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task extraction failed: {str(e)}")


@router.post("/extract/legal")
async def extract_legal_tasks(request: TaskExtractionRequest):
    """Extract tasks specifically from legal documents"""
    request.document_type = "legal"
    return await extract_tasks(request)


@router.post("/extract/contract")
async def extract_contract_tasks(request: TaskExtractionRequest):
    """Extract tasks specifically from contracts"""
    request.document_type = "contract"
    return await extract_tasks(request)


@router.post("/extract/case-law")
async def extract_case_law_tasks(request: TaskExtractionRequest):
    """Extract tasks specifically from case law"""
    request.document_type = "case_law"
    return await extract_tasks(request)


@router.get("/health")
async def tasks_health():
    """Health check for task extraction system"""
    try:
        # Test task extractor
        extractor = TaskExtractor("local")
        
        return {
            "status": "healthy",
            "service": "task-extraction",
            "components": {
                "llm_extraction": "available",
                "regex_fallback": "available",
                "task_patterns": len(extractor.task_patterns)
            }
        }
    except Exception as e:
        logger.error(f"Task extraction health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "task-extraction",
            "error": str(e)
        }


@router.get("/patterns")
async def get_task_patterns():
    """Get available task extraction patterns"""
    try:
        extractor = TaskExtractor("local")
        
        return {
            "patterns": extractor.task_patterns,
            "pattern_counts": {
                pattern_type: len(patterns) 
                for pattern_type, patterns in extractor.task_patterns.items()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get task patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task patterns: {str(e)}")


if __name__ == "__main__":
    # Test the tasks router
    import asyncio
    
    async def test_tasks_router():
        """Test task extraction functionality"""
        print("🧪 Testing Tasks Router")
        print("=" * 50)
        
        # Sample legal text
        sample_text = """
        The plaintiff must file a motion for summary judgment within 30 days of the discovery deadline.
        The defendant shall provide all relevant documents by March 15, 2024.
        Both parties are required to attend the mediation session on April 1, 2024.
        The court orders that expert reports must be submitted no later than May 1, 2024.
        """
        
        request = TaskExtractionRequest(
            text=sample_text,
            llm_provider="local",
            document_type="legal"
        )
        
        try:
            response = await extract_tasks(request)
            
            print(f"✅ Task extraction successful")
            print(f"Method: {response.extraction_method}")
            print(f"Tasks found: {len(response.tasks)}")
            print(f"Summary: {response.summary}")
            
            for i, task in enumerate(response.tasks, 1):
                print(f"\nTask {i}:")
                print(f"  Action: {task.get('action', 'N/A')}")
                print(f"  Deadline: {task.get('deadline', 'N/A')}")
                print(f"  Priority: {task.get('priority', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Task extraction failed: {e}")
    
    # Run test
    asyncio.run(test_tasks_router())
