"""Model adapters for the application.

This module provides a comprehensive adapter system for different types of models and providers,
including:

1. Core adapters (base directory):
   - BaseAdapter: Core adapter interface
   - ModelAdapter: Provider-specific adapter base class

2. Model type adapters (types directory):
   - LLMAdapter: For large language models
   - EmbeddingAdapter: For text embedding models
   - RerankerAdapter: For document reranking models

3. Provider-specific adapters (providers directory):
   - OpenAIAdapter: For OpenAI-compatible models
   - ClaudeAdapter: For Claude models
   - GeminiAdapter: For Google Gemini models

4. Adapter factory:
   - AdapterFactory: For creating and managing adapters

Adapters handle the specific implementation details for each model type and provider,
providing a unified interface for the application to interact with different models.
"""

# Core adapters
from app.adapters.base.core_adapter import BaseAdapter
from app.adapters.base.provider_base import ModelAdapter

# Model type adapters
from app.adapters.types.llm_adapter import LLMAdapter
from app.adapters.types.embedding_adapter import EmbeddingAdapter
from app.adapters.types.reranker_adapter import RerankerAdapter

# Provider-specific adapters
from app.adapters.providers.openai_adapter import OpenAIAdapter
from app.adapters.providers.claude_adapter import ClaudeAdapter
from app.adapters.providers.gemini_adapter import GeminiAdapter

# Adapter factory
from app.adapters.adapter_factory import UnifiedAdapterFactory

__all__ = [
    # Core adapters
    "BaseAdapter", "ModelAdapter",
    # Model type adapters
    "LLMAdapter", "EmbeddingAdapter", "RerankerAdapter",
    # Provider-specific adapters
    "OpenAIAdapter", "ClaudeAdapter", "GeminiAdapter",
    # Adapter factory
    "UnifiedAdapterFactory"
]
