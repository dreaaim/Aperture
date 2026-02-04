"""Model management and selection service."""

from typing import Literal

from app.config import settings
from app.models import ModelStatus
from app.repositories.memory_repository import MemoryRepository


class ModelService:
    """Service for managing models and selecting the best one for a given intent."""

    def __init__(self, repository: MemoryRepository):
        """Initialize the model service with a repository."""
        self.repository = repository
        # Convert model configs to ModelStatus objects
        self.model_catalog = [
            ModelStatus(
                model_id=model.model_id,
                price_per_1k_tokens=model.price_per_1k_tokens,
                remaining_tokens=model.remaining_tokens,
                quality_tier=model.quality_tier  # type: ignore
            )
            for model in settings.model_catalog
        ]

    def estimate_difficulty(self, intent: str) -> str:
        """Estimate task difficulty based on historical ratings."""
        logs = [log for log in self.repository.request_logs if log.intent_tag == intent]
        if not logs:
            return "low"
        avg_rating = sum(log.user_rating or 3 for log in logs) / len(logs)
        if avg_rating < 3.4:
            return "high"
        return "medium"

    def score_model(self, model: ModelStatus, difficulty: str) -> float:
        """Compute a weighted score for a model given difficulty."""
        history_score = self.repository.get_model_rating(model.model_id)
        price_score = 1 / model.price_per_1k_tokens
        quota_score = model.remaining_tokens / max(1, max(m.remaining_tokens for m in self.model_catalog))
        if difficulty == "high":
            difficulty_score = 1.0 if model.quality_tier == "large" else 0.0
        elif difficulty == "medium":
            difficulty_score = 1.0 if model.quality_tier in {"medium", "large"} else 0.4
        else:
            difficulty_score = 1.0

        weights = settings.router_weights
        return (
            history_score * weights.history
            + price_score * weights.price
            + quota_score * weights.quota
            + difficulty_score * weights.difficulty_match
        )

    def select_model(self, intent: str) -> ModelStatus:
        """Select the highest scoring model for the given intent."""
        difficulty = self.estimate_difficulty(intent)
        scored = [(model, self.score_model(model, difficulty)) for model in self.model_catalog]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[0][0]


    def select_few_shot_model(self) -> ModelStatus:
        """Force a low-cost model when using few-shot cache augmentation."""
        return next(model for model in self.model_catalog if model.quality_tier == "small")
