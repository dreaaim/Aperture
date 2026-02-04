"""In-memory repository implementation."""

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Literal

from app.models import CacheEntry, RequestLog


class MemoryRepository:
    """Lightweight in-memory storage for cached entries and request logs."""

    def __init__(self) -> None:
        """Initialize the memory repository."""
        # Cache entries for semantic lookup.
        self.cache_entries: list[CacheEntry] = []
        # Logs of handled requests for rating-based routing.
        self.request_logs: list[RequestLog] = []
        # Track rating history per model to compute normalized scores.
        self.model_ratings: dict[str, list[int]] = defaultdict(list)

    def add_cache_entry(self, entry: CacheEntry) -> None:
        """Persist a cache entry in memory."""
        self.cache_entries.append(entry)

    def add_request_log(
        self,
        request_id: str,
        query: str,
        query_embedding: list[float],
        intent_tag: str,
        router_decision: str,
        response_content: str,
        cache_status: Literal['HIT', 'FEW_SHOT', 'MISS'],
        tokens_used: int,
        user_rating: int | None = None,
    ) -> None:
        """Persist a request log and update rating aggregates."""
        from typing import Literal
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
        self.request_logs.append(log)
        if log.user_rating is not None:
            self.model_ratings[log.router_decision].append(log.user_rating)

    def get_model_rating(self, model_id: str) -> float:
        """Return a normalized rating score (0-1) for a model."""
        ratings = self.model_ratings.get(model_id, [])
        if not ratings:
            return 0.6
        return sum(ratings) / (len(ratings) * 5)

    def generate_request_id(self) -> str:
        """Generate a UUID for tracking the request."""
        return str(uuid.uuid4())
