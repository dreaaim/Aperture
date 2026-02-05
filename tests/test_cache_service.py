"""Unit tests for cache service.

This module contains unit tests for the CacheService class, testing:
- Text embedding generation
- Similarity search in cache
- Cache entry management

The tests verify that the cache service correctly handles text embedding,
finds similar cache entries, and properly stores cache entries.
"""

import asyncio
from app.services.cache_service import CacheService
from app.repositories.memory_repository import MemoryRepository


def test_embed_text() -> None:
    """Test text embedding generation.
    
    This test verifies that the embed_text method correctly generates
    a valid embedding vector from input text.
    
    Test steps:
    1. Create a MemoryRepository instance
    2. Create a CacheService instance with the repository
    3. Generate an embedding for test text
    4. Verify the embedding is not None
    5. Verify the embedding is a list
    6. Verify all elements in the embedding are floats
    """
    # Create repository and service instances
    repository = MemoryRepository()
    service = CacheService(repository)
    
    # Test text for embedding generation
    text = "Test text"
    
    # Generate embedding
    embedding = service.embed_text(text)
    
    # Verify embedding properties
    assert embedding is not None
    assert isinstance(embedding, list)
    assert all(isinstance(value, float) for value in embedding)


def test_find_similar() -> None:
    """Test finding similar cache entries.
    
    This test verifies that the find_similar method correctly finds
    a similar cache entry when given an embedding.
    
    Test steps:
    1. Create a MemoryRepository instance
    2. Create a CacheService instance with the repository
    3. Add a cache entry with a test query and embedding
    4. Find similar entry using the same embedding
    5. Verify a similar entry is found
    6. Verify the found entry matches the original
    7. Verify the similarity score is reasonable
    """
    async def test_async():
        # Create repository and service instances
        repository = MemoryRepository()
        service = CacheService(repository)
        
        # Add a cache entry
        query = "Test query"
        embedding = service.embed_text(query)
        service.upsert_cache(query, embedding, "Test answer", "gpt-4o")
        
        # Find similar entry using the same embedding
        similar_entry, similarity = await service.find_similar(query, embedding)
        
        # Verify the found entry
        assert similar_entry is not None
        assert similar_entry.query == query
        assert similar_entry.answer == "Test answer"
        # Verify similarity score is positive
        assert similarity > 0.0
    
    # Run the async test
    asyncio.run(test_async())


def test_upsert_cache() -> None:
    """Test upserting cache entries.
    
    This test verifies that the upsert_cache method correctly adds
    a cache entry to the repository.
    
    Test steps:
    1. Create a MemoryRepository instance
    2. Create a CacheService instance with the repository
    3. Add a cache entry
    4. Verify the entry was added to the repository
    5. Verify the entry properties match the input
    """
    # Create repository and service instances
    repository = MemoryRepository()
    service = CacheService(repository)
    
    # Add a cache entry
    query = "Test query"
    embedding = service.embed_text(query)
    service.upsert_cache(query, embedding, "Test answer", "gpt-4o")
    
    # Verify the entry was added
    assert len(repository.cache_entries) == 1
    
    # Verify entry properties
    assert repository.cache_entries[0].query == query
    assert repository.cache_entries[0].answer == "Test answer"
    assert repository.cache_entries[0].model_id == "gpt-4o"
