"""Claude model adapter.

This module provides an adapter for Claude models, handling request
formatting, response parsing, and format conversion.

Example:
    from app.services.model_adapters.claude_adapter import ClaudeAdapter
    from app.models import ModelStatus
    
    model = ModelStatus(
        model_id="claude-3.5-sonnet",
        price_per_1k_tokens=3.5,
        remaining_tokens=300000,
        quality_tier="large",
        api_format="claude"
    )
    adapter = ClaudeAdapter(model)
    
    # Format a request
    request = adapter.format_request("Hello, how are you?")
    
    # Parse a response
    response = {"content": [{"type": "text", "text": "I'm doing well, thank you!"}]}
    parsed = adapter.parse_response(response)
"""

from typing import Dict, Any
from app.adapters.base.provider_base import ModelAdapter
from app.models import ModelStatus


class ClaudeAdapter(ModelAdapter):
    """Adapter for Claude models."""
    
    def format_request(self, query: str, **kwargs) -> Dict[str, Any]:
        """Format a query into Claude's expected request format.
        
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
        
        # Add thinking mode if supported
        if self.model.reasoning_support:
            request["thinking"] = True
        
        return request
    
    def parse_response(self, response: Dict[str, Any]) -> str:
        """Parse a Claude response into a standard format.
        
        Args:
            response: The Claude response
            
        Returns:
            The parsed response as a string
        """
        if "content" in response:
            text_parts = []
            for part in response["content"]:
                if part["type"] == "text":
                    text_parts.append(part["text"])
            return "".join(text_parts)
        return ""
    
    def convert_to_openai(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Claude response to OpenAI format.
        
        Args:
            response: The Claude response
            
        Returns:
            The response in OpenAI format
        """
        openai_response = {
            "id": response.get("id", ""),
            "object": "chat.completion",
            "created": response.get("created", 0),
            "model": response.get("model", self.model.model_id),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": self.parse_response(response)
                    },
                    "finish_reason": response.get("stop_reason", "stop")
                }
            ],
            "usage": response.get("usage", {})
        }
        return openai_response
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle an error from the Claude API.
        
        Args:
            error: The exception that occurred
            
        Returns:
            An error response in a standard format
        """
        return {
            "error": {
                "message": str(error),
                "type": error.__class__.__name__,
                "code": "claude_error"
            }
        }
