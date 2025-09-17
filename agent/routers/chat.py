"""
Chat endpoints for the Copilot Platform Agent
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    url: Optional[str] = None
    timestamp: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    timestamp: str
    sources: Optional[list] = None
    suggestions: Optional[list] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage, request: Request):
    """Main chat endpoint"""
    try:
        # Get LLM client from app state
        llm_client = request.app.state.llm_client
        
        # Process the message
        response = await llm_client.process_message(
            message.message,
            url=message.url,
            context=message.context
        )
        
        return ChatResponse(
            message=response["message"],
            timestamp=response["timestamp"],
            sources=response.get("sources"),
            suggestions=response.get("suggestions")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream_endpoint(message: ChatMessage, request: Request):
    """Streaming chat endpoint"""
    try:
        llm_client = request.app.state.llm_client
        
        async def generate():
            async for chunk in llm_client.stream_message(
                message.message,
                url=message.url,
                context=message.context
            ):
                yield f"data: {chunk}\n\n"
        
        return generate()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
