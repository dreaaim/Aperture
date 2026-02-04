"""Model adapter factory.

This module provides a factory class for creating and managing model adapters,
making it easy to get the appropriate adapter for a given model.

Example:
    from app.services.model_adapters.adapter_factory import AdapterFactory
    from app.models import ModelStatus
    
    model = ModelStatus(
        model_id="gpt-4o",
        price_per_1k_tokens=5.0,
        remaining_tokens=400000,
        quality_tier="large",
        api_format="openai"
    )
    
    factory = AdapterFactory()
    adapter = factory.get_adapter(model)
    
    # Use the adapter
    request = adapter.format_request("Hello, how are you?")
"""

from typing import Dict, Optional
from app.models import ModelStatus
from app.services.model_adapters.openai_adapter import OpenAIAdapter
from app.services.model_adapters.claude_adapter import ClaudeAdapter
from app.services.model_adapters.gemini_adapter import GeminiAdapter
from app.services.model_adapters.base_adapter import ModelAdapter


class AdapterFactory:
    """Factory for creating model adapters."""
    
    def __init__(self):
        """Initialize the adapter factory."""
        self._adapters: Dict[str, ModelAdapter] = {}
    
    def get_adapter(self, model: ModelStatus) -> ModelAdapter:
        """Get an adapter for the given model.
        
        Args:
            model: The model to get an adapter for
            
        Returns:
            An adapter for the model
        """
        # Create a cache key based on model ID and API format
        cache_key = f"{model.model_id}:{model.api_format}"
        
        # Return cached adapter if it exists
        if cache_key in self._adapters:
            return self._adapters[cache_key]
        
        # Create a new adapter based on API format
        adapter = self._create_adapter(model)
        
        # Cache the adapter
        self._adapters[cache_key] = adapter
        
        return adapter
    
    def _create_adapter(self, model: ModelStatus) -> ModelAdapter:
        """Create an adapter for the given model.
        
        Args:
            model: The model to create an adapter for
            
        Returns:
            An adapter for the model
        """
        if model.api_format == "openai":
            return OpenAIAdapter(model)
        elif model.api_format == "claude":
            return ClaudeAdapter(model)
        elif model.api_format == "gemini":
            return GeminiAdapter(model)
        else:
            # Default to OpenAI adapter for unknown formats
            return OpenAIAdapter(model)
    
    def clear_cache(self):
        """Clear the adapter cache."""
        self._adapters.clear()
    
    def get_cache_size(self) -> int:
        """Get the size of the adapter cache.
        
        Returns:
            The size of the adapter cache
        """
        return len(self._adapters)
