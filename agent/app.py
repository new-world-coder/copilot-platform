"""
FastAPI Desktop Agent Application
Main application entry point with routing to specialized routers
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import yaml
from pathlib import Path
from contextlib import asynccontextmanager

from .routers import llm_router, pdf_router, search_router
from .core.config import load_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Copilot Platform Desktop Agent...")
    
    # Load configuration
    config = load_config()
    app.state.config = config
    
    print("✅ Agent initialized successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Copilot Platform Desktop Agent...")
    print("✅ Agent shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Copilot Platform Desktop Agent",
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

# Include specialized routers
app.include_router(llm_router.router, prefix="/llm", tags=["llm"])
app.include_router(pdf_router.router, prefix="/pdf", tags=["pdf"])
app.include_router(search_router.router, prefix="/search", tags=["search"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Copilot Platform Desktop Agent",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "copilot-desktop-agent",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if app.state.config.get("debug", False) else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    uvicorn.run(
        "app:app",
        host=config.get("host", "localhost"),
        port=config.get("port", 8000),
        reload=config.get("debug", False),
        log_level="info"
    )
