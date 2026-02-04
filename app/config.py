"""Central configuration for cache thresholds and routing weights."""

from pydantic import BaseModel


class RouterWeights(BaseModel):
    """Weights used by the model scoring function."""

    history: float = 0.35
    price: float = 0.25
    quota: float = 0.2
    difficulty_match: float = 0.2


class CacheThresholds(BaseModel):
    """Similarity thresholds for cache hit and few-shot reuse."""

    direct_hit: float = 0.95
    few_shot: float = 0.85


class Settings(BaseModel):
    """Runtime settings shared across the router and cache."""

    cache_thresholds: CacheThresholds = CacheThresholds()
    router_weights: RouterWeights = RouterWeights()
    embedding_dim: int = 12


settings = Settings()
