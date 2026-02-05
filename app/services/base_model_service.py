"""Abstract base class for model services.

This module defines the abstract base class for model services, providing a
common interface for different types of model services.

The ModelService interface defines methods for:
- Model selection
- Model configuration
- Model usage
- Model monitoring

Example:
    from app.services.base_model_service import ModelService
    from app.repositories.memory_repository import MemoryRepository
    
    class MyModelService(ModelService):
        def select_model(self, intent: str):
            # Implementation
            pass
        
        def select_few_shot_model(self):
            # Implementation
            pass
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.models import ModelStatus
from app.repositories.memory_repository import MemoryRepository


class BaseModelService(ABC):
    """Abstract base class for model services.
    
    This class defines the common interface for all model services, ensuring
    that they all implement the required methods for model selection, configuration,
    and usage.
    """
    
    def __init__(self, repository: MemoryRepository):
        """Initialize the model service with a repository.
        
        Args:
            repository: The memory repository instance for accessing request logs and model ratings
        """
        self.repository = repository
    
    @abstractmethod
    def select_model(self, intent: str, reasoning_level: Optional[str] = None) -> ModelStatus:
        """Select the best model for the given intent.
        
        Args:
            intent: The intent category to select a model for
            reasoning_level: Optional reasoning level (low/medium/high)
            
        Returns:
            The best model for the given intent
        """
        pass
    
    @abstractmethod
    def select_few_shot_model(self) -> ModelStatus:
        """Select a small model for few-shot learning.
        
        Returns:
            A small model suitable for few-shot learning
        """
        pass
    
    @abstractmethod
    def get_model_by_id(self, model_id: str) -> Optional[ModelStatus]:
        """Get a model by its ID.
        
        Args:
            model_id: The ID of the model to get
            
        Returns:
            The model with the given ID, or None if not found
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[ModelStatus]:
        """Get all available models.
        
        Returns:
            A list of all available models
        """
        pass
    
    @abstractmethod
    def update_model_status(self, model_id: str, **kwargs) -> bool:
        """Update the status of a model.
        
        Args:
            model_id: The ID of the model to update
            kwargs: The attributes to update
            
        Returns:
            True if the model was updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def select_embedding_model(self) -> ModelStatus:
        """Select the best embedding model.
        
        Returns:
            The best embedding model based on scoring
        """
        pass
    
    @abstractmethod
    def select_reranker_model(self) -> ModelStatus:
        """Select the best reranker model.
        
        Returns:
            The best reranker model based on scoring
        """
        pass
    
    @abstractmethod
    def get_models_by_type(self, model_type: str) -> List[ModelStatus]:
        """Get models by type.
        
        Args:
            model_type: The type of models to get
            
        Returns:
            List of models of the specified type
        """
        pass
