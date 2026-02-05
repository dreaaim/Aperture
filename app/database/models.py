"""Database models for PostgreSQL with pgvector support.

This module defines all database models for the application, including:
- LLM model configurations
- Semantic cache with vector embeddings
- Chat logs
- User feedback

All models use SQLAlchemy ORM and include pgvector support for vector embeddings.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, Vector
from sqlalchemy.sql import func
from app.database import Base


class LLMModel(Base):
    """LLM model configuration table."""
    __tablename__ = "llm_models"
    
    model_id = Column(String(50), primary_key=True, index=True)
    provider_name = Column(String(50), nullable=False)
    input_price_per_1k = Column(DECIMAL(10, 6), nullable=False)
    output_price_per_1k = Column(DECIMAL(10, 6), nullable=False)
    max_context_length = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    current_latency_p95 = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class SemanticCache(Base):
    """Semantic cache table with vector embeddings."""
    __tablename__ = "semantic_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1024))  # Using 1024-dimensional embeddings
    intent_category = Column(String(50), index=True)
    hit_count = Column(Integer, default=1)
    source_model_id = Column(String(50), ForeignKey("llm_models.model_id"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_hit_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        # Create HNSW index for vector search
        {'extend_existing': True}
    )


class ChatLog(Base):
    """Chat transaction log table."""
    __tablename__ = "chat_logs"
    
    request_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1024))  # Using 1024-dimensional embeddings
    routing_strategy = Column(String(20), index=True)
    selected_model_id = Column(String(50), ForeignKey("llm_models.model_id"))
    response_text = Column(Text)
    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    total_cost = Column(DECIMAL(10, 6))
    latency_ms = Column(Integer)
    status = Column(String(20), default="SUCCESS", index=True)
    security_flag = Column(String(50), index=True)  # Security threat type, e.g., "injection", "sensitive_info"
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class UserFeedback(Base):
    """User feedback table."""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("chat_logs.request_id"), nullable=False, index=True)
    model_id = Column(String(50), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    feedback_text = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint('score >= 1 AND score <= 5', name='check_score_range'),
    )
