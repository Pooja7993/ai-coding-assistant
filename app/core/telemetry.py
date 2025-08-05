"""
Telemetry and monitoring system for the AI Coding Assistant.
Tracks API usage, model performance, and system metrics.
"""
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pydantic import BaseModel
import threading

logger = logging.getLogger(__name__)


@dataclass
class APICall:
    """Represents an API call record."""
    timestamp: datetime
    endpoint: str
    method: str
    user_id: Optional[str]
    duration_ms: float
    status_code: int
    model_used: Optional[str] = None
    tokens_used: int = 0
    error: Optional[str] = None


@dataclass
class ModelUsage:
    """Represents model usage statistics."""
    model_name: str
    provider: str
    total_calls: int
    total_tokens: int
    avg_latency_ms: float
    success_rate: float
    last_used: datetime


class SystemMetrics(BaseModel):
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    active_connections: int
    queue_size: int
    timestamp: datetime


class TelemetryCollector:
    """Collects and manages telemetry data."""
    
    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self.api_calls = deque(maxlen=max_records)
        self.model_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_calls": 0,
            "total_tokens": 0,
            "total_latency": 0.0,
            "success_count": 0,
            "error_count": 0,
            "last_used": None
        })
        self.system_metrics = deque(maxlen=1000)  # Keep last 1000 metric points
        self._lock = threading.Lock()
        
        logger.info("Telemetry collector initialized")
    
    def record_api_call(self, call: APICall):
        """Record an API call."""
        with self._lock:
            self.api_calls.append(call)
            
            # Update model statistics if model was used
            if call.model_used:
                stats = self.model_stats[call.model_used]
                stats["total_calls"] += 1
                stats["total_tokens"] += call.tokens_used
                stats["total_latency"] += call.duration_ms
                stats["last_used"] = call.timestamp
                
                if call.status_code < 400:
                    stats["success_count"] += 1
                else:
                    stats["error_count"] += 1
    
    def record_system_metrics(self, metrics: SystemMetrics):
        """Record system metrics."""
        with self._lock:
            self.system_metrics.append(metrics)
    
    def get_api_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get API usage statistics for the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_calls = [call for call in self.api_calls if call.timestamp >= cutoff]
        
        if not recent_calls:
            return {
                "total_calls": 0,
                "avg_duration_ms": 0,
                "success_rate": 0,
                "endpoints": {},
                "models": {},
                "errors": []
            }
        
        # Calculate statistics
        total_calls = len(recent_calls)
        avg_duration = sum(call.duration_ms for call in recent_calls) / total_calls
        success_count = sum(1 for call in recent_calls if call.status_code < 400)
        success_rate = success_count / total_calls
        
        # Endpoint statistics
        endpoint_stats = defaultdict(int)
        for call in recent_calls:
            endpoint_stats[call.endpoint] += 1
        
        # Model usage statistics
        model_stats = defaultdict(lambda: {"calls": 0, "tokens": 0})
        for call in recent_calls:
            if call.model_used:
                model_stats[call.model_used]["calls"] += 1
                model_stats[call.model_used]["tokens"] += call.tokens_used
        
        # Recent errors
        errors = [
            {
                "timestamp": call.timestamp.isoformat(),
                "endpoint": call.endpoint,
                "error": call.error,
                "status_code": call.status_code
            }
            for call in recent_calls[-50:]  # Last 50 calls
            if call.error
        ]
        
        return {
            "total_calls": total_calls,
            "avg_duration_ms": round(avg_duration, 2),
            "success_rate": round(success_rate, 3),
            "endpoints": dict(endpoint_stats),
            "models": dict(model_stats),
            "errors": errors
        }
    
    def get_model_stats(self) -> List[ModelUsage]:
        """Get model usage statistics."""
        with self._lock:
            stats_list = []
            for model_name, stats in self.model_stats.items():
                if stats["total_calls"] > 0:
                    avg_latency = stats["total_latency"] / stats["total_calls"]
                    success_rate = stats["success_count"] / stats["total_calls"]
                    
                    stats_list.append(ModelUsage(
                        model_name=model_name,
                        provider="unknown",  # Would need to track this
                        total_calls=stats["total_calls"],
                        total_tokens=stats["total_tokens"],
                        avg_latency_ms=round(avg_latency, 2),
                        success_rate=round(success_rate, 3),
                        last_used=stats["last_used"]
                    ))
            
            return sorted(stats_list, key=lambda x: x.total_calls, reverse=True)
    
    def get_system_metrics(self, minutes: int = 60) -> List[SystemMetrics]:
        """Get system metrics for the last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        with self._lock:
            return [m for m in self.system_metrics if m.timestamp >= cutoff]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        recent_stats = self.get_api_stats(hours=1)
        system_metrics = self.get_system_metrics(minutes=5)
        
        # Determine health status
        health = "healthy"
        issues = []
        
        # Check error rate
        if recent_stats["success_rate"] < 0.95:
            health = "degraded"
            issues.append(f"High error rate: {1 - recent_stats['success_rate']:.1%}")
        
        # Check response time
        if recent_stats["avg_duration_ms"] > 5000:
            health = "degraded"
            issues.append(f"High response time: {recent_stats['avg_duration_ms']:.0f}ms")
        
        # Check recent system metrics
        if system_metrics:
            avg_cpu = sum(m.cpu_usage for m in system_metrics) / len(system_metrics)
            avg_memory = sum(m.memory_usage for m in system_metrics) / len(system_metrics)
            
            if avg_cpu > 80:
                health = "degraded"
                issues.append(f"High CPU usage: {avg_cpu:.1f}%")
            
            if avg_memory > 85:
                health = "degraded"
                issues.append(f"High memory usage: {avg_memory:.1f}%")
        
        if len(issues) > 3:
            health = "unhealthy"
        
        return {
            "status": health,
            "issues": issues,
            "last_check": datetime.now().isoformat(),
            "api_stats": recent_stats,
            "uptime_hours": (datetime.now() - self._start_time).total_seconds() / 3600
        }
    
    def export_data(self, format: str = "json") -> str:
        """Export telemetry data."""
        with self._lock:
            data = {
                "api_calls": [asdict(call) for call in list(self.api_calls)],
                "model_stats": dict(self.model_stats),
                "system_metrics": [m.dict() for m in list(self.system_metrics)],
                "export_timestamp": datetime.now().isoformat()
            }
        
        if format == "json":
            return json.dumps(data, default=str, indent=2)
        else:
            return str(data)
    
    def clear_data(self):
        """Clear all telemetry data."""
        with self._lock:
            self.api_calls.clear()
            self.model_stats.clear()
            self.system_metrics.clear()
            logger.info("Telemetry data cleared")


class TelemetryMiddleware:
    """ASGI middleware for collecting API telemetry."""
    
    def __init__(self, app, collector: TelemetryCollector):
        self.app = app
        self.collector = collector
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Extract request info
        method = scope["method"]
        path = scope["path"]
        
        # Wrap send to capture response info
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            error = None
        except Exception as e:
            error = str(e)
            status_code = 500
            raise
        finally:
            # Record the API call
            duration_ms = (time.time() - start_time) * 1000
            
            call = APICall(
                timestamp=datetime.now(),
                endpoint=path,
                method=method,
                user_id=None,  # Would extract from auth headers
                duration_ms=duration_ms,
                status_code=status_code,
                error=error
            )
            
            self.collector.record_api_call(call)


# Global telemetry collector
telemetry = TelemetryCollector()
telemetry._start_time = datetime.now()


def collect_system_metrics():
    """Collect current system metrics."""
    try:
        import psutil
        
        metrics = SystemMetrics(
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            active_connections=len(psutil.net_connections()),
            queue_size=0,  # Would need to implement queue monitoring
            timestamp=datetime.now()
        )
        
        telemetry.record_system_metrics(metrics)
        
    except ImportError:
        # psutil not available, use basic metrics
        metrics = SystemMetrics(
            cpu_usage=0.0,
            memory_usage=0.0,
            active_connections=0,
            queue_size=0,
            timestamp=datetime.now()
        )
        
        telemetry.record_system_metrics(metrics)
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")


# Background task to collect system metrics periodically
import asyncio
import threading

def start_metrics_collection():
    """Start background metrics collection."""
    def metrics_loop():
        while True:
            collect_system_metrics()
            time.sleep(30)  # Collect every 30 seconds
    
    thread = threading.Thread(target=metrics_loop, daemon=True)
    thread.start()
    logger.info("Started background metrics collection")