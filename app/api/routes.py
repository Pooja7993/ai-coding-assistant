"""
API routes for the AI Coding Assistant.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.agent import agent, CodeRequest, CodeResponse, ChatRequest, ChatResponse
from app.core.memory import memory

router = APIRouter()


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str
    message: str


class CodeReviewRequest(BaseModel):
    """Request model for code review."""
    code: str
    language: str = "python"


class MemoryStats(BaseModel):
    """Memory statistics response."""
    backend_type: str
    total_documents: int
    status: str


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        message="AI Coding Assistant is running"
    )


@router.post("/generate-code", response_model=CodeResponse)
async def generate_code(request: CodeRequest) -> CodeResponse:
    """Generate code based on user prompt."""
    try:
        response = await agent.generate_code(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with the AI assistant."""
    try:
        response = await agent.chat(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/review-code")
async def review_code(request: CodeReviewRequest) -> Dict[str, Any]:
    """Review code and provide feedback."""
    try:
        feedback = agent.review_code(request.code, request.language)
        return {
            "code": request.code,
            "language": request.language,
            "review": feedback
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code review failed: {str(e)}"
        )


@router.get("/memory/stats", response_model=MemoryStats)
async def get_memory_stats() -> MemoryStats:
    """Get memory statistics."""
    try:
        # This is a simplified version - in production, implement proper stats
        return MemoryStats(
            backend_type=memory.backend.__class__.__name__,
            total_documents=len(getattr(memory.backend, 'documents', [])),
            status="active"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory stats: {str(e)}"
        )


@router.delete("/memory/clear")
async def clear_memory() -> Dict[str, str]:
    """Clear all memory."""
    try:
        memory.clear_memory()
        return {"message": "Memory cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear memory: {str(e)}"
        )


@router.get("/memory/search")
async def search_memory(query: str, k: int = 5) -> Dict[str, Any]:
    """Search memory for relevant context."""
    try:
        results = memory.search_relevant_context(query, k)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory search failed: {str(e)}"
        )