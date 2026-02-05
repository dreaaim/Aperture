"""Central configuration for the LLM gateway.

This module provides the central configuration for the LLM gateway application,
including:
- Router weights for model scoring
- Cache thresholds for similarity matching
- Model configurations for available models
- Intent keywords for intent classification
- Embedding dimensions for text embeddings

The configuration is managed using pydantic-settings, which allows for:
- Type validation of configuration values
- Default values for configuration options
- Environment variable overrides
- Nested configuration structures

Example:
    from app.config import settings
    
    # Access router weights
    print(settings.router_weights.history)  # Output: 0.35
    
    # Access cache thresholds
    print(settings.cache_thresholds.direct_hit)  # Output: 0.95
    
    # Access intent keywords
    print(settings.intent_keywords["code"])  # Output: ["代码", "python", "java", ...]
    
    # Access model catalog
    print(len(settings.model_catalog))  # Output: 4
    print(settings.model_catalog[0].model_id)  # Output: "gpt-4o"
"""

from pydantic_settings import BaseSettings
from typing import Dict, List


class RouterWeights(BaseSettings):
    """Weights used by the model scoring function.
    
    These weights determine the importance of different factors when scoring models:
    - history: Importance of historical model ratings
    - price: Importance of model price (lower price = higher score)
    - quota: Importance of remaining tokens quota
    - difficulty_match: Importance of matching model quality to task difficulty
    
    The weights should sum to approximately 1.0 for optimal results.
    """

    # Weight for historical model ratings (0-1)
    history: float = 0.35
    
    # Weight for model price (0-1)
    price: float = 0.25
    
    # Weight for remaining tokens quota (0-1)
    quota: float = 0.2
    
    # Weight for difficulty matching (0-1)
    difficulty_match: float = 0.2


class CacheThresholds(BaseSettings):
    """Similarity thresholds for cache hit and few-shot reuse.
    
    These thresholds determine how similar a query must be to a cached entry
    to trigger different cache behaviors:
    - direct_hit: Threshold for direct cache hit (return cached answer)
    - few_shot: Threshold for few-shot learning (use cached entry as context)
    
    Values should be between 0.0 and 1.0, with direct_hit > few_shot.
    """

    # Threshold for direct cache hit (0-1, higher = more strict)
    direct_hit: float = 0.95
    
    # Threshold for few-shot learning (0-1, higher = more strict)
    few_shot: float = 0.85


class ModelConfig(BaseSettings):
    """Configuration for a single model.
    
    This class defines the configuration for a single LLM model, including:
    - model_id: Unique identifier for the model
    - price_per_1k_tokens: Price per 1000 tokens (in dollars)
    - remaining_tokens: Remaining tokens quota for the model
    - quality_tier: Quality tier of the model (small, medium, large)
    - api_format: API format type (openai, claude, gemini, etc.)
    -推理_level: Support for reasoning levels (high, medium, low)
    - enabled: Whether the model is enabled
    - rate_limit: Rate limit per minute
    - max_concurrency: Maximum concurrent requests
    - timeout: Request timeout in seconds
    """

    # Unique identifier for the model
    model_id: str
    
    # Price per 1000 tokens (in dollars)
    price_per_1k_tokens: float
    
    # Remaining tokens quota for the model
    remaining_tokens: int
    
    # Quality tier of the model (small, medium, large)
    quality_tier: str
    
    # API format type
    api_format: str = "openai"
    
    # Support for reasoning levels
    reasoning_support: bool = False
    
    # Whether the model is enabled
    enabled: bool = True
    
    # Rate limit per minute
    rate_limit: int = 60
    
    # Maximum concurrent requests
    max_concurrency: int = 10
    
    # Request timeout in seconds
    timeout: int = 30


class Settings(BaseSettings):
    """Runtime settings shared across the router and cache.
    
    This class defines the main configuration for the application,
    including nested configurations for various components.
    """

    # Cache settings
    cache_thresholds: CacheThresholds = CacheThresholds()
    
    # Router settings
    router_weights: RouterWeights = RouterWeights()
    
    # Embedding settings
    # Dimension of text embeddings for semantic caching
    embedding_dim: int = 12
    
    # Intent classification settings
    # Keywords for classifying user intent
    intent_keywords: Dict[str, List[str]] = {
        "code": ["代码", "python", "java", "algorithm", "bug", "脚本"],
        "chat": ["天气", "你好", "闲聊", "心情", "笑话"],
        "reasoning": ["证明", "推理", "分析", "原因", "为什么"],
        "creative": ["写作", "故事", "创意", "营销", "文案"],
    }
    
    # Model catalog
    # List of available models with their configurations
    model_catalog: List[ModelConfig] = [
        ModelConfig(
            model_id="gpt-4o",
            price_per_1k_tokens=5.0,
            remaining_tokens=400000,
            quality_tier="large",
            api_format="openai",
            reasoning_support=True,
            enabled=True,
            rate_limit=60,
            max_concurrency=10,
            timeout=30
        ),
        ModelConfig(
            model_id="claude-3.5-sonnet",
            price_per_1k_tokens=3.5,
            remaining_tokens=300000,
            quality_tier="large",
            api_format="claude",
            reasoning_support=True,
            enabled=True,
            rate_limit=60,
            max_concurrency=10,
            timeout=30
        ),
        ModelConfig(
            model_id="gpt-4o-mini",
            price_per_1k_tokens=0.8,
            remaining_tokens=600000,
            quality_tier="medium",
            api_format="openai",
            reasoning_support=False,
            enabled=True,
            rate_limit=120,
            max_concurrency=20,
            timeout=20
        ),
        ModelConfig(
            model_id="llama-3-8b",
            price_per_1k_tokens=0.2,
            remaining_tokens=1000000,
            quality_tier="small",
            api_format="openai",
            reasoning_support=False,
            enabled=True,
            rate_limit=240,
            max_concurrency=30,
            timeout=15
        ),
    ]
    
    # Database configuration
    # PostgreSQL connection string
    database_url: str = "postgresql://postgres:postgres@localhost:5432/aperture"
    
    class Config:
        """Pydantic settings configuration.
        
        This class configures how pydantic loads and processes settings:
        - env_file: Path to .env file for environment variable overrides
        - env_nested_delimiter: Delimiter for nested environment variables
        """
        # Path to .env file
        env_file = ".env"
        
        # Delimiter for nested environment variables
        # Example: CACHE_THRESHOLDS__DIRECT_HIT=0.9
        env_nested_delimiter = "__"


# Create a global settings instance
# This instance is imported and used throughout the application
settings = Settings()
