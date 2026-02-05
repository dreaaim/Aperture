"""Database initialization and connection management.

This module provides database connection management and initialization functions
for the PostgreSQL database with pgvector support.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Get a database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database.
    
    Creates all tables if they don't exist.
    """
    # Import all models to ensure they are registered
    from app.database.models import LLMModel, SemanticCache, ChatLog, UserFeedback
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
