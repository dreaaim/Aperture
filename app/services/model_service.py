"""Model management and selection service.

This module provides a service for managing models and selecting the best one for a given intent.

The ModelService class handles:
- Loading and managing model configurations
- Estimating task difficulty based on historical ratings
- Scoring models based on multiple factors
- Selecting the best model for a given intent
- Selecting a small model for few-shot learning

Example:
    from app.services.model_service import ModelService
    from app.repositories.memory_repository import MemoryRepository
    
    repository = MemoryRepository()
    service = ModelService(repository)
    
    # Select a model for code intent
    model = service.select_model("code")
    print(model.model_id)  # Output: "gpt-4o" (or another high-quality model)
    
    # Select a small model for few-shot learning
    few_shot_model = service.select_few_shot_model()
    print(few_shot_model.model_id)  # Output: "llama-3-8b"
"""

from typing import Literal, List, Optional

from app.config import settings
from app.models import ModelStatus
from app.repositories.memory_repository import MemoryRepository
from app.utils.telemetry import get_tracer
from app.services.base_model_service import BaseModelService

# Get OpenTelemetry tracer
tracer = get_tracer()


class ModelService(BaseModelService):
    """Service for managing models and selecting the best one for a given intent.
    
    This service is responsible for loading model configurations, estimating task difficulty,
    scoring models based on multiple factors, and selecting the best model for a given intent.
    
    Attributes:
        repository: The memory repository instance for accessing request logs and model ratings
        model_catalog: A list of ModelStatus objects representing available models
    """

    def __init__(self, repository: MemoryRepository):
        """Initialize the model service with a repository.
        
        Args:
            repository: The memory repository instance for accessing request logs and model ratings
        """
        super().__init__(repository)
        # Convert model configs from settings to ModelStatus objects
        # This allows for easy access to model properties
        self.model_catalog: List[ModelStatus] = [
            ModelStatus(
                model_id=model.model_id,
                model_type=getattr(model, 'model_type', 'llm'),
                price_per_1k_tokens=model.price_per_1k_tokens,
                remaining_tokens=model.remaining_tokens,
                quality_tier=model.quality_tier,  # type: ignore
                api_format=model.api_format,
                reasoning_support=model.reasoning_support,
                enabled=model.enabled,
                rate_limit=model.rate_limit,
                max_concurrency=model.max_concurrency,
                timeout=model.timeout,
                embedding_dimension=getattr(model, 'embedding_dimension', 1024),
                max_input_length=getattr(model, 'max_input_length', 4096)
            )
            for model in settings.model_catalog
        ]

    def estimate_difficulty(self, intent: str) -> str:
        """Estimate task difficulty based on historical ratings.
        
        Args:
            intent: The intent category to estimate difficulty for
            
        Returns:
            The estimated difficulty level as a string
            Possible values: "low", "medium", "high"
            
        Example:
            >>> service = ModelService(repository)
            >>> service.estimate_difficulty("code")
            "medium"
            
            >>> service.estimate_difficulty("chat")
            "low"
        """
        # Create span for difficulty estimation
        with tracer.start_as_current_span("estimate_difficulty", attributes={
            "intent": intent
        }) as span:
            # Get request logs for the given intent
            logs = [log for log in self.repository.request_logs if log.intent_tag == intent]
            
            # If no logs exist for this intent, default to low difficulty
            if not logs:
                span.set_attribute("difficulty", "low")
                span.set_attribute("has_history", False)
                return "low"
            
            # Calculate average user rating (default to 3 if no rating)
            avg_rating = sum(log.user_rating or 3 for log in logs) / len(logs)
            
            # Determine difficulty based on average rating
            # Lower rating indicates higher difficulty (users are less satisfied)
            if avg_rating < 3.4:
                difficulty = "high"
            else:
                difficulty = "medium"
            
            # Set span attributes
            span.set_attribute("difficulty", difficulty)
            span.set_attribute("has_history", True)
            span.set_attribute("log_count", len(logs))
            span.set_attribute("average_rating", avg_rating)
            
            return difficulty

    def score_model(self, model: ModelStatus, difficulty: str) -> float:
        """Compute a weighted score for a model given difficulty.
        
        Args:
            model: The model to score
            difficulty: The estimated difficulty level ("low", "medium", "high")
            
        Returns:
            The weighted score for the model (higher is better)
            
        Example:
            >>> service = ModelService(repository)
            >>> model = service.model_catalog[0]  # gpt-4o
            >>> service.score_model(model, "high")
            0.85  # Example score
        """
        # Create span for model scoring
        with tracer.start_as_current_span("score_model", attributes={
            "model_id": model.model_id,
            "model_quality_tier": model.quality_tier,
            "difficulty": difficulty
        }) as span:
            # Get historical rating score for the model (0-1)
            history_score = self.repository.get_model_rating(model.model_id)
            
            # Apply cold start strategy for new models
            if history_score == 0.0:
                history_score = self.get_initial_model_rating(model.model_id)
                span.set_attribute("cold_start", True)
                span.set_attribute("initial_rating", history_score)
            
            # Calculate price score (inverse of price, so lower price = higher score)
            price_score = 1 / model.price_per_1k_tokens
            
            # Calculate quota score (normalized by max remaining tokens)
            max_tokens = max(1, max(m.remaining_tokens for m in self.model_catalog))
            quota_score = model.remaining_tokens / max_tokens
            
            # Calculate difficulty score based on model quality tier
            if difficulty == "high":
                # High difficulty requires large models
                difficulty_score = 1.0 if model.quality_tier == "large" else 0.0
            elif difficulty == "medium":
                # Medium difficulty can use medium or large models
                difficulty_score = 1.0 if model.quality_tier in {"medium", "large"} else 0.4
            else:
                # Low difficulty can use any model
                difficulty_score = 1.0

            # Get weights from settings
            weights = settings.router_weights
            
            # Calculate weighted sum
            score = (
                history_score * weights.history
                + price_score * weights.price
                + quota_score * weights.quota
                + difficulty_score * weights.difficulty_match
            )
            
            # Add exploration bonus for new models
            exploration_bonus = self.get_exploration_budget(model.model_id)
            score = score * (1 - exploration_bonus) + exploration_bonus * 0.7
            
            # Set span attributes
            span.set_attribute("history_score", history_score)
            span.set_attribute("price_score", price_score)
            span.set_attribute("quota_score", quota_score)
            span.set_attribute("difficulty_score", difficulty_score)
            span.set_attribute("total_score", score)
            span.set_attribute("history_weight", weights.history)
            span.set_attribute("price_weight", weights.price)
            span.set_attribute("quota_weight", weights.quota)
            span.set_attribute("difficulty_weight", weights.difficulty_match)
            span.set_attribute("exploration_bonus", exploration_bonus)
            
            return score

    def select_model(self, intent: str, reasoning_level: Optional[str] = None) -> ModelStatus:
        """Select the highest scoring model for the given intent.
        
        Args:
            intent: The intent category to select a model for
            reasoning_level: Optional reasoning level (low/medium/high)
            
        Returns:
            The best model for the given intent based on scoring
            
        Example:
            >>> service = ModelService(repository)
            >>> model = service.select_model("code")
            >>> model.model_id
            "gpt-4o"  # Example result
            
            >>> model = service.select_model("reasoning", reasoning_level="high")
            >>> model.model_id
            "gpt-4o"  # Example result
        """
        # Create span for model selection
        with tracer.start_as_current_span("select_model", attributes={
            "intent": intent,
            "reasoning_level": reasoning_level or "medium"
        }) as span:
            # Step 1: Estimate difficulty for the intent
            difficulty = self.estimate_difficulty(intent)
            span.set_attribute("difficulty", difficulty)
            
            # Step 2: Filter models based on reasoning level support
            filtered_models = [model for model in self.model_catalog if model.enabled]
            if reasoning_level and reasoning_level != "medium":
                filtered_models = [model for model in filtered_models if model.reasoning_support]
            
            # Step 3: Score all models for this difficulty
            scored_models = [(model, self.score_model(model, difficulty)) for model in filtered_models]
            
            # Step 4: Sort models by score (descending)
            scored_models.sort(key=lambda item: item[1], reverse=True)
            
            # Step 5: Return the highest scoring model
            selected_model = scored_models[0][0]
            highest_score = scored_models[0][1]
            
            # Set reasoning level if provided
            if reasoning_level:
                selected_model.reasoning_level = reasoning_level
            
            # Set span attributes
            span.set_attribute("selected_model_id", selected_model.model_id)
            span.set_attribute("selected_model_tier", selected_model.quality_tier)
            span.set_attribute("selected_model_api_format", selected_model.api_format)
            span.set_attribute("highest_score", highest_score)
            span.set_attribute("model_count", len(filtered_models))
            span.set_attribute("reasoning_level", selected_model.reasoning_level)
            
            return selected_model

    def select_few_shot_model(self) -> ModelStatus:
        """Select a small model for few-shot learning.
        
        For few-shot learning, we always use a small, cost-effective model
        regardless of the intent or difficulty.
        
        Returns:
            A small model suitable for few-shot learning
            
        Example:
            >>> service = ModelService(repository)
            >>> model = service.select_few_shot_model()
            >>> model.model_id
            "llama-3-8b"
        """
        # Create span for few-shot model selection
        with tracer.start_as_current_span("select_few_shot_model") as span:
            # Find the first model with small quality tier
            selected_model = next(model for model in self.model_catalog if model.quality_tier == "small")
            
            # Set span attributes
            span.set_attribute("selected_model_id", selected_model.model_id)
            span.set_attribute("selected_model_tier", selected_model.quality_tier)
            span.set_attribute("model_count", len(self.model_catalog))
            
            return selected_model
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelStatus]:
        """Get a model by its ID.
        
        Args:
            model_id: The ID of the model to get
            
        Returns:
            The model with the given ID, or None if not found
            
        Example:
            >>> service = ModelService(repository)
            >>> model = service.get_model_by_id("gpt-4o")
            >>> model.model_id if model else "Not found"
            "gpt-4o"
        """
        # Create span for model lookup
        with tracer.start_as_current_span("get_model_by_id", attributes={
            "model_id": model_id
        }) as span:
            for model in self.model_catalog:
                if model.model_id == model_id:
                    span.set_attribute("model_found", True)
                    span.set_attribute("model_tier", model.quality_tier)
                    span.set_attribute("model_api_format", model.api_format)
                    return model
            span.set_attribute("model_found", False)
            return None
    
    def get_initial_model_rating(self, model_id: str) -> float:
        """Get initial rating for new models (cold start strategy).
        
        Args:
            model_id: The ID of the model
            
        Returns:
            Initial rating score (0.0-1.0)
        """
        with tracer.start_as_current_span("get_initial_model_rating", attributes={
            "model_id": model_id
        }) as span:
            # Check if model exists in catalog
            model = self.get_model_by_id(model_id)
            if not model:
                span.set_attribute("model_not_found", True)
                return 0.5
            
            # Base initial rating on model tier
            tier_rating = {
                "large": 0.85,
                "medium": 0.75,
                "small": 0.65
            }
            
            initial_rating = tier_rating.get(model.quality_tier, 0.7)
            
            # Adjust based on model type
            if model.model_type == "embedding":
                initial_rating *= 0.9
            elif model.model_type == "reranker":
                initial_rating *= 0.85
            
            span.set_attribute("initial_rating", initial_rating)
            span.set_attribute("model_tier", model.quality_tier)
            
            return initial_rating
    
    def get_exploration_budget(self, model_id: str) -> float:
        """Get exploration budget for new models (Multi-Armed Bandit strategy).
        
        Args:
            model_id: The ID of the model
            
        Returns:
            Exploration budget (0.0-1.0)
        """
        with tracer.start_as_current_span("get_exploration_budget", attributes={
            "model_id": model_id
        }) as span:
            # Get model
            model = self.get_model_by_id(model_id)
            if not model:
                span.set_attribute("model_not_found", True)
                return 0.0
            
            # Check if model has historical data
            historical_rating = self.repository.get_model_rating(model_id)
            
            if historical_rating == 0.0:
                # New model, high exploration budget
                exploration_budget = 0.2  # 20% of traffic
            else:
                # Existing model, lower exploration budget
                exploration_budget = max(0.05, 0.15 * (1 - historical_rating))
            
            span.set_attribute("exploration_budget", exploration_budget)
            span.set_attribute("historical_rating", historical_rating)
            
            return exploration_budget
    
    def get_available_models(self) -> List[ModelStatus]:
        """Get all available models.
        
        Returns:
            A list of all available models
            
        Example:
            >>> service = ModelService(repository)
            >>> models = service.get_available_models()
            >>> len(models)
            4
        """
        # Create span for available models lookup
        with tracer.start_as_current_span("get_available_models") as span:
            available_models = [model for model in self.model_catalog if model.enabled]
            span.set_attribute("available_model_count", len(available_models))
            span.set_attribute("total_model_count", len(self.model_catalog))
            return available_models
    
    def update_model_status(self, model_id: str, **kwargs) -> bool:
        """Update the status of a model.
        
        Args:
            model_id: The ID of the model to update
            kwargs: The attributes to update
            
        Returns:
            True if the model was updated successfully, False otherwise
            
        Example:
            >>> service = ModelService(repository)
            >>> service.update_model_status("gpt-4o", enabled=False)
            True
        """
        # Create span for model status update
        with tracer.start_as_current_span("update_model_status", attributes={
            "model_id": model_id,
            "update_attributes": list(kwargs.keys())
        }) as span:
            for model in self.model_catalog:
                if model.model_id == model_id:
                    for key, value in kwargs.items():
                        if hasattr(model, key):
                            setattr(model, key, value)
                            span.set_attribute(f"updated_{key}", value)
                    span.set_attribute("update_success", True)
                    return True
            span.set_attribute("update_success", False)
            return False
    
    def select_embedding_model(self) -> ModelStatus:
        """Select the best embedding model.
        
        Returns:
            The best embedding model based on scoring
            
        Example:
            >>> service = ModelService(repository)
            >>> model = service.select_embedding_model()
            >>> model.model_id
            "text-embedding-3-small"
        """
        # Create span for embedding model selection
        with tracer.start_as_current_span("select_embedding_model") as span:
            # Filter enabled embedding models
            embedding_models = [model for model in self.model_catalog if model.enabled and model.model_type == "embedding"]
            
            if not embedding_models:
                span.set_attribute("error", "No embedding models available")
                raise ValueError("No embedding models available")
            
            # Score embedding models
            scored_models = []
            for model in embedding_models:
                # Calculate score based on price, quota, and quality
                price_score = 1 / model.price_per_1k_tokens
                max_tokens = max(1, max(m.remaining_tokens for m in embedding_models))
                quota_score = model.remaining_tokens / max_tokens
                quality_score = 1.0 if model.quality_tier == "large" else 0.7 if model.quality_tier == "medium" else 0.4
                
                # Calculate weighted score
                score = (
                    price_score * 0.3
                    + quota_score * 0.3
                    + quality_score * 0.4
                )
                scored_models.append((model, score))
            
            # Sort by score (descending)
            scored_models.sort(key=lambda item: item[1], reverse=True)
            
            # Return the highest scoring model
            selected_model = scored_models[0][0]
            highest_score = scored_models[0][1]
            
            # Set span attributes
            span.set_attribute("selected_model_id", selected_model.model_id)
            span.set_attribute("selected_model_tier", selected_model.quality_tier)
            span.set_attribute("selected_model_api_format", selected_model.api_format)
            span.set_attribute("highest_score", highest_score)
            span.set_attribute("model_count", len(embedding_models))
            span.set_attribute("embedding_dimension", selected_model.embedding_dimension)
            
            return selected_model
    
    def select_reranker_model(self) -> ModelStatus:
        """Select the best reranker model.
        
        Returns:
            The best reranker model based on scoring
            
        Example:
            >>> service = ModelService(repository)
            >>> model = service.select_reranker_model()
            >>> model.model_id
            "rerank-english-v3.0"
        """
        # Create span for reranker model selection
        with tracer.start_as_current_span("select_reranker_model") as span:
            # Filter enabled reranker models
            reranker_models = [model for model in self.model_catalog if model.enabled and model.model_type == "reranker"]
            
            if not reranker_models:
                span.set_attribute("error", "No reranker models available")
                raise ValueError("No reranker models available")
            
            # Score reranker models
            scored_models = []
            for model in reranker_models:
                # Calculate score based on price, quota, and quality
                price_score = 1 / model.price_per_1k_tokens
                max_tokens = max(1, max(m.remaining_tokens for m in reranker_models))
                quota_score = model.remaining_tokens / max_tokens
                quality_score = 1.0 if model.quality_tier == "large" else 0.7 if model.quality_tier == "medium" else 0.4
                
                # Calculate weighted score
                score = (
                    price_score * 0.3
                    + quota_score * 0.3
                    + quality_score * 0.4
                )
                scored_models.append((model, score))
            
            # Sort by score (descending)
            scored_models.sort(key=lambda item: item[1], reverse=True)
            
            # Return the highest scoring model
            selected_model = scored_models[0][0]
            highest_score = scored_models[0][1]
            
            # Set span attributes
            span.set_attribute("selected_model_id", selected_model.model_id)
            span.set_attribute("selected_model_tier", selected_model.quality_tier)
            span.set_attribute("selected_model_api_format", selected_model.api_format)
            span.set_attribute("highest_score", highest_score)
            span.set_attribute("model_count", len(reranker_models))
            span.set_attribute("max_input_length", selected_model.max_input_length)
            
            return selected_model
    
    def get_models_by_type(self, model_type: str) -> List[ModelStatus]:
        """Get models by type.
        
        Args:
            model_type: The type of models to get
            
        Returns:
            List of models of the specified type
            
        Example:
            >>> service = ModelService(repository)
            >>> models = service.get_models_by_type("embedding")
            >>> len(models)
            2
        """
        # Create span for models by type lookup
        with tracer.start_as_current_span("get_models_by_type", attributes={
            "model_type": model_type
        }) as span:
            models = [model for model in self.model_catalog if model.model_type == model_type]
            span.set_attribute("model_count", len(models))
            span.set_attribute("enabled_model_count", len([m for m in models if m.enabled]))
            return models
