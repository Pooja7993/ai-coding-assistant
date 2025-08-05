"""
Main FastAPI application for the AI Coding Assistant.
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.api.routes import router
from app.core.telemetry import TelemetryMiddleware, telemetry, start_metrics_collection

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting AI Coding Assistant...")
    logger.info(f"Using memory backend: {settings.memory_type}")
    logger.info(f"Model: {settings.model_name}")
    
    # Initialize components here if needed
    try:
        # Test memory backend
        from app.core.memory import memory
        logger.info("Memory backend initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize memory backend: {e}")
    
    # Initialize model router
    try:
        from app.core.model_router import router as model_router
        available_models = model_router.get_available_models()
        logger.info(f"Model router initialized with {len(available_models)} available models: {available_models}")
    except Exception as e:
        logger.error(f"Failed to initialize model router: {e}")
    
    # Initialize plugin system
    try:
        from app.core.plugins import plugin_manager
        plugin_manager.discover_plugins()
        tools = plugin_manager.list_tools()
        logger.info(f"Plugin system initialized with {len(tools)} tools")
    except Exception as e:
        logger.error(f"Failed to initialize plugin system: {e}")
    
    # Start telemetry collection
    try:
        start_metrics_collection()
        logger.info("Telemetry collection started")
    except Exception as e:
        logger.error(f"Failed to start telemetry collection: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Coding Assistant...")


# Create FastAPI application
app = FastAPI(
    title="AI Coding Assistant",
    description="An AI-powered coding assistant with RAG memory, task orchestration, and developer tooling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add telemetry middleware
app.add_middleware(TelemetryMiddleware, collector=telemetry)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url),
            "method": request.method
        }
    )


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with basic information."""
    return {
        "name": "AI Coding Assistant",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/api/health",
            "generate_code": "/api/generate-code",
            "chat": "/api/chat",
            "review_code": "/api/review-code",
            "memory_stats": "/api/memory/stats",
            "clear_memory": "/api/memory/clear",
            "search_memory": "/api/memory/search",
            "model_info": "/api/models/info",
            "tools_list": "/api/tools/list",
            "telemetry_stats": "/api/telemetry/stats",
            "health_status": "/api/telemetry/health"
        }
    }


# Include API routes
app.include_router(router, prefix="/api", tags=["AI Assistant"])


def main():
    """Main entry point for running the application."""
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()