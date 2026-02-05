"""Model adapters for different model types.

This module provides adapters for different types of models, including:
- LLM (Large Language Model) adapters
- Embedding model adapters
- Reranker model adapters

Adapters handle the specific implementation details for each model type, providing a
unified interface for the application to interact with different models.
"""

from app.adapters.base_adapter import BaseAdapter
from app.adapters.llm_adapter import LLMAdapter
from app.adapters.embedding_adapter import EmbeddingAdapter
from app.adapters.reranker_adapter import RerankerAdapter

__all__ = ["BaseAdapter", "LLMAdapter", "EmbeddingAdapter", "RerankerAdapter"]
