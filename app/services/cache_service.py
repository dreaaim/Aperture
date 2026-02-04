"""Cache service for semantic caching.

This module provides a service for managing semantic cache operations, including:
- Generating text embeddings for queries
- Finding similar entries in the cache
- Adding new entries to the cache

The CacheService class uses a deterministic hashing approach for generating embeddings
(which is suitable for testing and demos) and cosine similarity for finding similar entries.

Example:
    from app.services.cache_service import CacheService
    from app.repositories.memory_repository import MemoryRepository
    
    repository = MemoryRepository()
    service = CacheService(repository)
    
    # Generate embedding for a query
    query = "帮我写个Python脚本"
    embedding = service.embed_text(query)
    
    # Add to cache
    service.upsert_cache(query, embedding, "这是一个Python脚本", "gpt-4o")
    
    # Find similar entry
    similar_query = "帮我写个Python程序"
    similar_embedding = service.embed_text(similar_query)
    cached_entry, similarity = service.find_similar(similar_embedding)
    
    print(cached_entry.query)  # Output: "帮我写个Python脚本"
    print(cached_entry.answer)  # Output: "这是一个Python脚本"
    print(similarity)  # Output: Similarity score (e.g., 0.95)
"""

import hashlib
from typing import List, Tuple, Optional

from app.config import settings
from app.models import CacheEntry
from app.repositories.memory_repository import MemoryRepository
from app.utils.math import cosine_similarity


class CacheService:
    """Service for managing semantic cache operations.
    
    This service is responsible for generating text embeddings, finding similar
    cache entries, and updating the cache with new entries.
    
    Attributes:
        repository: The memory repository instance for accessing and storing cache entries
    """

    def __init__(self, repository: MemoryRepository):
        """Initialize the cache service with a repository.
        
        Args:
            repository: The memory repository instance for accessing and storing cache entries
        """
        self.repository = repository

    def embed_text(self, text: str) -> List[float]:
        """Generate a deterministic embedding from text for testing and demos.
        
        This method uses SHA-256 hashing to generate a deterministic embedding,
        which is suitable for testing and demos but not for production use.
        In a production environment, you would use a real embedding model (e.g., OpenAI Embeddings).
        
        Args:
            text: The text to embed
            
        Returns:
            A list of floats representing the embedding vector
            
        Example:
            >>> service = CacheService(repository)
            >>> embedding = service.embed_text("帮我写个Python脚本")
            >>> len(embedding)
            12  # Based on settings.embedding_dim
            >>> embedding[0]
            0.45  # Example value
        """
        # Generate SHA-256 hash of the text
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        
        # Convert bytes to float values between 0 and 1
        values = [b / 255 for b in digest]
        
        # Calculate chunk size based on desired embedding dimension
        chunk_size = len(values) // settings.embedding_dim
        embeddings = []
        
        # Average chunks to create fixed-size embedding
        for index in range(settings.embedding_dim):
            # Get the chunk of values for this index
            chunk = values[index * chunk_size : (index + 1) * chunk_size]
            # Calculate average of the chunk
            embeddings.append(sum(chunk) / len(chunk))
        
        return embeddings

    def find_similar(self, query_embedding: List[float]) -> Tuple[Optional[CacheEntry], float]:
        """Find the most similar cache entry and its similarity score.
        
        Args:
            query_embedding: The embedding vector of the query to find similar entries for
            
        Returns:
            A tuple containing:
            - The most similar CacheEntry (or None if no entries)
            - The cosine similarity score (0-1, higher is better)
            
        Example:
            >>> service = CacheService(repository)
            >>> query = "帮我写个Python脚本"
            >>> embedding = service.embed_text(query)
            >>> service.upsert_cache(query, embedding, "这是一个Python脚本", "gpt-4o")
            >>> 
            >>> similar_query = "帮我写个Python程序"
            >>> similar_embedding = service.embed_text(similar_query)
            >>> cached_entry, similarity = service.find_similar(similar_embedding)
            >>> cached_entry.query
            "帮我写个Python脚本"
            >>> similarity
            0.95  # Example similarity score
        """
        # Initialize variables to track best match
        best_entry: Optional[CacheEntry] = None
        best_score = 0.0
        
        # Iterate through all cache entries
        for entry in self.repository.cache_entries:
            # Calculate cosine similarity between query embedding and entry embedding
            score = cosine_similarity(query_embedding, entry.query_embedding)
            
            # Update best match if current entry is more similar
            if score > best_score:
                best_score = score
                best_entry = entry
        
        return best_entry, best_score

    def upsert_cache(self, query: str, query_embedding: List[float], answer: str, model_id: str) -> None:
        """Add a new entry to the cache.
        
        Note: This implementation simply adds a new entry without deduplication,
        which is suitable for testing and demos but not for production use.
        In a production environment, you would check for existing entries
        and update them if a similar entry exists.
        
        Args:
            query: The user's query string
            query_embedding: The embedding vector of the query
            answer: The generated answer
            model_id: The ID of the model used to generate the answer
            
        Example:
            >>> service = CacheService(repository)
            >>> query = "帮我写个Python脚本"
            >>> embedding = service.embed_text(query)
            >>> service.upsert_cache(query, embedding, "这是一个Python脚本", "gpt-4o")
            >>> 
            # Cache now contains this entry
            >>> len(repository.cache_entries)
            1
        """
        # Create a new CacheEntry object
        cache_entry = CacheEntry(
            query=query,
            query_embedding=query_embedding,
            answer=answer,
            model_id=model_id,
        )
        
        # Add the entry to the repository
        self.repository.add_cache_entry(cache_entry)
