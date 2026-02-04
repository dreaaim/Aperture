"""Unit tests for cache and routing flows."""

from fastapi.testclient import TestClient

from app.cache import embed_text, upsert_cache
from app.config import RouterWeights, settings
from app.main import app
from app.storage import store

client = TestClient(app)


def reset_settings() -> None:
    """Reset mutable settings to defaults to avoid test coupling."""
    settings.cache_thresholds.direct_hit = 0.95
    settings.cache_thresholds.few_shot = 0.85
    settings.router_weights = RouterWeights()


def reset_store() -> None:
    """Reset the in-memory store between tests."""
    store.cache_entries.clear()
    store.request_logs.clear()
    store.model_ratings.clear()


def test_cache_hit_returns_cached_answer() -> None:
    """Exact match should return cached answer with HIT status."""
    reset_store()
    reset_settings()
    query = "你好，帮我写个Python脚本"
    embedding = embed_text(query)
    upsert_cache(query, embedding, "cached-answer", "gpt-4o")

    response = client.post("/v1/query", json={"query": query})

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"] == "HIT"
    assert payload["answer"] == "cached-answer"
    assert payload["model_id"] == "gpt-4o"


def test_cache_few_shot_uses_small_model() -> None:
    """Few-shot path should force the small model selection."""
    reset_store()
    reset_settings()
    settings.cache_thresholds.direct_hit = 2.0
    settings.cache_thresholds.few_shot = 0.0

    seed_query = "今天天气怎么样"
    embedding = embed_text(seed_query)
    upsert_cache(seed_query, embedding, "cached-weather", "gpt-4o")

    response = client.post("/v1/query", json={"query": "今天天气如何"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"] == "FEW_SHOT"
    assert payload["model_id"] == "llama-3-8b"


def test_cache_miss_routes_with_scoring() -> None:
    """Cache miss should route based on scoring logic."""
    reset_store()
    reset_settings()
    settings.cache_thresholds.direct_hit = 2.0
    settings.cache_thresholds.few_shot = 2.0
    settings.router_weights = RouterWeights(history=0.0, price=1.0, quota=0.0, difficulty_match=0.0)

    response = client.post("/v1/query", json={"query": "简单闲聊"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"] == "MISS"
    assert payload["model_id"] == "llama-3-8b"
