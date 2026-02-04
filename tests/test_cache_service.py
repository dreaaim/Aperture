"""Unit tests for cache service."""

from app.services.cache_service import CacheService
from app.repositories.memory_repository import MemoryRepository


def test_embed_text() -> None:
    """Test text embedding generation."""
    repository = MemoryRepository()
    service = CacheService(repository)
    
    text = "Test text"
    embedding = service.embed_text(text)
    assert embedding is not None
    assert isinstance(embedding, list)
    assert all(isinstance(value, float) for value in embedding)


def test_find_similar() -> None:
    """Test finding similar cache entries."""
    repository = MemoryRepository()
    service = CacheService(repository)
    
    # Add a cache entry
    query = "Test query"
    embedding = service.embed_text(query)
    service.upsert_cache(query, embedding, "Test answer", "gpt-4o")
    
    # Find similar entry
    similar_entry, similarity = service.find_similar(embedding)
    assert similar_entry is not None
    assert similar_entry.query == query
    assert similar_entry.answer == "Test answer"
    assert abs(similarity - 1.0) < 1e-9  # Approximate match due to floating point precision


def test_upsert_cache() -> None:
    """Test upserting cache entries."""
    repository = MemoryRepository()
    service = CacheService(repository)
    
    # Add a cache entry
    query = "Test query"
    embedding = service.embed_text(query)
    service.upsert_cache(query, embedding, "Test answer", "gpt-4o")
    
    # Verify the entry was added
    assert len(repository.cache_entries) == 1
    assert repository.cache_entries[0].query == query
    assert repository.cache_entries[0].answer == "Test answer"
    assert repository.cache_entries[0].model_id == "gpt-4o"
