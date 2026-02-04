"""Google Gemini model adapter.

This module provides an adapter for Google Gemini models, handling request
formatting, response parsing, and format conversion.

Example:
    from app.services.model_adapters.gemini_adapter import GeminiAdapter
    from app.models import ModelStatus
    
    model = ModelStatus(
        model_id="gemini-2.5-pro",
        price_per_1k_tokens=2.0,
        remaining_tokens=500000,
        quality_tier="large",
        api_format="gemini"
    )
    adapter = GeminiAdapter(model)
    
    # Format a request
    request = adapter.format_request("Hello, how are you?")
    
    # Parse a response
    response = {"candidates": [{"content": {"parts": [{"text": "I'm doing well, thank you!"}]}}]}
    parsed = adapter.parse_response(response)
"""

from typing import Dict, Any
from app.services.model_adapters.base_adapter import ModelAdapter
from app.models import ModelStatus


class GeminiAdapter(ModelAdapter):
    """Adapter for Google Gemini models."""
    
    def format_request(self, query: str, **kwargs) -> Dict[str, Any]:
        """Format a query into Gemini's expected request format.
        
        Args:
            query: The user's query
            kwargs: Additional parameters
            
        Returns:
            A dictionary representing the formatted request
        """
        request = {
            "contents": [
                {"role": "user", "parts": [{"text": query}]}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 1000)
        }
        
        # Add reasoning level if supported
        if self.model.reasoning_support and self.model.reasoning_level:
            request["reasoning_effort"] = self.model.reasoning_level
        
        return request
    
    def parse_response(self, response: Dict[str, Any]) -> str:
        """Parse a Gemini response into a standard format.
        
        Args:
            response: The Gemini response
            
        Returns:
            The parsed response as a string
        """
        if "candidates" in response and response["candidates"]:
            candidate = response["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                text_parts = []
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        text_parts.append(part["text"])
                return "".join(text_parts)
        return ""
    
    def convert_to_openai(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Gemini response to OpenAI format.
        
        Args:
            response: The Gemini response
            
        Returns:
            The response in OpenAI format
        """
        openai_response = {
            "id": response.get("name", ""),
            "object": "chat.completion",
            "created": int(response.get("create_time", {}).get("seconds", 0)),
            "model": self.model.model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": self.parse_response(response)
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": response.get("usage_metadata", {})
        }
        return openai_response
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle an error from the Gemini API.
        
        Args:
            error: The exception that occurred
            
        Returns:
            An error response in a standard format
        """
        return {
            "error": {
                "message": str(error),
                "type": error.__class__.__name__,
                "code": "gemini_error"
            }
        }
