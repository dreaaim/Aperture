"""In-memory storage and simple math helpers for the prototype.

This module provides:
- An in-memory storage system for cache entries and request logs
- Math utilities for vector operations like cosine similarity
- Helper functions for request ID generation

The InMemoryStore class is designed for prototype use and provides
lightweight storage without persistence. It's suitable for testing
and demonstration purposes.
"""

import math
import uuid
from collections import defaultdict

from app.models import CacheEntry, RequestLog


class InMemoryStore:
    """Lightweight in-memory storage for cached entries and request logs.
    
    This class provides a simple in-memory storage system for:
    - Cache entries for semantic lookup
    - Request logs for rating-based routing
    - Model rating history for performance evaluation
    
    Example:
        >>> store = InMemoryStore()
        >>> # Add a cache entry
        >>> entry = CacheEntry(
        ...     query="What is the capital of France?",
        ...     query_embedding=[0.1, 0.2, 0.3],
        ...     answer="Paris",
        ...     model_id="gpt-3.5-turbo"
        ... )
        >>> store.add_cache_entry(entry)
        >>> # Get model rating
        >>> store.get_model_rating("gpt-3.5-turbo")
        0.6  # Default rating
    """

    def __init__(self) -> None:
        """Initialize the in-memory store with empty collections."""
        # Cache entries for semantic lookup
        self.cache_entries: list[CacheEntry] = []
        # Logs of handled requests for rating-based routing
        self.request_logs: list[RequestLog] = []
        # Track rating history per model to compute normalized scores
        self.model_ratings: dict[str, list[int]] = defaultdict(list)

    def add_cache_entry(self, entry: CacheEntry) -> None:
        """Add a cache entry to the in-memory store.
        
        Args:
            entry: CacheEntry object to add
            
        Example:
            >>> entry = CacheEntry(
            ...     query="What is the capital of France?",
            ...     query_embedding=[0.1, 0.2, 0.3],
            ...     answer="Paris",
            ...     model_id="gpt-3.5-turbo"
            ... )
            >>> store.add_cache_entry(entry)
        """
        self.cache_entries.append(entry)

    def add_request_log(self, log: RequestLog) -> None:
        """Add a request log and update model rating history.
        
        This method adds the request log to the store and updates the
        model rating history if a user rating is provided.
        
        Args:
            log: RequestLog object to add
            
        Example:
            >>> log = RequestLog(
            ...     request_id="req_123",
            ...     query="What is the capital of France?",
            ...     query_embedding=[0.1, 0.2, 0.3],
            ...     intent_tag="general",
            ...     router_decision="gpt-3.5-turbo",
            ...     response_content="Paris",
            ...     cache_status="MISS",
            ...     user_rating=5,
            ...     tokens_used=10
            ... )
            >>> store.add_request_log(log)
        """
        self.request_logs.append(log)
        # Update model rating history if user rating is provided
        if log.user_rating is not None:
            self.model_ratings[log.router_decision].append(log.user_rating)

    def get_model_rating(self, model_id: str) -> float:
        """Get normalized rating score (0-1) for a model.
        
        This method returns a normalized rating score between 0 and 1
        based on historical user ratings. If no ratings exist, it returns
        a default score of 0.6.
        
        Args:
            model_id: ID of the model to get rating for
            
        Returns:
            float: Normalized rating score (0-1)
            
        Example:
            >>> store.get_model_rating("gpt-3.5-turbo")
            0.8  # If average rating is 4/5
            >>> store.get_model_rating("unknown-model")
            0.6  # Default rating
        """
        ratings = self.model_ratings.get(model_id, [])
        if not ratings:
            return 0.6  # Default rating if no history
        # Normalize rating to 0-1 scale (assuming 1-5 rating system)
        return sum(ratings) / (len(ratings) * 5)

    def generate_request_id(self) -> str:
        """Generate a unique UUID for tracking requests.
        
        Returns:
            str: Unique request ID
            
        Example:
            >>> store.generate_request_id()
            "550e8400-e29b-41d4-a716-446655440000"
        """
        return str(uuid.uuid4())


# Global store instance used throughout the application
store = InMemoryStore()
"""Global in-memory store instance.

This instance is imported by other modules to access storage functionality.
"""


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Cosine similarity measures the cosine of the angle between two non-zero vectors,
    indicating how similar they are in direction. It ranges from -1 (opposite directions)
    to 1 (same direction).
    
    Args:
        vector_a: First vector
        vector_b: Second vector
        
    Returns:
        float: Cosine similarity score (0-1 for non-negative vectors)
        
    Example:
        >>> cosine_similarity([1, 0], [1, 0])
        1.0  # Identical vectors
        >>> cosine_similarity([1, 0], [0, 1])
        0.0  # Orthogonal vectors
        >>> cosine_similarity([1, 1], [1, 1])
        1.0  # Identical vectors
    """
    # Calculate dot product of the two vectors
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    
    # Calculate L2 norm (magnitude) of each vector
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    
    # Handle zero vectors to avoid division by zero
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    # Calculate cosine similarity
    return dot / (norm_a * norm_b)
