"""
API routes for the AI Coding Assistant.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.services.agent import agent, CodeRequest, CodeResponse, ChatRequest, ChatResponse
from app.core.memory import memory
from app.core.model_router import router as model_router
from app.core.plugins import plugin_manager
from app.core.telemetry import telemetry

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


class ModelInfo(BaseModel):
    """Model information response."""
    available_models: List[str]
    selected_model: str
    providers_status: Dict[str, bool]


class StreamRequest(BaseModel):
    """Request model for streaming completions."""
    messages: List[Dict[str, Any]]
    model_name: Optional[str] = None
    task_type: str = "general"


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    tool_name: str
    parameters: Dict[str, Any] = {}


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


@router.get("/models/info", response_model=ModelInfo)
async def get_model_info() -> ModelInfo:
    """Get information about available models and their status."""
    try:
        available_models = model_router.get_available_models()
        selected_model = model_router.select_best_model() or "none"
        
        # Check provider status
        providers_status = {}
        for provider_name, provider in model_router.providers.items():
            providers_status[provider_name.value] = provider.is_available()
        
        return ModelInfo(
            available_models=available_models,
            selected_model=selected_model,
            providers_status=providers_status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.post("/models/generate")
async def generate_with_model_selection(request: StreamRequest) -> Dict[str, Any]:
    """Generate completion with automatic model selection."""
    try:
        result = await model_router.generate_completion(
            messages=request.messages,
            model_name=request.model_name,
            task_type=request.task_type
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model generation failed: {str(e)}"
        )


@router.post("/models/stream")
async def stream_with_model_selection(request: StreamRequest):
    """Stream completion with automatic model selection."""
    try:
        async def generate_stream():
            async for chunk in model_router.stream_completion(
                messages=request.messages,
                model_name=request.model_name,
                task_type=request.task_type
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model streaming failed: {str(e)}"
        )


@router.get("/tools/list")
async def list_tools() -> Dict[str, Any]:
    """List all available tools."""
    try:
        tools = plugin_manager.list_tools()
        return {
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.post("/tools/execute")
async def execute_tool(request: ToolExecutionRequest) -> Dict[str, Any]:
    """Execute a tool with given parameters."""
    try:
        result = await plugin_manager.execute_tool(
            request.tool_name,
            **request.parameters
        )
        
        return {
            "tool_name": request.tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )


@router.get("/tools/{tool_name}/schema")
async def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """Get the schema for a specific tool."""
    try:
        tool = plugin_manager.get_tool(tool_name)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
            )
        
        return tool.get_schema()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool schema: {str(e)}"
        )


@router.get("/telemetry/stats")
async def get_telemetry_stats(hours: int = 24) -> Dict[str, Any]:
    """Get API usage statistics."""
    try:
        return telemetry.get_api_stats(hours=hours)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get telemetry stats: {str(e)}"
        )


@router.get("/telemetry/health")
async def get_health_status() -> Dict[str, Any]:
    """Get system health status."""
    try:
        return telemetry.get_health_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )


@router.get("/telemetry/models")
async def get_model_stats() -> Dict[str, Any]:
    """Get model usage statistics."""
    try:
        model_stats = telemetry.get_model_stats()
        return {
            "models": [
                {
                    "model_name": m.model_name,
                    "provider": m.provider,
                    "total_calls": m.total_calls,
                    "total_tokens": m.total_tokens,
                    "avg_latency_ms": m.avg_latency_ms,
                    "success_rate": m.success_rate,
                    "last_used": m.last_used.isoformat() if m.last_used else None
                }
                for m in model_stats
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model stats: {str(e)}"
        )


@router.delete("/telemetry/clear")
async def clear_telemetry_data() -> Dict[str, str]:
    """Clear all telemetry data."""
    try:
        telemetry.clear_data()
        return {"message": "Telemetry data cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear telemetry data: {str(e)}"
        )