"""Background task service for asynchronous operations.

This module provides a service for handling background tasks, including:
- Asynchronous log recording
- Batch embedding computation
- Background model health checks

The BackgroundTaskService class uses either Celery (for production) or an
in-memory queue (for development) to handle background tasks.

Example:
    from app.services.background_task_service import background_task_service
    from app.models import RequestLog
    
    # Queue a task to compute embedding and update log
    background_task_service.queue_embedding_task(
        request_id="req-123",
        query="帮我写个Python脚本"
    )
    
    # Queue a task to update cache
    background_task_service.queue_cache_update_task(
        query="帮我写个Python脚本",
        answer="这是一个Python脚本",
        model_id="gpt-4o"
    )
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from app.utils.logger import default_logger
from app.utils.telemetry import get_tracer
from app.services.container import container

# Get OpenTelemetry tracer
tracer = get_tracer()


class BackgroundTaskService:
    """Service for handling background tasks."""
    
    def __init__(self):
        """Initialize the background task service."""
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.loop = asyncio.get_event_loop()
        self.task_queue: List[Dict[str, Any]] = []
        self.running = False
        self.start_worker()
    
    def start_worker(self):
        """Start the background worker thread."""
        if not self.running:
            self.running = True
            self.loop.create_task(self._worker_task())
            default_logger.info("Background task worker started")
    
    async def _worker_task(self):
        """Background worker task that processes the task queue."""
        while self.running:
            try:
                if self.task_queue:
                    task = self.task_queue.pop(0)
                    await self._process_task(task)
                else:
                    await asyncio.sleep(0.1)  # Sleep briefly to avoid busy waiting
            except Exception as e:
                default_logger.error(f"Background worker error: {e}")
                await asyncio.sleep(1)  # Sleep longer on error
    
    async def _process_task(self, task: Dict[str, Any]):
        """Process a single background task.
        
        Args:
            task: The task to process
        """
        task_type = task.get("type")
        task_id = task.get("id", f"task-{int(time.time() * 1000)}")
        
        with tracer.start_as_current_span(f"process_{task_type}_task", attributes={
            "task_id": task_id,
            "task_type": task_type
        }) as span:
            try:
                if task_type == "embedding":
                    await self._process_embedding_task(task)
                elif task_type == "cache_update":
                    await self._process_cache_update_task(task)
                elif task_type == "health_check":
                    await self._process_health_check_task(task)
                else:
                    default_logger.warning(f"Unknown task type: {task_type}")
                    span.set_attribute("error", f"Unknown task type: {task_type}")
            except Exception as e:
                default_logger.error(f"Error processing {task_type} task: {e}")
                span.set_attribute("error", str(e)[:100])
    
    async def _process_embedding_task(self, task: Dict[str, Any]):
        """Process an embedding task.
        
        Args:
            task: The embedding task
        """
        request_id = task.get("request_id")
        query = task.get("query")
        
        if not request_id or not query:
            default_logger.error("Missing required fields for embedding task")
            return
        
        try:
            # Get services
            cache_service = container.get_cache_service()
            repository = container.get_repository()
            
            # Compute embedding
            embedding = cache_service.embed_text(query)
            
            # Update request log with embedding
            repository.update_request_log_embedding(request_id, embedding)
            
            default_logger.info(f"Processed embedding task for request {request_id}")
        except Exception as e:
            default_logger.error(f"Error processing embedding task: {e}")
    
    async def _process_cache_update_task(self, task: Dict[str, Any]):
        """Process a cache update task.
        
        Args:
            task: The cache update task
        """
        query = task.get("query")
        answer = task.get("answer")
        model_id = task.get("model_id")
        
        if not query or not answer or not model_id:
            default_logger.error("Missing required fields for cache update task")
            return
        
        try:
            # Get services
            cache_service = container.get_cache_service()
            
            # Compute embedding
            embedding = cache_service.embed_text(query)
            
            # Update cache
            cache_service.upsert_cache(query, embedding, answer, model_id)
            
            default_logger.info(f"Processed cache update task for model {model_id}")
        except Exception as e:
            default_logger.error(f"Error processing cache update task: {e}")
    
    async def _process_health_check_task(self, task: Dict[str, Any]):
        """Process a health check task.
        
        Args:
            task: The health check task
        """
        model_id = task.get("model_id")
        
        try:
            # Get services
            model_service = container.get_model_service()
            
            # Perform health check (placeholder)
            model = model_service.get_model_by_id(model_id)
            if model:
                default_logger.info(f"Health check passed for model {model_id}")
            else:
                default_logger.warning(f"Model {model_id} not found during health check")
        except Exception as e:
            default_logger.error(f"Error processing health check task: {e}")
    
    def queue_embedding_task(self, request_id: str, query: str):
        """Queue a task to compute embedding and update log.
        
        Args:
            request_id: The request ID
            query: The query text
        """
        task = {
            "type": "embedding",
            "id": f"embedding-{request_id}",
            "request_id": request_id,
            "query": query,
            "timestamp": time.time()
        }
        self.task_queue.append(task)
        default_logger.debug(f"Queued embedding task for request {request_id}")
    
    def queue_cache_update_task(self, query: str, answer: str, model_id: str):
        """Queue a task to update cache.
        
        Args:
            query: The query text
            answer: The answer text
            model_id: The model ID
        """
        task = {
            "type": "cache_update",
            "id": f"cache-{int(time.time() * 1000)}",
            "query": query,
            "answer": answer,
            "model_id": model_id,
            "timestamp": time.time()
        }
        self.task_queue.append(task)
        default_logger.debug(f"Queued cache update task for model {model_id}")
    
    def queue_health_check_task(self, model_id: str):
        """Queue a task to check model health.
        
        Args:
            model_id: The model ID
        """
        task = {
            "type": "health_check",
            "id": f"health-{model_id}-{int(time.time() * 1000)}",
            "model_id": model_id,
            "timestamp": time.time()
        }
        self.task_queue.append(task)
        default_logger.debug(f"Queued health check task for model {model_id}")
    
    def get_queue_size(self) -> int:
        """Get the current queue size.
        
        Returns:
            The number of tasks in the queue
        """
        return len(self.task_queue)
    
    def stop(self):
        """Stop the background worker."""
        self.running = False
        default_logger.info("Background task worker stopped")


# Create a global instance of BackgroundTaskService
background_task_service = BackgroundTaskService()
