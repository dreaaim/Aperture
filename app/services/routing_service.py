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
import time
import asyncio
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.services.model_service import ModelService
from app.services.enhanced_intent_service import EnhancedIntentService
from app.services.cost_optimization_service import CostOptimizationService
from app.models import ModelStatus
from app.utils.telemetry import get_tracer
from app.config import settings

# Get OpenTelemetry tracer
tracer = get_tracer()


class RoutingService:
    """Intelligent routing service for model selection."""
    
    def __init__(self, model_service: ModelService, cost_optimization_service: Optional[CostOptimizationService] = None):
        """Initialize the routing service.
        
        Args:
            model_service: The model service instance
            cost_optimization_service: Optional cost optimization service
        """
        self.model_service = model_service
        self.intent_service = EnhancedIntentService()
        self.cost_optimization_service = cost_optimization_service
        self.active_requests: Dict[str, int] = {}  # 活跃请求计数
        self.model_health: Dict[str, bool] = {}  # 模型健康状态
    
    def get_intent_complexity(self, query: str) -> float:
        """Calculate intent complexity score based on query.
        
        Args:
            query: The user query string
            
        Returns:
            A complexity score between 0.0 and 1.0
        """
        with tracer.start_as_current_span("get_intent_complexity", attributes={
            "query": query[:50]
        }) as span:
            # Get intent classification
            intent_result = self.intent_service.classify_intent(query)
            intent = intent_result.get("intent", "general")
            confidence = intent_result.get("confidence", 0.5)
            
            # Map intent to base complexity
            complexity_map = {
                "code": 0.8,
                "reasoning": 0.7,
                "creative": 0.6,
                "chat": 0.3,
                "general": 0.4
            }
            
            base_complexity = complexity_map.get(intent, 0.4)
            # Adjust based on confidence
            complexity = base_complexity * (0.5 + confidence * 0.5)
            
            # Set span attributes
            span.set_attribute("intent", intent)
            span.set_attribute("confidence", confidence)
            span.set_attribute("complexity", complexity)
            
            return complexity
    
    def get_model_by_weight(self, intent: str, reasoning_level: Optional[str] = None, complexity: Optional[float] = None) -> ModelStatus:
        """Get a model using weighted random routing.
        
        Args:
            intent: The intent category
            reasoning_level: Optional reasoning level
            complexity: Optional complexity score (0.0-1.0)
            
        Returns:
            A model selected based on weights
        """
        with tracer.start_as_current_span("get_model_by_weight", attributes={
            "intent": intent,
            "reasoning_level": reasoning_level or "medium",
            "complexity": complexity or 0.5
        }) as span:
            # Get available models
            available_models = self.model_service.get_available_models()
            
            # Filter out unhealthy models
            available_models = [model for model in available_models if self.model_health.get(model.model_id, True)]
            
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
                weight = self._calculate_model_weight(model, intent, complexity)
                weighted_models.append((model, weight))
                total_weight += weight
            
            # Perform weighted random selection
            selected_model = self._weighted_random_selection(weighted_models, total_weight)
            
            # Set reasoning level if provided
            if reasoning_level:
                selected_model.reasoning_level = reasoning_level
            
            # Increment active requests
            self.active_requests[selected_model.model_id] = self.active_requests.get(selected_model.model_id, 0) + 1
            
            # Set span attributes
            span.set_attribute("selected_model_id", selected_model.model_id)
            span.set_attribute("selected_model_weight", next(w for m, w in weighted_models if m.model_id == selected_model.model_id))
            span.set_attribute("model_count", len(available_models))
            span.set_attribute("active_requests", self.active_requests.get(selected_model.model_id, 0))
            
            return selected_model
    
    async def get_model_with_cost_optimization(self, query: str, intent: str, 
                                             reasoning_level: Optional[str] = None, 
                                             budget_constraint: Optional[float] = None) -> ModelStatus:
        """Get a model using cost optimization.
        
        Args:
            query: The user query
            intent: The intent category
            reasoning_level: Optional reasoning level
            budget_constraint: Optional budget constraint per request
            
        Returns:
            A model selected based on cost optimization
        """
        with tracer.start_as_current_span("get_model_with_cost_optimization", attributes={
            "intent": intent,
            "reasoning_level": reasoning_level or "medium",
            "budget_constraint": budget_constraint or 0
        }) as span:
            # Calculate complexity if not provided
            complexity = self.get_intent_complexity(query)
            
            # Use cost optimization service if available
            if self.cost_optimization_service:
                try:
                    # Get model recommendations
                    recommendations = await self.cost_optimization_service.get_model_recommendations(
                        query=query,
                        intent=intent,
                        complexity=complexity,
                        budget_constraint=budget_constraint,
                        max_recommendations=3
                    )
                    
                    if recommendations:
                        # Get recommended model IDs
                        recommended_model_ids = [rec.model_id for rec in recommendations if rec.is_recommended]
                        
                        if recommended_model_ids:
                            # Get available models from model service
                            available_models = self.model_service.get_available_models()
                            
                            # Filter by recommended models and health status
                            healthy_models = [
                                model for model in available_models 
                                if model.model_id in recommended_model_ids 
                                and self.model_health.get(model.model_id, True)
                            ]
                            
                            if healthy_models:
                                # Select the first healthy recommended model
                                selected_model = healthy_models[0]
                                span.set_attribute("cost_optimized", True)
                                span.set_attribute("recommendations_count", len(recommendations))
                            else:
                                # Fallback to weighted selection
                                selected_model = self.get_model_by_weight(intent, reasoning_level, complexity)
                                span.set_attribute("fallback_to_weighted", True)
                        else:
                            # Fallback to weighted selection
                            selected_model = self.get_model_by_weight(intent, reasoning_level, complexity)
                            span.set_attribute("no_recommendations", True)
                    else:
                        # Fallback to weighted selection
                        selected_model = self.get_model_by_weight(intent, reasoning_level, complexity)
                        span.set_attribute("no_recommendations", True)
                except Exception as e:
                    # Fallback to weighted selection on error
                    span.set_attribute("cost_optimization_error", str(e))
                    selected_model = self.get_model_by_weight(intent, reasoning_level, complexity)
            else:
                # Fallback to weighted selection if cost optimization service not available
                selected_model = self.get_model_by_weight(intent, reasoning_level, complexity)
                span.set_attribute("cost_optimization_unavailable", True)
            
            # Set reasoning level if provided
            if reasoning_level:
                selected_model.reasoning_level = reasoning_level
            
            # Increment active requests
            self.active_requests[selected_model.model_id] = self.active_requests.get(selected_model.model_id, 0) + 1
            
            # Set span attributes
            span.set_attribute("selected_model_id", selected_model.model_id)
            span.set_attribute("complexity", complexity)
            span.set_attribute("active_requests", self.active_requests.get(selected_model.model_id, 0))
            
            return selected_model
    
    def _calculate_model_weight(self, model: ModelStatus, intent: str, complexity: Optional[float] = None) -> float:
        """Calculate weight for a model based on its properties and intent.
        
        Args:
            model: The model to calculate weight for
            intent: The intent category
            complexity: Optional complexity score (0.0-1.0)
            
        Returns:
            The calculated weight
        """
        complexity = complexity or 0.5
        
        # Get weights from settings
        weights = settings.router_weights
        
        # 1. Historical satisfaction (0-1)
        # Using model rating as satisfaction score
        f_sat = getattr(model, 'rating', 0.8)  # Default to 0.8 for new models (cold start)
        
        # 2. Price factor (normalized)
        # Get all models to find price range
        all_models = self.model_service.get_available_models()
        if all_models:
            min_price = min(m.price_per_1k_tokens for m in all_models if m.price_per_1k_tokens > 0)
            max_price = max(m.price_per_1k_tokens for m in all_models)
            if max_price > min_price:
                # Normalize price: lower price = higher score
                f_cost = 1.0 - ((model.price_per_1k_tokens - min_price) / (max_price - min_price))
            else:
                f_cost = 1.0
        else:
            f_cost = 1.0
        
        # 3. Quota health (remaining tokens / total limit)
        total_limit = getattr(model, 'total_limit', 1000000)  # Default total limit
        f_budget = min(1.0, model.remaining_tokens / total_limit) if total_limit > 0 else 0.5
        
        # 4. Concurrency factor (active requests penalty)
        active_requests = self.active_requests.get(model.model_id, 0)
        max_concurrency = getattr(model, 'max_concurrency', 10)
        # Normalize active requests to 0-1 range
        concurrency_ratio = min(1.0, active_requests / max_concurrency)
        concurrency_penalty = 1.0 - (concurrency_ratio * 0.5)  # Max 50% penalty
        
        # 5. Quality tier matching
        tier_score = 1.0
        tier_match = {
            "large": 1.0 + complexity * 0.5,  # Higher complexity prefers larger models
            "medium": 1.0,
            "small": 1.0 - complexity * 0.3  # Lower complexity can use smaller models
        }
        tier_score = tier_match.get(model.quality_tier, 1.0)
        
        # Dynamic weight adjustment based on complexity
        # For high complexity, prioritize satisfaction and quality
        # For low complexity, prioritize cost efficiency
        adjusted_weights = {
            "satisfaction": weights.history * (1 + complexity * 0.5),
            "cost": weights.price * (1 - complexity * 0.3),
            "quota": weights.quota,
            "quality": weights.difficulty_match * (1 + complexity * 0.4)
        }
        
        # Calculate final score
        score = (
            adjusted_weights["satisfaction"] * f_sat +
            adjusted_weights["cost"] * f_cost +
            adjusted_weights["quota"] * f_budget +
            adjusted_weights["quality"] * tier_score
        ) * concurrency_penalty
        
        # Intent-specific adjustments
        if intent == "code" and model.quality_tier == "large":
            score *= 1.2
        elif intent == "chat" and model.quality_tier == "small":
            score *= 1.1
        
        # API format adjustments
        if model.api_format == "openai":
            score *= 1.1  # Slightly prefer OpenAI for compatibility
        
        # Ensure score is always positive
        if score <= 0:
            # Fallback to a base score based on quality tier
            tier_base_score = {
                "large": 0.8,
                "medium": 0.6,
                "small": 0.4
            }
            score = tier_base_score.get(model.quality_tier, 0.5)
        
        return score
    
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.5, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def execute_with_fallback(self, model_id: str, messages: list) -> dict:
        """Execute model call with automatic retry and fallback.
        
        Args:
            model_id: The model ID to call
            messages: The messages to send
            
        Returns:
            The model response
        """
        with tracer.start_as_current_span("execute_with_fallback", attributes={
            "model_id": model_id
        }) as span:
            try:
                # Get the model adapter and execute
                # Note: This is a placeholder, actual implementation would use the adapter factory
                # For now, we'll simulate a successful response
                span.set_attribute("attempt", 1)
                
                # Simulate model execution
                await asyncio.sleep(0.01)  # Simulate network delay
                
                # Decrement active requests
                if model_id in self.active_requests:
                    self.active_requests[model_id] -= 1
                    if self.active_requests[model_id] <= 0:
                        del self.active_requests[model_id]
                
                # Mark model as healthy
                self.model_health[model_id] = True
                
                # Return mock response
                response = {
                    "model": model_id,
                    "text": "This is a mock response from the model",
                    "usage": {
                        "total_tokens": 100
                    }
                }
                
                span.set_attribute("success", True)
                span.set_attribute("response_model", model_id)
                
                return response
                
            except Exception as e:
                span.set_attribute("error", str(e))
                
                # Mark model as unhealthy
                self.model_health[model_id] = False
                
                # Decrement active requests
                if model_id in self.active_requests:
                    self.active_requests[model_id] -= 1
                    if self.active_requests[model_id] <= 0:
                        del self.active_requests[model_id]
                
                # Circuit breaker: Mark model as temporarily unavailable
                await self._circuit_break(model_id)
                
                # Fallback to default model
                span.set_attribute("fallback", True)
                fallback_model = "gpt-4o-mini"
                
                # Decrement active requests for fallback
                if fallback_model in self.active_requests:
                    self.active_requests[fallback_model] -= 1
                    if self.active_requests[fallback_model] <= 0:
                        del self.active_requests[fallback_model]
                
                # Return mock fallback response
                return {
                    "model": fallback_model,
                    "text": "This is a fallback response from the default model",
                    "usage": {
                        "total_tokens": 100
                    }
                }
    
    async def _circuit_break(self, model_id: str):
        """Mark a model as temporarily unavailable (circuit breaker).
        
        Args:
            model_id: The model ID to mark as unavailable
        """
        # Placeholder for circuit breaker implementation
        # In a real system, this would:
        # 1. Set a timeout in Redis for the model
        # 2. Track failure counts
        # 3. Implement half-open state for recovery testing
        self.model_health[model_id] = False
        # Simulate circuit breaker timeout
        await asyncio.sleep(0.1)
    
    def get_models_by_priority(self, intent: str, limit: int = 3, complexity: Optional[float] = None) -> List[ModelStatus]:
        """Get models ordered by priority.
        
        Args:
            intent: The intent category
            limit: Maximum number of models to return
            complexity: Optional complexity score (0.0-1.0)
            
        Returns:
            A list of models ordered by priority
        """
        with tracer.start_as_current_span("get_models_by_priority", attributes={
            "intent": intent,
            "limit": limit,
            "complexity": complexity or 0.5
        }) as span:
            # Get available models
            available_models = self.model_service.get_available_models()
            
            # Filter out unhealthy models
            available_models = [model for model in available_models if self.model_health.get(model.model_id, True)]
            
            # Calculate weights
            weighted_models = []
            for model in available_models:
                weight = self._calculate_model_weight(model, intent, complexity)
                weighted_models.append((model, weight))
            
            # Sort by weight (descending)
            weighted_models.sort(key=lambda x: x[1], reverse=True)
            
            # Get top models
            top_models = [m for m, w in weighted_models[:limit]]
            
            # Set span attributes
            span.set_attribute("top_model_ids", [m.model_id for m in top_models])
            span.set_attribute("model_count", len(available_models))
            
            return top_models
