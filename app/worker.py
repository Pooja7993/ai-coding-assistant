"""
Celery worker for background task processing.
"""
import logging
from typing import Dict, Any
from celery import Celery

from app.core.config import settings
from app.services.agent import agent
from app.core.memory import memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "ai_coding_assistant",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.worker']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True)
def generate_code_task(self, prompt: str, language: str = "python", context: str = None) -> Dict[str, Any]:
    """Background task for code generation."""
    try:
        logger.info(f"Starting code generation task for prompt: {prompt[:100]}...")
        
        # This would be async in a real implementation, but for simplicity we'll use sync
        # In production, you'd want to handle async properly
        from app.services.agent import CodeRequest
        import asyncio
        
        request = CodeRequest(
            prompt=prompt,
            language=language,
            context=context
        )
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(agent.generate_code(request))
            return {
                "status": "success",
                "code": response.code,
                "explanation": response.explanation,
                "language": response.language,
                "confidence": response.confidence
            }
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Code generation task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(bind=True)
def process_chat_task(self, message: str, context: str = None, use_memory: bool = True) -> Dict[str, Any]:
    """Background task for chat processing."""
    try:
        logger.info(f"Starting chat processing task for message: {message[:100]}...")
        
        from app.services.agent import ChatRequest
        import asyncio
        
        request = ChatRequest(
            message=message,
            context=context,
            use_memory=use_memory
        )
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(agent.chat(request))
            return {
                "status": "success",
                "response": response.response,
                "context_used": response.context_used,
                "confidence": response.confidence
            }
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Chat processing task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(bind=True)
def review_code_task(self, code: str, language: str = "python") -> Dict[str, Any]:
    """Background task for code review."""
    try:
        logger.info(f"Starting code review task for {language} code...")
        
        feedback = agent.review_code(code, language)
        
        return {
            "status": "success",
            "code": code,
            "language": language,
            "review": feedback
        }
        
    except Exception as e:
        logger.error(f"Code review task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(bind=True)
def cleanup_memory_task(self) -> Dict[str, Any]:
    """Background task for memory cleanup."""
    try:
        logger.info("Starting memory cleanup task...")
        
        # This is a placeholder for memory cleanup logic
        # In production, you might want to implement:
        # - Remove old entries
        # - Compress memory
        # - Reindex vectors
        
        # For now, just log the current memory stats
        memory_stats = {
            "backend_type": memory.backend.__class__.__name__,
            "total_documents": len(getattr(memory.backend, 'documents', [])),
        }
        
        logger.info(f"Memory cleanup completed. Stats: {memory_stats}")
        
        return {
            "status": "success",
            "message": "Memory cleanup completed",
            "stats": memory_stats
        }
        
    except Exception as e:
        logger.error(f"Memory cleanup task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    # Run worker
    celery_app.start()