"""OpenAI model adapter.

This module provides an adapter for OpenAI-compatible models, handling request
formatting, response parsing, and format conversion.

Example:
    from app.services.model_adapters.openai_adapter import OpenAIAdapter
    from app.models import ModelStatus
    
    model = ModelStatus(
        model_id="gpt-4o",
        price_per_1k_tokens=5.0,
        remaining_tokens=400000,
        quality_tier="large",
        api_format="openai"
    )
    adapter = OpenAIAdapter(model)
    
    # Format a request
    request = adapter.format_request("Hello, how are you?")
    
    # Parse a response
    response = {"choices": [{"message": {"content": "I'm doing well, thank you!"}}]}
    parsed = adapter.parse_response(response)
"""

from typing import Dict, Any
from app.services.model_adapters.base_adapter import ModelAdapter
from app.models import ModelStatus


class OpenAIAdapter(ModelAdapter):
    """Adapter for OpenAI-compatible models."""
    
    def format_request(self, query: str, **kwargs) -> Dict[str, Any]:
        """Format a query into OpenAI's expected request format.
        
        Args:
            query: The user's query
            kwargs: Additional parameters
            
        Returns:
            A dictionary representing the formatted request
        """
        request = {
            "model": self.model.model_id,
            "messages": [
                {"role": "user", "content": query}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }
        
        # Add reasoning level if supported
        if self.model.reasoning_support and self.model.reasoning_level:
            request["reasoning_level"] = self.model.reasoning_level
        
        return request
    
    def parse_response(self, response: Dict[str, Any]) -> str:
        """Parse an OpenAI response into a standard format.
        
        Args:
            response: The OpenAI response
            
        Returns:
            The parsed response as a string
        """
        if "choices" in response and response["choices"]:
            return response["choices"][0]["message"]["content"]
        return ""
    
    def convert_to_openai(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a response to OpenAI format.
        
        For OpenAI models, this is a no-op as the response is already in OpenAI format.
        
        Args:
            response: The model's response
            
        Returns:
            The response in OpenAI format
        """
        return response
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle an error from the OpenAI API.
        
        Args:
            error: The exception that occurred
            
        Returns:
            An error response in a standard format
        """
        return {
            "error": {
                "message": str(error),
                "type": error.__class__.__name__,
                "code": "openai_error"
            }
        }
