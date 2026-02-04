"""Pydantic schemas used by the API and in-memory storage."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Inbound request payload."""

    query: str
    user_id: str | None = None


class QueryResponse(BaseModel):
    """Outbound response payload."""

    request_id: str
    answer: str
    model_id: str
    cache_status: Literal["HIT", "FEW_SHOT", "MISS"]


class ModelStatus(BaseModel):
    """Snapshot of a model's routing metadata."""

    model_id: str
    price_per_1k_tokens: float
    remaining_tokens: int
    quality_tier: Literal["small", "medium", "large"]


class RequestLog(BaseModel):
    """Log record for a handled request, used for feedback loops."""

    request_id: str
    query: str
    query_embedding: list[float]
    intent_tag: str
    router_decision: str
    response_content: str
    cache_status: Literal["HIT", "FEW_SHOT", "MISS"]
    user_rating: int | None = None
    tokens_used: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CacheEntry(BaseModel):
    """Cached question/answer pair with its embedding."""

    query: str
    query_embedding: list[float]
    answer: str
    model_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
