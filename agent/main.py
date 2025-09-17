"""
Copilot Platform Agent - FastAPI Application
Main entry point for the desktop agent service
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from .routers import chat, health, tasks
from .core.config import settings
from .core.database import init_db
from .core.llm_client import LLMClient
from .core.task_manager import TaskManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Copilot Platform Agent...")
    
    # Initialize database
    await init_db()
    
    # Initialize LLM client
    app.state.llm_client = LLMClient()
    await app.state.llm_client.initialize()
    
    # Initialize task manager
    app.state.task_manager = TaskManager()
    await app.state.task_manager.start()
    
    print("✅ Agent initialized successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Copilot Platform Agent...")
    await app.state.task_manager.stop()
    await app.state.llm_client.cleanup()
    print("✅ Agent shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Copilot Platform Agent",
    description="AI-powered desktop agent for enhanced productivity",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Copilot Platform Agent",
        "version": "1.0.0",
        "status": "running"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
