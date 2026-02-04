"""Central configuration for cache thresholds and routing weights.

This module provides a centralized configuration system using Pydantic models
for managing cache similarity thresholds, model routing weights, and other
runtime settings for the LLM router.

The configuration is structured hierarchically with:
- CacheThresholds: Similarity thresholds for cache operations
- RouterWeights: Weights for model scoring factors
- Settings: Main settings container
"""

from pydantic import BaseModel


class RouterWeights(BaseModel):
    """Weights used by the model scoring function.
    
    This class defines the weights for different factors used in the
    model scoring algorithm. The weights determine the relative importance
    of each factor when calculating the overall score for a model.
    
    Fields:
        history: Weight for model performance history (default: 0.35)
        price: Weight for model price/cost (default: 0.25)
        quota: Weight for remaining quota (default: 0.2)
        difficulty_match: Weight for task difficulty match (default: 0.2)
    
    Example:
        >>> weights = RouterWeights()
        >>> weights.history
        0.35
        >>> custom_weights = RouterWeights(history=0.5, price=0.1)
        >>> custom_weights.history
        0.5
    """

    history: float = 0.35  # Weight for model performance history
    price: float = 0.25    # Weight for model price/cost
    quota: float = 0.2      # Weight for remaining quota
    difficulty_match: float = 0.2  # Weight for task difficulty match


class CacheThresholds(BaseModel):
    """Similarity thresholds for cache hit and few-shot reuse.
    
    This class defines the similarity score thresholds used to determine
    if a cache entry is relevant enough for different use cases.
    
    Fields:
        direct_hit: Threshold for direct cache hit (default: 0.95)
        few_shot: Threshold for few-shot example reuse (default: 0.85)
    
    Example:
        >>> thresholds = CacheThresholds()
        >>> thresholds.direct_hit
        0.95
        >>> custom_thresholds = CacheThresholds(direct_hit=0.9, few_shot=0.8)
        >>> custom_thresholds.few_shot
        0.8
    """

    direct_hit: float = 0.95  # Threshold for direct cache hit
    few_shot: float = 0.85    # Threshold for few-shot example reuse


class Settings(BaseModel):
    """Runtime settings shared across the router and cache.
    
    This class is the main configuration container that holds all
    runtime settings used by the router and cache components.
    
    Fields:
        cache_thresholds: Cache similarity thresholds
        router_weights: Model scoring weights
        embedding_dim: Dimension of text embeddings (default: 12)
    
    Example:
        >>> settings = Settings()
        >>> settings.embedding_dim
        12
        >>> settings.cache_thresholds.direct_hit
        0.95
    """

    cache_thresholds: CacheThresholds = CacheThresholds()  # Cache similarity thresholds
    router_weights: RouterWeights = RouterWeights()        # Model scoring weights
    embedding_dim: int = 12                                # Dimension of text embeddings


# Global settings instance used throughout the application
settings = Settings()
"""Global settings instance shared across the application.

This instance is imported by other modules to access configuration values.
"""
