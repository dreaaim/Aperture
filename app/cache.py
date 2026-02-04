"""Semantic cache utilities for the routing prototype.

This module provides utilities for semantic caching, including:
- Text embedding generation for semantic similarity comparison
- Similarity search in the cache
- Cache entry management

Semantic caching allows the system to find relevant cached responses
based on the meaning of the query, not just exact string matches.
"""

import hashlib

from app.config import settings
from app.models import CacheEntry
from app.storage import cosine_similarity, store


def embed_text(text: str) -> list[float]:
    """Create a deterministic embedding from text for testing and demos.
    
    This function generates a fixed-dimensional embedding vector from input text
    using SHA-256 hashing and averaging. It's designed for testing purposes only
    and doesn't use a real embedding model.
    
    Args:
        text: Input text to generate embedding for
        
    Returns:
        list[float]: Embedding vector of length settings.embedding_dim
        
    Example:
        >>> embed_text("What is the capital of France?")
        [0.456, 0.234, 0.876, ...]  # Vector of length embedding_dim
    """
    # Generate SHA-256 hash of the text to create a deterministic representation
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    
    # Normalize hash values to 0-1 range
    values = [b / 255 for b in digest]
    
    # Calculate chunk size to average values into the desired embedding dimension
    chunk_size = len(values) // settings.embedding_dim
    embeddings = []
    
    # Average chunks of the hash to create the embedding vector
    for index in range(settings.embedding_dim):
        # Extract a chunk of the hash values
        chunk = values[index * chunk_size : (index + 1) * chunk_size]
        # Calculate the average of the chunk
        embeddings.append(sum(chunk) / len(chunk))
    
    return embeddings


def find_similar(query_embedding: list[float]) -> tuple[CacheEntry | None, float]:
    """Find the most similar cache entry to the given query embedding.
    
    This function searches through all cache entries and returns the one
    with the highest cosine similarity to the provided query embedding.
    
    Args:
        query_embedding: Embedding vector of the query to search for
        
    Returns:
        tuple[CacheEntry | None, float]: A tuple containing:
            - The most similar CacheEntry or None if no entries exist
            - The similarity score (0.0 to 1.0)
        
    Example:
        >>> query_emb = embed_text("What is the capital of France?")
        >>> find_similar(query_emb)
        (CacheEntry(query="What's France's capital?", ...), 0.98)
    """
    best_entry = None
    best_score = 0.0
    
    # Iterate through all cache entries to find the most similar one
    for entry in store.cache_entries:
        # Calculate cosine similarity between query embedding and entry embedding
        score = cosine_similarity(query_embedding, entry.query_embedding)
        
        # Update best entry if current score is higher
        if score > best_score:
            best_score = score
            best_entry = entry
    
    return best_entry, best_score


def upsert_cache(query: str, query_embedding: list[float], answer: str, model_id: str) -> None:
    """Insert or update a cache entry.
    
    This function adds a new cache entry to the store. Note that this prototype
    implementation doesn't handle deduplication - it simply adds new entries.
    
    Args:
        query: Original query text
        query_embedding: Embedding vector of the query
        answer: Response answer from the model
        model_id: ID of the model that generated the answer
        
    Example:
        >>> query = "What is the capital of France?"
        >>> embedding = embed_text(query)
        >>> answer = "The capital of France is Paris."
        >>> model_id = "gpt-3.5-turbo"
        >>> upsert_cache(query, embedding, answer, model_id)
        # Cache entry added to store
    """
    # Create a new CacheEntry object with the provided data
    new_entry = CacheEntry(
        query=query,
        query_embedding=query_embedding,
        answer=answer,
        model_id=model_id,
    )
    
    # Add the new entry to the store
    store.add_cache_entry(new_entry)
