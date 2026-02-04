"""Cache service for semantic caching."""

import hashlib

from app.config import settings
from app.models import CacheEntry
from app.repositories.memory_repository import MemoryRepository
from app.utils.math import cosine_similarity


class CacheService:
    """Service for managing semantic cache operations."""

    def __init__(self, repository: MemoryRepository):
        """Initialize the cache service with a repository."""
        self.repository = repository

    def embed_text(self, text: str) -> list[float]:
        """Create a deterministic embedding from text for testing and demos."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = [b / 255 for b in digest]
        chunk_size = len(values) // settings.embedding_dim
        embeddings = []
        for index in range(settings.embedding_dim):
            # Average the chunk to keep the dimension fixed.
            chunk = values[index * chunk_size : (index + 1) * chunk_size]
            embeddings.append(sum(chunk) / len(chunk))
        return embeddings

    def find_similar(self, query_embedding: list[float]) -> tuple[CacheEntry | None, float]:
        """Return the most similar cache entry and its similarity score."""
        best_entry = None
        best_score = 0.0
        for entry in self.repository.cache_entries:
            score = cosine_similarity(query_embedding, entry.query_embedding)
            if score > best_score:
                best_score = score
                best_entry = entry
        return best_entry, best_score

    def upsert_cache(self, query: str, query_embedding: list[float], answer: str, model_id: str) -> None:
        """Insert a cache entry (no dedupe for this prototype)."""
        self.repository.add_cache_entry(
            CacheEntry(
                query=query,
                query_embedding=query_embedding,
                answer=answer,
                model_id=model_id,
            )
        )
