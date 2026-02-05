"""Base adapter abstract class for model interactions.

This module defines the abstract base class for all model adapters, providing
common interface methods that all adapters must implement.

The BaseAdapter interface defines methods for:
- Model initialization
- Model configuration
- Model execution
- Model result processing

Example:
    from app.adapters.base_adapter import BaseAdapter
    from app.models import ModelStatus
    
    class MyAdapter(BaseAdapter):
        def initialize(self, model: ModelStatus):
            # Implementation
            pass
        
        def execute(self, **kwargs):
            # Implementation
            pass
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from app.models import ModelStatus


class BaseAdapter(ABC):
    """Abstract base class for model adapters.
    
    This class defines the common interface for all model adapters, ensuring
    that they all implement the required methods for model initialization,
    configuration, execution, and result processing.
    """
    
    def __init__(self, model: ModelStatus):
        """Initialize the adapter with a model configuration.
        
        Args:
            model: The model configuration to use
        """
        self.model = model
        self.initialize(model)
    
    @abstractmethod
    def initialize(self, model: ModelStatus):
        """Initialize the adapter for the given model.
        
        Args:
            model: The model configuration to initialize with
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the model with the given parameters.
        
        Args:
            **kwargs: Parameters specific to the model type
            
        Returns:
            The result of the model execution
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_id": self.model.model_id,
            "model_type": self.model.model_type,
            "quality_tier": self.model.quality_tier,
            "api_format": self.model.api_format,
            "enabled": self.model.enabled,
            "rate_limit": self.model.rate_limit,
            "max_concurrency": self.model.max_concurrency,
            "timeout": self.model.timeout
        }
    
    def update_model_status(self, **kwargs):
        """Update the model status with new values.
        
        Args:
            **kwargs: Model status attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                setattr(self.model, key, value)
