"""Central configuration for the LLM gateway."""

from pydantic_settings import BaseSettings
from typing import Dict, List


class RouterWeights(BaseSettings):
    """Weights used by the model scoring function."""

    history: float = 0.35
    price: float = 0.25
    quota: float = 0.2
    difficulty_match: float = 0.2


class CacheThresholds(BaseSettings):
    """Similarity thresholds for cache hit and few-shot reuse."""

    direct_hit: float = 0.95
    few_shot: float = 0.85


class ModelConfig(BaseSettings):
    """Configuration for a single model."""

    model_id: str
    price_per_1k_tokens: float
    remaining_tokens: int
    quality_tier: str


class Settings(BaseSettings):
    """Runtime settings shared across the router and cache."""

    # Cache settings
    cache_thresholds: CacheThresholds = CacheThresholds()
    
    # Router settings
    router_weights: RouterWeights = RouterWeights()
    
    # Embedding settings
    embedding_dim: int = 12
    
    # Intent classification settings
    intent_keywords: Dict[str, List[str]] = {
        "code": ["代码", "python", "java", "algorithm", "bug", "脚本"],
        "chat": ["天气", "你好", "闲聊", "心情", "笑话"],
        "reasoning": ["证明", "推理", "分析", "原因", "为什么"],
        "creative": ["写作", "故事", "创意", "营销", "文案"],
    }
    
    # Model catalog
    model_catalog: List[ModelConfig] = [
        ModelConfig(
            model_id="gpt-4o",
            price_per_1k_tokens=5.0,
            remaining_tokens=400000,
            quality_tier="large",
        ),
        ModelConfig(
            model_id="claude-3.5-sonnet",
            price_per_1k_tokens=3.5,
            remaining_tokens=300000,
            quality_tier="large",
        ),
        ModelConfig(
            model_id="gpt-4o-mini",
            price_per_1k_tokens=0.8,
            remaining_tokens=600000,
            quality_tier="medium",
        ),
        ModelConfig(
            model_id="llama-3-8b",
            price_per_1k_tokens=0.2,
            remaining_tokens=1000000,
            quality_tier="small",
        ),
    ]
    
    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_nested_delimiter = "__"


settings = Settings()
