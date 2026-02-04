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

from typing import Literal, List

from app.config import settings
from app.models import ModelStatus
from app.repositories.memory_repository import MemoryRepository


class ModelService:
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
        self.repository = repository
        # Convert model configs from settings to ModelStatus objects
        # This allows for easy access to model properties
        self.model_catalog: List[ModelStatus] = [
            ModelStatus(
                model_id=model.model_id,
                price_per_1k_tokens=model.price_per_1k_tokens,
                remaining_tokens=model.remaining_tokens,
                quality_tier=model.quality_tier  # type: ignore
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
        # Get request logs for the given intent
        logs = [log for log in self.repository.request_logs if log.intent_tag == intent]
        
        # If no logs exist for this intent, default to low difficulty
        if not logs:
            return "low"
        
        # Calculate average user rating (default to 3 if no rating)
        avg_rating = sum(log.user_rating or 3 for log in logs) / len(logs)
        
        # Determine difficulty based on average rating
        # Lower rating indicates higher difficulty (users are less satisfied)
        if avg_rating < 3.4:
            return "high"
        return "medium"

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
        # Get historical rating score for the model (0-1)
        history_score = self.repository.get_model_rating(model.model_id)
        
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
        return (
            history_score * weights.history
            + price_score * weights.price
            + quota_score * weights.quota
            + difficulty_score * weights.difficulty_match
        )

    def select_model(self, intent: str) -> ModelStatus:
        """Select the highest scoring model for the given intent.
        
        Args:
            intent: The intent category to select a model for
            
        Returns:
            The best model for the given intent based on scoring
            
        Example:
            >>> service = ModelService(repository)
            >>> model = service.select_model("code")
            >>> model.model_id
            "gpt-4o"  # Example result
        """
        # Step 1: Estimate difficulty for the intent
        difficulty = self.estimate_difficulty(intent)
        
        # Step 2: Score all models for this difficulty
        scored_models = [(model, self.score_model(model, difficulty)) for model in self.model_catalog]
        
        # Step 3: Sort models by score (descending)
        scored_models.sort(key=lambda item: item[1], reverse=True)
        
        # Step 4: Return the highest scoring model
        return scored_models[0][0]

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
        # Find the first model with small quality tier
        return next(model for model in self.model_catalog if model.quality_tier == "small")
