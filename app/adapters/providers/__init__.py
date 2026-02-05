"""Provider-specific adapters.

This module provides adapters for different model providers, including:
- OpenAI adapter
- Claude adapter
- Gemini adapter

Adapters handle the specific implementation details for each provider's API format,
providing a unified interface for the application to interact with different providers.
"""

from app.adapters.providers.openai_adapter import OpenAIAdapter
from app.adapters.providers.claude_adapter import ClaudeAdapter
from app.adapters.providers.gemini_adapter import GeminiAdapter

__all__ = ["OpenAIAdapter", "ClaudeAdapter", "GeminiAdapter"]
