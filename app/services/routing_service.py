"""Intelligent routing service for model selection.

This module provides an intelligent routing service that implements weighted random routing
and other advanced routing strategies for model selection.

The RoutingService class handles:
- Weighted random routing
- Model health checks
- Load balancing
- Priority-based routing

Example:
    from app.services.routing_service import RoutingService
    from app.services.model_service import ModelService
    from app.repositories.memory_repository import MemoryRepository
    
    repository = MemoryRepository()
    model_service = ModelService(repository)
    routing_service = RoutingService(model_service)
    
    # Get a model using weighted routing
    model = routing_service.get_model_by_weight("code")
"""

import random
from typing import List, Optional, Dict, Any
from app.services.model_service import ModelService
from app.models import ModelStatus
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


class RoutingService:
    """Intelligent routing service for model selection."""
    
    def __init__(self, model_service: ModelService):
        """Initialize the routing service.
        
        Args:
            model_service: The model service instance
        """
        self.model_service = model_service
    
    def get_model_by_weight(self, intent: str, reasoning_level: Optional[str] = None) -> ModelStatus:
        """Get a model using weighted random routing.
        
        Args:
            intent: The intent category
            reasoning_level: Optional reasoning level
            
        Returns:
            A model selected based on weights
        """
        with tracer.start_as_current_span("get_model_by_weight", attributes={
            "intent": intent,
            "reasoning_level": reasoning_level or "medium"
        }) as span:
            # Get available models
            available_models = self.model_service.get_available_models()
            
            # Filter models based on reasoning level support
            if reasoning_level and reasoning_level != "medium":
                available_models = [model for model in available_models if model.reasoning_support]
            
            if not available_models:
                span.set_attribute("no_models_available", True)
                # Fallback to default model selection
                return self.model_service.select_model(intent, reasoning_level)
            
            # Calculate weights based on model properties
            weighted_models = []
            total_weight = 0.0
            
            for model in available_models:
                # Calculate weight based on multiple factors
                weight = self._calculate_model_weight(model, intent)
                weighted_models.append((model, weight))
                total_weight += weight
            
            # Perform weighted random selection
            selected_model = self._weighted_random_selection(weighted_models, total_weight)
            
            # Set reasoning level if provided
            if reasoning_level:
                selected_model.reasoning_level = reasoning_level
            
            # Set span attributes
            span.set_attribute("selected_model_id", selected_model.model_id)
            span.set_attribute("selected_model_weight", next(w for m, w in weighted_models if m.model_id == selected_model.model_id))
            span.set_attribute("model_count", len(available_models))
            
            return selected_model
    
    def _calculate_model_weight(self, model: ModelStatus, intent: str) -> float:
        """Calculate weight for a model based on its properties and intent.
        
        Args:
            model: The model to calculate weight for
            intent: The intent category
            
        Returns:
            The calculated weight
        """
        weight = 1.0
        
        # Quality tier weight
        tier_weights = {
            "large": 1.5,
            "medium": 1.0,
            "small": 0.6
        }
        weight *= tier_weights.get(model.quality_tier, 1.0)
        
        # Price weight (inverse)
        price_weight = max(0.5, 1.0 / (model.price_per_1k_tokens / 10 + 1))
        weight *= price_weight
        
        # Quota weight
        quota_weight = min(1.5, model.remaining_tokens / 100000)
        weight *= quota_weight
        
        # Intent-specific adjustments
        if intent == "code" and model.quality_tier == "large":
            weight *= 1.2
        elif intent == "chat" and model.quality_tier == "small":
            weight *= 1.1
        
        # API format adjustments
        if model.api_format == "openai":
            weight *= 1.1  # Slightly prefer OpenAI for compatibility
        
        return weight
    
    def _weighted_random_selection(self, weighted_models: List[tuple], total_weight: float) -> ModelStatus:
        """Perform weighted random selection.
        
        Args:
            weighted_models: List of (model, weight) tuples
            total_weight: Total weight
            
        Returns:
            The selected model
        """
        if not weighted_models:
            raise ValueError("No models to select from")
        
        if total_weight <= 0:
            # Fallback to random selection
            return random.choice([m for m, w in weighted_models])
        
        # Generate a random number between 0 and total_weight
        r = random.uniform(0, total_weight)
        
        # Select the model based on the random number
        current_weight = 0.0
        for model, weight in weighted_models:
            current_weight += weight
            if r <= current_weight:
                return model
        
        # Fallback to the last model
        return weighted_models[-1][0]
    
    def get_models_by_priority(self, intent: str, limit: int = 3) -> List[ModelStatus]:
        """Get models ordered by priority.
        
        Args:
            intent: The intent category
            limit: Maximum number of models to return
            
        Returns:
            A list of models ordered by priority
        """
        with tracer.start_as_current_span("get_models_by_priority", attributes={
            "intent": intent,
            "limit": limit
        }) as span:
            # Get available models
            available_models = self.model_service.get_available_models()
            
            # Calculate weights
            weighted_models = []
            for model in available_models:
                weight = self._calculate_model_weight(model, intent)
                weighted_models.append((model, weight))
            
            # Sort by weight (descending)
            weighted_models.sort(key=lambda x: x[1], reverse=True)
            
            # Get top models
            top_models = [m for m, w in weighted_models[:limit]]
            
            # Set span attributes
            span.set_attribute("top_model_ids", [m.model_id for m in top_models])
            span.set_attribute("model_count", len(available_models))
            
            return top_models
