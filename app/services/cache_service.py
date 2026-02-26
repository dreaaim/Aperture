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
from app.utils.telemetry import get_tracer
from sentence_transformers import CrossEncoder
import asyncio

# Initialize reranker model (lazy loading)
ranking_model = None

async def get_ranking_model():
    """Lazily initialize and return the reranking model."""
    global ranking_model
    if ranking_model is None:
        ranking_model = CrossEncoder('BAAI/bge-reranker-base')
    return ranking_model

# Get OpenTelemetry tracer
tracer = get_tracer()


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
        # Create span for text embedding generation
        with tracer.start_as_current_span("embed_text", attributes={
            "text": text[:50],  # Truncate for span attributes
            "embedding_dim": settings.embedding_dim
        }) as span:
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
            
            # Set span attributes
            span.set_attribute("embedding_generated", True)
            span.set_attribute("digest_length", len(digest))
            span.set_attribute("chunk_size", chunk_size)
            
            return embeddings

    async def find_similar(self, query: str, query_embedding: List[float], top_k: int = 5) -> Tuple[Optional[CacheEntry], float]:
        """Find similar cache entries with Top-K retrieval and reranking.
        
        Args:
            query: The original query text (used for reranking)
            query_embedding: The embedding vector of the query to find similar entries for
            top_k: Number of top similar entries to retrieve
            
        Returns:
            A tuple containing:
            - The most similar CacheEntry after reranking (or None if no entries)
            - The reranked score (0-1, higher is better)
            
        Example:
            >>> service = CacheService(repository)
            >>> query = "帮我写个Python脚本"
            >>> embedding = service.embed_text(query)
            >>> service.upsert_cache(query, embedding, "这是一个Python脚本", "gpt-4o")
            >>> 
            >>> similar_query = "帮我写个Python程序"
            >>> similar_embedding = service.embed_text(similar_query)
            >>> cached_entry, similarity = await service.find_similar(similar_query, similar_embedding)
            >>> cached_entry.query
            "帮我写个Python脚本"
            >>> cached_entry.answer
            "这是一个Python脚本"
            >>> similarity
            0.98  # Reranked score
        """
        # Create span for similar cache entry search
        with tracer.start_as_current_span("find_similar", attributes={
            "embedding_dim": len(query_embedding),
            "cache_entries_count": len(self.repository.cache_entries),
            "top_k": top_k
        }) as span:
            # Step 1: Get Top-K similar entries based on cosine similarity
            scored_entries = []
            for entry in self.repository.cache_entries:
                # Calculate cosine similarity between query embedding and entry embedding
                score = cosine_similarity(query_embedding, entry.query_embedding)
                scored_entries.append((entry, score))
            
            # Sort by similarity score (descending) and take top-k
            scored_entries.sort(key=lambda item: item[1], reverse=True)
            top_entries = scored_entries[:top_k]
            
            if not top_entries:
                # No similar entries found
                span.set_attribute("similar_entry_found", False)
                return None, 0.0
            
            # Step 2: Apply reranking using Cross-Encoder
            try:
                # Get reranking model
                model = await get_ranking_model()
                
                # Prepare pairs for reranking
                pairs = [(query, entry[0].query) for entry in top_entries]
                
                # Get reranking scores
                rerank_scores = model.predict(pairs)
                
                # Combine entries with rerank scores
                reranked_entries = [(top_entries[i][0], float(rerank_scores[i])) for i in range(len(top_entries))]
                
                # Sort by rerank score (descending)
                reranked_entries.sort(key=lambda item: item[1], reverse=True)
                
                # Get best entry and score after reranking
                best_entry = reranked_entries[0][0]
                best_score = reranked_entries[0][1]
                
                # Set span attributes
                span.set_attribute("best_similarity_score", best_score)
                span.set_attribute("similar_entry_found", True)
                span.set_attribute("reranking_applied", True)
                span.set_attribute("top_k_retrieved", len(top_entries))
                span.set_attribute("reranking_model", "BAAI/bge-reranker-base")
                if best_entry:
                    span.set_attribute("best_entry_model_id", best_entry.model_id)
                    span.set_attribute("best_entry_query", best_entry.query[:50])  # Truncate for span attributes
                
                return best_entry, best_score
            except Exception as e:
                # Fallback to cosine similarity if reranking fails
                span.set_attribute("reranking_error", str(e)[:100])
                best_entry = top_entries[0][0]
                best_score = top_entries[0][1]
                
                # Set span attributes
                span.set_attribute("best_similarity_score", best_score)
                span.set_attribute("similar_entry_found", True)
                span.set_attribute("reranking_applied", False)
                span.set_attribute("top_k_retrieved", len(top_entries))
                if best_entry:
                    span.set_attribute("best_entry_model_id", best_entry.model_id)
                    span.set_attribute("best_entry_query", best_entry.query[:50])  # Truncate for span attributes
                
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
        # Create span for cache upsert
        with tracer.start_as_current_span("upsert_cache", attributes={
            "query": query[:50],  # Truncate for span attributes
            "model_id": model_id,
            "embedding_dim": len(query_embedding)
        }) as span:
            # Create a new CacheEntry object
            cache_entry = CacheEntry(
                query=query,
                query_embedding=query_embedding,
                answer=answer,
                model_id=model_id,
            )
            
            # Add the entry to the repository
            self.repository.add_cache_entry(cache_entry)
            
            # Set span attributes
            span.set_attribute("cache_entry_added", True)
            span.set_attribute("answer_length", len(answer))
            span.set_attribute("new_cache_size", len(self.repository.cache_entries))
    
    def calculate_cache_cost_benefit(self, entry_id: str, model_cost: float) -> dict:
        """Calculate cost benefit of a cache entry.
        
        Args:
            entry_id: The cache entry identifier
            model_cost: The original cost per call for this model
            
        Returns:
            Dictionary with cost benefit metrics
        """
        with tracer.start_as_current_span("calculate_cache_cost_benefit", attributes={
            "entry_id": entry_id,
            "model_cost": model_cost
        }) as span:
            entry = None
            for e in self.repository.cache_entries:
                if e.query == entry_id:
                    entry = e
                    break
            
            if not entry:
                span.set_attribute("entry_not_found", True)
                return {
                    "entry_id": entry_id,
                    "original_cost": 0.0,
                    "cache_hits": 0,
                    "total_savings": 0.0,
                    "cost_benefit_ratio": 0.0
                }
            
            cache_hits = getattr(entry, 'hit_count', 1)
            original_cost = model_cost * cache_hits
            total_savings = original_cost - model_cost
            cost_benefit_ratio = total_savings / model_cost if model_cost > 0 else 0.0
            
            result = {
                "entry_id": entry_id,
                "original_cost": round(original_cost, 4),
                "cache_hits": cache_hits,
                "total_savings": round(total_savings, 4),
                "cost_benefit_ratio": round(cost_benefit_ratio, 2)
            }
            
            span.set_attribute("total_savings", total_savings)
            span.set_attribute("cost_benefit_ratio", cost_benefit_ratio)
            
            return result
    
    def optimize_eviction_policy(self, max_entries: int = 1000) -> dict:
        """Optimize cache eviction based on cost-aware policy.
        
        This method implements a hybrid eviction strategy that considers:
        - Access frequency (LRU factor)
        - Cost value of cached responses
        - Time since last access
        
        Args:
            max_entries: Maximum number of entries to keep
            
        Returns:
            Dictionary with eviction statistics
        """
        with tracer.start_as_current_span("optimize_eviction_policy", attributes={
            "max_entries": max_entries,
            "current_entries": len(self.repository.cache_entries)
        }) as span:
            current_size = len(self.repository.cache_entries)
            
            if current_size <= max_entries:
                span.set_attribute("eviction_needed", False)
                return {
                    "evicted_count": 0,
                    "remaining_count": current_size,
                    "eviction_needed": False
                }
            
            scored_entries = []
            current_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
            
            for entry in self.repository.cache_entries:
                lru_score = 1.0 / (1 + getattr(entry, 'access_count', 1))
                cost_score = getattr(entry, 'cost_value', 0.5)
                time_score = 1.0 / (1 + (current_time - getattr(entry, 'last_access', current_time)) / 3600)
                
                combined_score = (lru_score * 0.3) + (cost_score * 0.5) + (time_score * 0.2)
                scored_entries.append((entry, combined_score))
            
            scored_entries.sort(key=lambda x: x[1], reverse=True)
            
            entries_to_keep = scored_entries[:max_entries]
            entries_to_evict = scored_entries[max_entries:]
            
            evicted_count = len(entries_to_evict)
            
            keep_queries = {e[0].query for e in entries_to_keep}
            self.repository.cache_entries = [
                e for e in self.repository.cache_entries
                if e.query in keep_queries
            ]
            
            result = {
                "evicted_count": evicted_count,
                "remaining_count": len(self.repository.cache_entries),
                "eviction_needed": True
            }
            
            span.set_attribute("evicted_count", evicted_count)
            span.set_attribute("remaining_count", len(self.repository.cache_entries))
            
            return result
    
    def monitor_cache_hit_rate(self, time_window: int = 3600) -> dict:
        """Monitor cache hit rate statistics.
        
        Args:
            time_window: Time window in seconds for statistics
            
        Returns:
            Dictionary with hit rate statistics
        """
        with tracer.start_as_current_span("monitor_cache_hit_rate", attributes={
            "time_window": time_window
        }) as span:
            total_hits = getattr(self, '_total_hits', 0)
            total_misses = getattr(self, '_total_misses', 0)
            total_requests = total_hits + total_misses
            
            hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            hits_by_model = getattr(self, '_hits_by_model', {})
            hits_by_intent = getattr(self, '_hits_by_intent', {})
            
            result = {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_requests": total_requests,
                "hit_rate": round(hit_rate, 2),
                "hits_by_model": hits_by_model,
                "hits_by_intent": hits_by_intent,
                "time_window": time_window
            }
            
            span.set_attribute("hit_rate", hit_rate)
            span.set_attribute("total_requests", total_requests)
            
            return result
    
    def predict_cache_cost(self, prediction_days: int = 7) -> dict:
        """Predict future cache cost savings.
        
        Args:
            prediction_days: Number of days to predict
            
        Returns:
            Dictionary with cost predictions
        """
        with tracer.start_as_current_span("predict_cache_cost", attributes={
            "prediction_days": prediction_days
        }) as span:
            total_hits = getattr(self, '_total_hits', 0)
            avg_cost_per_hit = getattr(self, '_avg_cost_per_hit', 0.01)
            
            daily_hits = total_hits / 30 if total_hits > 0 else 10
            predicted_hits = daily_hits * prediction_days
            predicted_savings = predicted_hits * avg_cost_per_hit
            
            result = {
                "prediction_days": prediction_days,
                "predicted_hits": int(predicted_hits),
                "predicted_savings": round(predicted_savings, 4),
                "daily_average_hits": round(daily_hits, 2),
                "average_cost_per_hit": avg_cost_per_hit
            }
            
            span.set_attribute("predicted_savings", predicted_savings)
            span.set_attribute("predicted_hits", int(predicted_hits))
            
            return result
    
    def set_cache_priority(self, query: str, priority: float = 1.0) -> None:
        """Set cache priority for a query based on cost value.
        
        Args:
            query: The query string
            priority: Priority value (0-1, higher is more important)
        """
        with tracer.start_as_current_span("set_cache_priority", attributes={
            "query": query[:50],
            "priority": priority
        }) as span:
            for entry in self.repository.cache_entries:
                if entry.query == query:
                    entry.cost_value = priority
                    span.set_attribute("priority_set", True)
                    return
            
            span.set_attribute("priority_set", False)
    
    async def warmup_cache(self, queries: List[dict]) -> dict:
        """Warmup cache with high-priority queries.
        
        Args:
            queries: List of query dictionaries with 'query', 'answer', 'model_id'
            
        Returns:
            Dictionary with warmup statistics
        """
        with tracer.start_as_current_span("warmup_cache", attributes={
            "queries_count": len(queries)
        }) as span:
            warmed_count = 0
            
            for q in queries:
                query = q.get('query', '')
                answer = q.get('answer', '')
                model_id = q.get('model_id', 'unknown')
                priority = q.get('priority', 1.0)
                
                if query and answer:
                    embedding = self.embed_text(query)
                    self.upsert_cache(query, embedding, answer, model_id)
                    self.set_cache_priority(query, priority)
                    warmed_count += 1
            
            result = {
                "total_queries": len(queries),
                "warmed_count": warmed_count,
                "success_rate": round(warmed_count / len(queries) * 100, 2) if queries else 0
            }
            
            span.set_attribute("warmed_count", warmed_count)
            
            return result
    
    def adjust_cache_capacity(self, target_hit_rate: float = 0.8) -> dict:
        """Dynamically adjust cache capacity based on hit rate.
        
        Args:
            target_hit_rate: Target hit rate (0-1)
            
        Returns:
            Dictionary with adjustment results
        """
        with tracer.start_as_current_span("adjust_cache_capacity", attributes={
            "target_hit_rate": target_hit_rate
        }) as span:
            stats = self.monitor_cache_hit_rate()
            current_hit_rate = stats['hit_rate'] / 100
            
            current_capacity = len(self.repository.cache_entries)
            
            if current_hit_rate < target_hit_rate:
                adjustment_factor = 1.2
                action = "increase"
            elif current_hit_rate > target_hit_rate + 0.1:
                adjustment_factor = 0.9
                action = "decrease"
            else:
                adjustment_factor = 1.0
                action = "maintain"
            
            new_capacity = int(current_capacity * adjustment_factor)
            new_capacity = max(100, min(10000, new_capacity))
            
            result = {
                "current_capacity": current_capacity,
                "new_capacity": new_capacity,
                "current_hit_rate": round(current_hit_rate, 2),
                "target_hit_rate": target_hit_rate,
                "action": action
            }
            
            span.set_attribute("action", action)
            span.set_attribute("new_capacity", new_capacity)
            
            return result
    
    def analyze_cache_effectiveness(self) -> dict:
        """Analyze cache effectiveness and generate optimization suggestions.
        
        Returns:
            Dictionary with effectiveness analysis and suggestions
        """
        with tracer.start_as_current_span("analyze_cache_effectiveness") as span:
            total_entries = len(self.repository.cache_entries)
            stats = self.monitor_cache_hit_rate()
            cost_prediction = self.predict_cache_cost(prediction_days=7)
            
            suggestions = []
            
            if stats['hit_rate'] < 50:
                suggestions.append({
                    "type": "low_hit_rate",
                    "message": "Cache hit rate is below 50%. Consider increasing cache capacity or warming up frequent queries.",
                    "priority": "high"
                })
            
            if total_entries > 5000:
                suggestions.append({
                    "type": "large_cache",
                    "message": "Cache size is large. Consider implementing eviction policy optimization.",
                    "priority": "medium"
                })
            
            if cost_prediction['predicted_savings'] > 10:
                suggestions.append({
                    "type": "high_savings_potential",
                    "message": "High cost savings potential. Cache is performing well.",
                    "priority": "info"
                })
            
            top_cached = []
            for entry in self.repository.cache_entries[:10]:
                top_cached.append({
                    "query": entry.query[:50],
                    "model_id": entry.model_id,
                    "hit_count": getattr(entry, 'hit_count', 1)
                })
            
            result = {
                "total_entries": total_entries,
                "hit_rate": stats['hit_rate'],
                "predicted_weekly_savings": cost_prediction['predicted_savings'],
                "top_cached_queries": top_cached,
                "suggestions": suggestions,
                "overall_score": round(stats['hit_rate'] * 0.5 + min(total_entries / 100, 50), 2)
            }
            
            span.set_attribute("overall_score", result['overall_score'])
            span.set_attribute("suggestions_count", len(suggestions))
            
            return result
    
    def record_cache_hit(self, model_id: str, intent: str = "unknown") -> None:
        """Record a cache hit for statistics.
        
        Args:
            model_id: The model ID that was cached
            intent: The intent category of the query
        """
        self._total_hits = getattr(self, '_total_hits', 0) + 1
        self._hits_by_model = getattr(self, '_hits_by_model', {})
        self._hits_by_intent = getattr(self, '_hits_by_intent', {})
        
        if model_id not in self._hits_by_model:
            self._hits_by_model[model_id] = 0
        self._hits_by_model[model_id] += 1
        
        if intent not in self._hits_by_intent:
            self._hits_by_intent[intent] = 0
        self._hits_by_intent[intent] += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss for statistics."""
        self._total_misses = getattr(self, '_total_misses', 0) + 1
