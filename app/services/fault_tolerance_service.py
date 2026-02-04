"""Fault tolerance service for model failures.

This module provides a fault tolerance service that implements automatic failover
and retry mechanisms for model failures.

The FaultToleranceService class handles:
- Automatic failover to backup models
- Retry policies
- Circuit breaker pattern
- Model health checks

Example:
    from app.services.fault_tolerance_service import FaultToleranceService
    from app.services.routing_service import RoutingService
    from app.services.model_service import ModelService
    from app.repositories.memory_repository import MemoryRepository
    
    repository = MemoryRepository()
    model_service = ModelService(repository)
    routing_service = RoutingService(model_service)
    ft_service = FaultToleranceService(routing_service)
    
    # Get a model with failover
    try:
        model = ft_service.get_model_with_failover("code")
    except Exception as e:
        print(f"All models failed: {e}")
"""

import time
from typing import List, Optional, Callable, Any
from app.services.routing_service import RoutingService
from app.models import ModelStatus
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


class ModelHealthStatus:
    """Model health status tracking."""
    
    def __init__(self, model_id: str):
        """Initialize model health status.
        
        Args:
            model_id: The model ID
        """
        self.model_id = model_id
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        self.circuit_open_time = 0
        self.health_check_interval = 30  # seconds


class FaultToleranceService:
    """Fault tolerance service for model failures."""
    
    def __init__(self, routing_service: RoutingService, max_retries: int = 3, retry_delay: float = 0.5):
        """Initialize the fault tolerance service.
        
        Args:
            routing_service: The routing service instance
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        self.routing_service = routing_service
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.model_health: dict[str, ModelHealthStatus] = {}
    
    def get_model_with_failover(self, intent: str, reasoning_level: Optional[str] = None) -> ModelStatus:
        """Get a model with automatic failover.
        
        Args:
            intent: The intent category
            reasoning_level: Optional reasoning level
            
        Returns:
            A healthy model
            
        Raises:
            Exception: If no healthy models are available
        """
        with tracer.start_as_current_span("get_model_with_failover", attributes={
            "intent": intent,
            "reasoning_level": reasoning_level or "medium",
            "max_retries": self.max_retries
        }) as span:
            # Get priority models
            priority_models = self.routing_service.get_models_by_priority(intent, limit=5)
            
            # Filter out unhealthy models
            healthy_models = self._filter_healthy_models(priority_models)
            
            if not healthy_models:
                # Try to get any available model
                span.set_attribute("no_healthy_models", True)
                healthy_models = priority_models
            
            if not healthy_models:
                raise Exception("No models available for intent: " + intent)
            
            # Try models in order of priority
            for i, model in enumerate(healthy_models):
                try:
                    span.set_attribute(f"attempt_{i}_model_id", model.model_id)
                    # Check if model is healthy
                    if self._is_model_healthy(model):
                        span.set_attribute("selected_model_id", model.model_id)
                        span.set_attribute("attempt_count", i + 1)
                        return model
                except Exception as e:
                    span.set_attribute(f"attempt_{i}_failed", True)
                    span.set_attribute(f"attempt_{i}_error", str(e)[:100])
                    self._record_model_failure(model.model_id)
                    time.sleep(self.retry_delay)
            
            # If all models failed, raise exception
            raise Exception("All models failed for intent: " + intent)
    
    def execute_with_retry(self, func: Callable, model: ModelStatus, **kwargs) -> Any:
        """Execute a function with retry mechanism.
        
        Args:
            func: The function to execute
            model: The model being used
            kwargs: Additional parameters for the function
            
        Returns:
            The result of the function
            
        Raises:
            Exception: If all retries fail
        """
        with tracer.start_as_current_span("execute_with_retry", attributes={
            "model_id": model.model_id,
            "max_retries": self.max_retries
        }) as span:
            for attempt in range(self.max_retries):
                try:
                    span.set_attribute(f"attempt_{attempt}", True)
                    result = func(**kwargs)
                    span.set_attribute("success", True)
                    span.set_attribute("attempt_count", attempt + 1)
                    # Reset failure count on success
                    self._reset_model_health(model.model_id)
                    return result
                except Exception as e:
                    span.set_attribute(f"attempt_{attempt}_failed", True)
                    span.set_attribute(f"attempt_{attempt}_error", str(e)[:100])
                    if attempt < self.max_retries - 1:
                        self._record_model_failure(model.model_id)
                        time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        span.set_attribute("all_attempts_failed", True)
                        self._record_model_failure(model.model_id)
                        raise
    
    def _filter_healthy_models(self, models: List[ModelStatus]) -> List[ModelStatus]:
        """Filter out unhealthy models.
        
        Args:
            models: List of models to filter
            
        Returns:
            List of healthy models
        """
        healthy_models = []
        for model in models:
            if self._is_model_healthy(model):
                healthy_models.append(model)
        return healthy_models
    
    def _is_model_healthy(self, model: ModelStatus) -> bool:
        """Check if a model is healthy.
        
        Args:
            model: The model to check
            
        Returns:
            True if the model is healthy, False otherwise
        """
        health_status = self.model_health.get(model.model_id)
        if not health_status:
            return True
        
        # Check circuit breaker
        if health_status.circuit_open:
            # Check if circuit should be closed
            if time.time() - health_status.circuit_open_time > health_status.health_check_interval:
                health_status.circuit_open = False
                return True
            return False
        
        # Check failure count
        if health_status.failure_count > 3:
            # Open circuit
            health_status.circuit_open = True
            health_status.circuit_open_time = time.time()
            return False
        
        return True
    
    def _record_model_failure(self, model_id: str):
        """Record a model failure.
        
        Args:
            model_id: The model ID that failed
        """
        if model_id not in self.model_health:
            self.model_health[model_id] = ModelHealthStatus(model_id)
        
        health_status = self.model_health[model_id]
        health_status.failure_count += 1
        health_status.last_failure_time = time.time()
    
    def _reset_model_health(self, model_id: str):
        """Reset model health status.
        
        Args:
            model_id: The model ID to reset
        """
        if model_id in self.model_health:
            health_status = self.model_health[model_id]
            health_status.failure_count = 0
            health_status.circuit_open = False
    
    def get_model_health_status(self, model_id: str) -> Optional[ModelHealthStatus]:
        """Get health status for a model.
        
        Args:
            model_id: The model ID
            
        Returns:
            The health status or None if not found
        """
        return self.model_health.get(model_id)
    
    def reset_all_health_statuses(self):
        """Reset all model health statuses."""
        self.model_health.clear()
