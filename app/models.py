"""Pydantic schemas used by the API and in-memory storage.

This module defines the data models used throughout the application, including:
- API request and response models
- Model status tracking
- Request logging
- Cache entry storage

All models use Pydantic BaseModel for automatic validation and serialization.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Inbound request payload for the query endpoint.
    
    This model represents the structure of incoming requests to the API's
    query endpoint, containing the user's query and optional user identifier.
    
    Fields:
        query: The user's query text
        user_id: Optional user identifier for tracking and personalization
        
    Example:
        >>> QueryRequest(
        ...     query="What is the capital of France?",
        ...     user_id="user123"
        ... )
        QueryRequest(query="What is the capital of France?", user_id="user123")
    """

    query: str  # The user's query text
    user_id: str | None = None  # Optional user identifier


class QueryResponse(BaseModel):
    """Outbound response payload from the query endpoint.
    
    This model represents the structure of responses returned by the API's
    query endpoint, containing the generated answer and metadata about
    how it was produced.
    
    Fields:
        request_id: Unique identifier for the request
        answer: The generated answer to the user's query
        model_id: ID of the model that generated the answer
        cache_status: Indicates if the answer was retrieved from cache
            - "HIT": Exact match found in cache
            - "FEW_SHOT": Similar examples used from cache
            - "MISS": No cache entry used
        
    Example:
        >>> QueryResponse(
        ...     request_id="req_123",
        ...     answer="The capital of France is Paris.",
        ...     model_id="gpt-3.5-turbo",
        ...     cache_status="HIT"
        ... )
        QueryResponse(request_id="req_123", answer="The capital of France is Paris.", model_id="gpt-3.5-turbo", cache_status="HIT")
    """

    request_id: str  # Unique identifier for the request
    answer: str  # The generated answer
    model_id: str  # ID of the model used
    cache_status: Literal["HIT", "FEW_SHOT", "MISS"]  # Cache usage status


class ModelStatus(BaseModel):
    """Snapshot of a model's routing metadata.
    
    This model tracks metadata about each available model, including
    pricing, quota, and quality tier, which are used for model selection.
    
    Fields:
        model_id: Unique identifier for the model
        price_per_1k_tokens: Price in currency units per 1000 tokens
        remaining_tokens: Remaining token quota for the model
        quality_tier: Size/quality tier of the model
            - "small": Smaller, faster, cheaper models
            - "medium": Balanced models
            - "large": Larger, more capable, more expensive models
        
    Example:
        >>> ModelStatus(
        ...     model_id="gpt-3.5-turbo",
        ...     price_per_1k_tokens=0.0015,
        ...     remaining_tokens=100000,
        ...     quality_tier="medium"
        ... )
        ModelStatus(model_id="gpt-3.5-turbo", price_per_1k_tokens=0.0015, remaining_tokens=100000, quality_tier="medium")
    """

    model_id: str  # Unique identifier for the model
    price_per_1k_tokens: float  # Price per 1000 tokens
    remaining_tokens: int  # Remaining token quota
    quality_tier: Literal["small", "medium", "large"]  # Model quality tier


class RequestLog(BaseModel):
    """Log record for a handled request, used for feedback loops.
    
    This model captures detailed information about each request for
    analytics, monitoring, and continuous improvement of the system.
    
    Fields:
        request_id: Unique identifier for the request
        query: The user's query text
        query_embedding: Embedding vector of the query
        intent_tag: Classified intent of the query
        router_decision: The model selected by the router
        response_content: The generated response
        cache_status: Cache usage status
        user_rating: Optional user rating of the response
        tokens_used: Number of tokens used for the request
        created_at: Timestamp when the request was processed
        
    Example:
        >>> RequestLog(
        ...     request_id="req_123",
        ...     query="What is the capital of France?",
        ...     query_embedding=[0.1, 0.2, 0.3],
        ...     intent_tag="general_knowledge",
        ...     router_decision="gpt-3.5-turbo",
        ...     response_content="The capital of France is Paris.",
        ...     cache_status="HIT",
        ...     tokens_used=10
        ... )
        RequestLog(..., created_at=datetime.datetime(...))
    """

    request_id: str  # Unique identifier for the request
    query: str  # The user's query text
    query_embedding: list[float]  # Embedding vector of the query
    intent_tag: str  # Classified intent of the query
    router_decision: str  # Selected model
    response_content: str  # Generated response
    cache_status: Literal["HIT", "FEW_SHOT", "MISS"]  # Cache usage status
    user_rating: int | None = None  # Optional user rating
    tokens_used: int  # Tokens used
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Timestamp


class CacheEntry(BaseModel):
    """Cached question/answer pair with its embedding.
    
    This model stores cached query-answer pairs along with the query's
    embedding for semantic similarity search.
    
    Fields:
        query: The original query text
        query_embedding: Embedding vector of the query
        answer: The cached answer
        model_id: ID of the model that generated the answer
        created_at: Timestamp when the entry was cached
        
    Example:
        >>> CacheEntry(
        ...     query="What is the capital of France?",
        ...     query_embedding=[0.1, 0.2, 0.3],
        ...     answer="The capital of France is Paris.",
        ...     model_id="gpt-3.5-turbo"
        ... )
        CacheEntry(..., created_at=datetime.datetime(...))
    """

    query: str  # Original query text
    query_embedding: list[float]  # Embedding vector of the query
    answer: str  # Cached answer
    model_id: str  # Model that generated the answer
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Timestamp
