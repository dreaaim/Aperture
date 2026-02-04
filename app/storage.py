"""In-memory storage and simple math helpers for the prototype."""

import math
import uuid
from collections import defaultdict

from app.models import CacheEntry, RequestLog


class InMemoryStore:
    """Lightweight storage for cached entries and request logs."""

    def __init__(self) -> None:
        # Cache entries for semantic lookup.
        self.cache_entries: list[CacheEntry] = []
        # Logs of handled requests for rating-based routing.
        self.request_logs: list[RequestLog] = []
        # Track rating history per model to compute normalized scores.
        self.model_ratings: dict[str, list[int]] = defaultdict(list)

    def add_cache_entry(self, entry: CacheEntry) -> None:
        """Persist a cache entry in memory."""
        self.cache_entries.append(entry)

    def add_request_log(self, log: RequestLog) -> None:
        """Persist a request log and update rating aggregates."""
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


store = InMemoryStore()


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
