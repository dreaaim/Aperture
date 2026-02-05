"""PostgreSQL repository implementation with pgvector support.

This module provides a PostgreSQL repository implementation that uses PostgreSQL
with pgvector extension for storing and querying vector embeddings. It implements
 the same interface as MemoryRepository but uses persistent storage.

Example:
    from app.repositories.postgresql_repository import PostgreSQLRepository
    from app.models import CacheEntry
    
    repository = PostgreSQLRepository()
    
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
    
    # Get model rating
    rating = repository.get_model_rating("gpt-4o")
    print(rating)  # Output: 1.0 (since we gave a 5-star rating)
    
    # Find similar queries
    similar_entries = repository.find_similar([0.1, 0.2, 0.3], threshold=0.8)
    print(len(similar_entries))  # Output: 1
"""

import uuid
from typing import Literal, List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import UUID

from app.database import SessionLocal, init_db
from app.database.models import LLMModel, SemanticCache, ChatLog, UserFeedback
from app.models import CacheEntry, RequestLog
from app.utils.telemetry import get_tracer
from app.utils.logger import default_logger

# Get OpenTelemetry tracer
tracer = get_tracer()


class PostgreSQLRepository:
    """PostgreSQL repository with pgvector support.
    
    This class implements the same interface as MemoryRepository but uses
    PostgreSQL with pgvector extension for persistent storage and vector search.
    """
    
    def __init__(self):
        """Initialize the PostgreSQL repository.
        
        This method initializes the repository and ensures the database is set up.
        """
        # Initialize database if needed
        init_db()
        # Create session factory
        self.session_factory = SessionLocal
    
    def add_cache_entry(self, entry: CacheEntry) -> None:
        """Add a cache entry to the repository.
        
        Args:
            entry: The CacheEntry object to add
        """
        # Create span for cache entry addition
        with tracer.start_as_current_span("add_cache_entry", attributes={
            "model_id": entry.model_id,
            "query": entry.query[:50],  # Truncate for span attributes
            "embedding_dim": len(entry.query_embedding)
        }) as span:
            db = self.session_factory()
            try:
                # Create SemanticCache object
                semantic_cache = SemanticCache(
                    query_text=entry.query,
                    response_text=entry.answer,
                    query_embedding=entry.query_embedding,
                    source_model_id=entry.model_id
                )
                
                # Add to database
                db.add(semantic_cache)
                db.commit()
                db.refresh(semantic_cache)
                
                # Set span attributes
                span.set_attribute("cache_entry_added", True)
                span.set_attribute("cache_entry_id", semantic_cache.id)
                span.set_attribute("answer_length", len(entry.answer))
            except Exception as e:
                db.rollback()
                span.set_attribute("error", str(e)[:100])
                raise
            finally:
                db.close()
    
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
        """
        # Create span for request log addition
        with tracer.start_as_current_span("add_request_log", attributes={
            "request_id": request_id,
            "intent_tag": intent_tag,
            "router_decision": router_decision,
            "cache_status": cache_status,
            "tokens_used": tokens_used,
            "user_rating": user_rating
        }) as span:
            db = self.session_factory()
            try:
                # Create ChatLog object
                chat_log = ChatLog(
                    request_id=uuid.UUID(request_id),
                    query_text=query,
                    query_embedding=query_embedding,
                    routing_strategy=cache_status,
                    selected_model_id=router_decision,
                    response_text=response_content,
                    tokens_input=tokens_used,
                    tokens_output=0,  # Not provided in current interface
                    total_cost=0.0,  # Not provided in current interface
                    latency_ms=0,  # Not provided in current interface
                    status="SUCCESS"
                )
                
                # Add to database
                db.add(chat_log)
                
                # Add user feedback if provided
                if user_rating is not None:
                    feedback = UserFeedback(
                        request_id=uuid.UUID(request_id),
                        model_id=router_decision,
                        score=user_rating
                    )
                    db.add(feedback)
                    span.set_attribute("rating_updated", True)
                    span.set_attribute("model_id", router_decision)
                    span.set_attribute("rating", user_rating)
                
                db.commit()
                span.set_attribute("log_added", True)
            except Exception as e:
                db.rollback()
                span.set_attribute("error", str(e)[:100])
                raise
            finally:
                db.close()
    
    def get_model_rating(self, model_id: str) -> float:
        """Get a normalized rating score (0-1) for a model.
        
        Args:
            model_id: The ID of the model to get the rating for
            
        Returns:
            The normalized rating score (0-1, higher is better)
            Returns 0.6 if no ratings exist for the model
        """
        # Create span for model rating retrieval
        with tracer.start_as_current_span("get_model_rating", attributes={
            "model_id": model_id
        }) as span:
            db = self.session_factory()
            try:
                # Query average rating for the model
                result = db.query(
                    func.avg(UserFeedback.score).label('avg_score'),
                    func.count(UserFeedback.id).label('count')
                ).filter(
                    UserFeedback.model_id == model_id
                ).first()
                
                if result and result.count > 0 and result.avg_score is not None:
                    # Normalize rating (1-5 to 0-1)
                    rating = float(result.avg_score) / 5.0
                    span.set_attribute("rating_count", result.count)
                    span.set_attribute("used_default_rating", False)
                    span.set_attribute("rating", rating)
                    span.set_attribute("average_rating", float(result.avg_score))
                    return rating
                else:
                    # Return default rating if no ratings exist
                    span.set_attribute("used_default_rating", True)
                    span.set_attribute("rating", 0.6)
                    return 0.6
            except Exception as e:
                span.set_attribute("error", str(e)[:100])
                return 0.6
            finally:
                db.close()
    
    def generate_request_id(self) -> str:
        """Generate a unique UUID for tracking the request.
        
        Returns:
            A string representation of a UUID
        """
        # Create span for request ID generation
        with tracer.start_as_current_span("generate_request_id") as span:
            request_id = str(uuid.uuid4())
            span.set_attribute("request_id", request_id)
            return request_id
    
    def find_similar(self, embedding: List[float], threshold: float = 0.8) -> List[Tuple[CacheEntry, float]]:
        """Find similar cache entries using vector similarity.
        
        Args:
            embedding: The query embedding to search with
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of tuples containing CacheEntry and similarity score
        """
        # Create span for similar entries search
        with tracer.start_as_current_span("find_similar", attributes={
            "embedding_dim": len(embedding),
            "threshold": threshold
        }) as span:
            db = self.session_factory()
            try:
                # Query similar entries using pgvector
                # Using cosine similarity (1 - distance)
                from sqlalchemy import literal
                
                # Convert embedding to PostgreSQL vector
                vector_embedding = embedding
                
                # Query with similarity threshold
                results = db.query(
                    SemanticCache,
                    (1 - SemanticCache.query_embedding.cosine_distance(vector_embedding)).label('similarity')
                ).filter(
                    (1 - SemanticCache.query_embedding.cosine_distance(vector_embedding)) > threshold
                ).order_by(
                    (1 - SemanticCache.query_embedding.cosine_distance(vector_embedding)).desc()
                ).limit(10).all()
                
                # Convert to CacheEntry objects
                similar_entries = []
                for semantic_cache, similarity in results:
                    cache_entry = CacheEntry(
                        query=semantic_cache.query_text,
                        query_embedding=semantic_cache.query_embedding,
                        answer=semantic_cache.response_text,
                        model_id=semantic_cache.source_model_id
                    )
                    similar_entries.append((cache_entry, float(similarity)))
                
                span.set_attribute("similar_entries_found", len(similar_entries))
                return similar_entries
            except Exception as e:
                span.set_attribute("error", str(e)[:100])
                return []
            finally:
                db.close()
    
    def initialize_models(self):
        """Initialize default models in the database.
        
        This method adds default model configurations to the database if they don't exist.
        """
        from app.config import settings
        
        db = self.session_factory()
        try:
            for model_config in settings.model_catalog:
                # Check if model already exists
                existing_model = db.query(LLMModel).filter(
                    LLMModel.model_id == model_config.model_id
                ).first()
                
                if not existing_model:
                    # Add new model
                    new_model = LLMModel(
                        model_id=model_config.model_id,
                        provider_name="openai" if "gpt" in model_config.model_id else 
                                  "anthropic" if "claude" in model_config.model_id else "other",
                        input_price_per_1k=model_config.price_per_1k_tokens,
                        output_price_per_1k=model_config.price_per_1k_tokens,
                        max_context_length=100000 if model_config.quality_tier == "large" else
                                      50000 if model_config.quality_tier == "medium" else 20000
                    )
                    db.add(new_model)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    
    def update_request_log_embedding(self, request_id: str, embedding: List[float]):
        """Update request log with embedding.
        
        Args:
            request_id: The request ID
            embedding: The embedding vector
        """
        with tracer.start_as_current_span("update_request_log_embedding", attributes={
            "request_id": request_id,
            "embedding_dim": len(embedding)
        }) as span:
            db = self.session_factory()
            try:
                # Update ChatLog with embedding
                chat_log = db.query(ChatLog).filter(
                    ChatLog.request_id == uuid.UUID(request_id)
                ).first()
                
                if chat_log:
                    chat_log.query_embedding = embedding
                    db.commit()
                    span.set_attribute("embedding_updated", True)
                    default_logger.info(f"Updated embedding for request {request_id}")
                else:
                    span.set_attribute("error", f"Request log not found: {request_id}")
                    default_logger.warning(f"Request log not found for {request_id}")
            except Exception as e:
                db.rollback()
                span.set_attribute("error", str(e)[:100])
                default_logger.error(f"Error updating request log embedding: {e}")
            finally:
                db.close()
