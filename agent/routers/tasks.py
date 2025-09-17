"""
Task management endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()


class TaskRequest(BaseModel):
    """Task request model"""
    task_type: str
    parameters: Dict[str, Any]
    priority: Optional[int] = 1


class TaskResponse(BaseModel):
    """Task response model"""
    task_id: str
    status: str
    created_at: str
    estimated_duration: Optional[int] = None


@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskRequest, request: Request):
    """Create a new task"""
    try:
        task_manager = request.app.state.task_manager
        
        task_id = await task_manager.create_task(
            task_type=task.task_type,
            parameters=task.parameters,
            priority=task.priority
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            created_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, request: Request):
    """Get task status"""
    try:
        task_manager = request.app.state.task_manager
        status = await task_manager.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(request: Request, limit: int = 10, offset: int = 0):
    """List recent tasks"""
    try:
        task_manager = request.app.state.task_manager
        tasks = await task_manager.list_tasks(limit=limit, offset=offset)
        
        return {"tasks": tasks}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
