"""In-memory repository implementation.

This module provides an in-memory repository for storing and managing data,
including:
- Cache entries for semantic lookup
- Request logs for rating-based routing
- Model ratings for model selection

The MemoryRepository class is a lightweight implementation that stores data
in memory, which is suitable for testing and demos. In a production environment,
you would use a persistent storage solution (e.g., a database).

Example:
    from app.repositories.memory_repository import MemoryRepository
    from app.models import CacheEntry
    
    repository = MemoryRepository()
    
    # Generate request ID
    request_id = repository.generate_request_id()
    print(request_id)  # Output: UUID string
    
    # Add cache entry
    cache_entry = CacheEntry(
        query="帮我写个Python脚本",
        query_embedding=[0.1, 0.2, 0.3],  # Example embedding
        answer="这是一个Python脚本",
        model_id="gpt-4o"
    )
    repository.add_cache_entry(cache_entry)
    print(len(repository.cache_entries))  # Output: 1
    
    # Add request log
    repository.add_request_log(
        request_id=request_id,
        query="帮我写个Python脚本",
        query_embedding=[0.1, 0.2, 0.3],
        intent_tag="code",
        router_decision="gpt-4o",
        response_content="这是一个Python脚本",
        cache_status="MISS",
        tokens_used=100,
        user_rating=5
    )
    print(len(repository.request_logs))  # Output: 1
    
    # Get model rating
    rating = repository.get_model_rating("gpt-4o")
    print(rating)  # Output: 1.0 (since we gave a 5-star rating)
"""

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Literal, List, Dict, Optional

from app.models import CacheEntry, RequestLog


class MemoryRepository:
    """Lightweight in-memory storage for cached entries and request logs.
    
    This class provides an in-memory storage solution for:
    - Cache entries: Stored in `cache_entries` list
    - Request logs: Stored in `request_logs` list
    - Model ratings: Stored in `model_ratings` defaultdict
    
    Attributes:
        cache_entries: List of CacheEntry objects for semantic lookup
        request_logs: List of RequestLog objects for rating-based routing
        model_ratings: Dictionary mapping model IDs to lists of user ratings
    """

    def __init__(self) -> None:
        """Initialize the memory repository.
        
        This method initializes the in-memory storage structures:
        - `cache_entries`: Empty list for storing cache entries
        - `request_logs`: Empty list for storing request logs
        - `model_ratings`: Default dict for storing model ratings
        """
        # Cache entries for semantic lookup
        self.cache_entries: List[CacheEntry] = []
        # Logs of handled requests for rating-based routing
        self.request_logs: List[RequestLog] = []
        # Track rating history per model to compute normalized scores
        self.model_ratings: Dict[str, List[int]] = defaultdict(list)

    def add_cache_entry(self, entry: CacheEntry) -> None:
        """Add a cache entry to the repository.
        
        Args:
            entry: The CacheEntry object to add
            
        Example:
            >>> repository = MemoryRepository()
            >>> cache_entry = CacheEntry(
            ...     query="帮我写个Python脚本",
            ...     query_embedding=[0.1, 0.2, 0.3],
            ...     answer="这是一个Python脚本",
            ...     model_id="gpt-4o"
            ... )
            >>> repository.add_cache_entry(cache_entry)
            >>> len(repository.cache_entries)
            1
        """
        self.cache_entries.append(entry)

    def add_request_log(
        self,
        request_id: str,
        query: str,
        query_embedding: List[float],
        intent_tag: str,
        router_decision: str,
        response_content: str,
        cache_status: Literal['HIT', 'FEW_SHOT', 'MISS'],
        tokens_used: int,
        user_rating: Optional[int] = None,
    ) -> None:
        """Add a request log to the repository and update model ratings.
        
        Args:
            request_id: Unique ID for the request
            query: The user's query string
            query_embedding: Embedding vector of the query
            intent_tag: Classified intent of the query
            router_decision: Model ID selected for the request
            response_content: Generated response content
            cache_status: Cache status (HIT, FEW_SHOT, or MISS)
            tokens_used: Number of tokens used for the request
            user_rating: Optional user rating for the response (1-5)
            
        Example:
            >>> repository = MemoryRepository()
            >>> request_id = repository.generate_request_id()
            >>> repository.add_request_log(
            ...     request_id=request_id,
            ...     query="帮我写个Python脚本",
            ...     query_embedding=[0.1, 0.2, 0.3],
            ...     intent_tag="code",
            ...     router_decision="gpt-4o",
            ...     response_content="这是一个Python脚本",
            ...     cache_status="MISS",
            ...     tokens_used=100,
            ...     user_rating=5
            ... )
            >>> len(repository.request_logs)
            1
            >>> len(repository.model_ratings["gpt-4o"])
            1
        """
        # Create a RequestLog object with the provided data
        log = RequestLog(
            request_id=request_id,
            query=query,
            query_embedding=query_embedding,
            intent_tag=intent_tag,
            router_decision=router_decision,
            response_content=response_content,
            cache_status=cache_status,
            user_rating=user_rating,
            tokens_used=tokens_used,
            created_at=datetime.utcnow(),
        )
        
        # Add the log to the repository
        self.request_logs.append(log)
        
        # Update model ratings if a user rating is provided
        if log.user_rating is not None:
            self.model_ratings[log.router_decision].append(log.user_rating)

    def get_model_rating(self, model_id: str) -> float:
        """Get a normalized rating score (0-1) for a model.
        
        Args:
            model_id: The ID of the model to get the rating for
            
        Returns:
            The normalized rating score (0-1, higher is better)
            Returns 0.6 if no ratings exist for the model
            
        Example:
            >>> repository = MemoryRepository()
            >>> request_id = repository.generate_request_id()
            >>> repository.add_request_log(
            ...     request_id=request_id,
            ...     query="帮我写个Python脚本",
            ...     query_embedding=[0.1, 0.2, 0.3],
            ...     intent_tag="code",
            ...     router_decision="gpt-4o",
            ...     response_content="这是一个Python脚本",
            ...     cache_status="MISS",
            ...     tokens_used=100,
            ...     user_rating=5
            ... )
            >>> repository.get_model_rating("gpt-4o")
            1.0
            >>> repository.get_model_rating("llama-3-8b")  # No ratings
            0.6
        """
        # Get ratings for the model (empty list if none exist)
        ratings = self.model_ratings.get(model_id, [])
        
        # Return default rating if no ratings exist
        if not ratings:
            return 0.6
        
        # Calculate normalized rating (0-1)
        # ratings are 1-5, so divide by 5 to normalize
        return sum(ratings) / (len(ratings) * 5)

    def generate_request_id(self) -> str:
        """Generate a unique UUID for tracking the request.
        
        Returns:
            A string representation of a UUID
            
        Example:
            >>> repository = MemoryRepository()
            >>> request_id = repository.generate_request_id()
            >>> import uuid
            >>> isinstance(uuid.UUID(request_id), uuid.UUID)
            True
        """
        return str(uuid.uuid4())
