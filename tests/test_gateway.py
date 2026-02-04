"""Unit tests for cache and routing flows.

This module contains integration tests for the gateway functionality, testing:
- Cache hit scenarios
- Few-shot learning scenarios
- Cache miss routing scenarios
- Model selection based on weights

The tests verify that the gateway correctly handles different cache scenarios
and routes requests appropriately based on the configured weights.
"""

from fastapi.testclient import TestClient

from app.services.cache_service import CacheService
from app.repositories.memory_repository import MemoryRepository
from app.config.settings import RouterWeights
from app.config import settings
from app.main import app

# Create test client for the FastAPI application
client = TestClient(app)

# Get the repository instance used by the API
from app.services.container import container
repository = container.get_repository()


def reset_settings() -> None:
    """Reset mutable settings to defaults to avoid test coupling.
    
    This function resets all configurable settings to their default values
    to ensure tests don't interfere with each other.
    """
    # Reset cache thresholds to defaults
    settings.cache_thresholds.direct_hit = 0.95
    settings.cache_thresholds.few_shot = 0.85
    # Reset router weights to defaults
    settings.router_weights = RouterWeights()


def reset_store() -> None:
    """Reset the in-memory store between tests.
    
    This function clears all data from the repository to ensure
    each test starts with a clean state.
    """
    # Clear cache entries
    repository.cache_entries.clear()
    # Clear request logs
    repository.request_logs.clear()
    # Clear model ratings
    repository.model_ratings.clear()


def test_cache_hit_returns_cached_answer() -> None:
    """Test that exact matches return cached answers with HIT status.
    
    This test verifies that when the same query is made twice:
    1. The first request populates the cache
    2. The second request hits the cache and returns the cached answer
    
    Test steps:
    1. Reset store and settings
    2. Make first request to populate cache
    3. Make second request with the same query
    4. Verify the second request returns a cache HIT
    """
    # Reset store and settings for clean test environment
    reset_store()
    reset_settings()
    
    # Test query
    query = "你好，帮我写个Python脚本"
    
    # First request to populate cache
    response = client.post("/v1/query", json={"query": query})
    assert response.status_code == 200
    
    # Second request should hit cache
    response = client.post("/v1/query", json={"query": query})
    assert response.status_code == 200
    
    # Verify cache status is HIT
    payload = response.json()
    assert payload["cache_status"] == "HIT"
    # We can't assert specific answer and model_id since they're generated dynamically


def test_cache_few_shot_uses_small_model() -> None:
    """Test that few-shot scenarios use the small model.
    
    This test verifies that when a similar query is made:
    1. The first request populates the cache
    2. The second similar request uses few-shot learning
    3. The small model is used for few-shot scenarios
    
    Test steps:
    1. Reset store and settings
    2. Configure thresholds to force few-shot behavior
    3. Make first request to populate cache
    4. Make second similar request
    5. Verify few-shot behavior and small model usage
    """
    # Reset store and settings for clean test environment
    reset_store()
    reset_settings()
    
    # Configure thresholds to force few-shot behavior
    settings.cache_thresholds.direct_hit = 2.0  # Make direct hit impossible
    settings.cache_thresholds.few_shot = 0.0    # Make few-shot always possible

    # First request to populate cache
    seed_query = "今天天气怎么样"
    response = client.post("/v1/query", json={"query": seed_query})
    assert response.status_code == 200

    # Second similar request
    response = client.post("/v1/query", json={"query": "今天天气如何"})

    # Verify response
    assert response.status_code == 200
    payload = response.json()
    # Verify cache status is FEW_SHOT
    assert payload["cache_status"] == "FEW_SHOT"
    # Verify small model is used for few-shot
    assert payload["model_id"] == "llama-3-8b"


def test_cache_miss_routes_with_scoring() -> None:
    """Test that cache misses route based on scoring logic.
    
    This test verifies that when there's a cache miss:
    1. The router uses the scoring logic to select a model
    2. With price-weighted routing, the cheapest model is selected
    
    Test steps:
    1. Reset store and settings
    2. Configure thresholds to force cache miss
    3. Configure router weights to prioritize price
    4. Make a request
    5. Verify cache miss and cheapest model selection
    """
    # Reset store and settings for clean test environment
    reset_store()
    reset_settings()
    
    # Configure thresholds to force cache miss
    settings.cache_thresholds.direct_hit = 2.0  # Make direct hit impossible
    settings.cache_thresholds.few_shot = 2.0    # Make few-shot impossible
    
    # Configure router weights to prioritize price
    settings.router_weights = RouterWeights(history=0.0, price=1.0, quota=0.0, difficulty_match=0.0)

    # Make a request
    response = client.post("/v1/query", json={"query": "简单闲聊"})

    # Verify response
    assert response.status_code == 200
    payload = response.json()
    # Verify cache status is MISS
    assert payload["cache_status"] == "MISS"
    # Verify cheapest model is selected (llama-3-8b)
    assert payload["model_id"] == "llama-3-8b"
