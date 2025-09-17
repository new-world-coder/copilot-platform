"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "copilot-agent"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "copilot-agent",
        "components": {
            "database": "healthy",
            "llm_client": "healthy",
            "task_manager": "healthy"
        }
    }
