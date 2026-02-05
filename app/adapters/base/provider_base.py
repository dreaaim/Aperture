"""Abstract base class for model API adapters.

This module defines the abstract base class for model API adapters, providing a
common interface for different types of model API formats.

The ModelAdapter interface defines methods for:
- Request formatting
- Response parsing
- Error handling
- Format conversion

Example:
    from app.services.model_adapters.base_adapter import ModelAdapter
    from app.models import ModelStatus
    
    class OpenAIAdapter(ModelAdapter):
        def format_request(self, query, **kwargs):
            # Implementation
            pass
        
        def parse_response(self, response):
            # Implementation
            pass
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models import ModelStatus


class ModelAdapter(ABC):
    """Abstract base class for model API adapters.
    
    This class defines the common interface for all model API adapters, ensuring
    that they all implement the required methods for request formatting, response
    parsing, and error handling.
    """
    
    def __init__(self, model: ModelStatus):
        """Initialize the adapter with a model.
        
        Args:
            model: The model to adapt
        """
        self.model = model
    
    @abstractmethod
    def format_request(self, query: str, **kwargs) -> Dict[str, Any]:
        """Format a query into the model's expected request format.
        
        Args:
            query: The user's query
            kwargs: Additional parameters
            
        Returns:
            A dictionary representing the formatted request
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> str:
        """Parse a model's response into a standard format.
        
        Args:
            response: The model's response
            
        Returns:
            The parsed response as a string
        """
        pass
    
    @abstractmethod
    def convert_to_openai(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a response to OpenAI format.
        
        Args:
            response: The model's response
            
        Returns:
            The response in OpenAI format
        """
        pass
    
    @abstractmethod
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle an error from the model API.
        
        Args:
            error: The exception that occurred
            
        Returns:
            An error response in a standard format
        """
        pass
    
    def get_api_format(self) -> str:
        """Get the API format type.
        
        Returns:
            The API format type
        """
        return self.model.api_format
