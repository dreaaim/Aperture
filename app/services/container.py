"""Dependency injection container."""

from app.repositories.memory_repository import MemoryRepository
from app.services.cache_service import CacheService
from app.services.intent_service import IntentService
from app.services.model_service import ModelService


class Container:
    """Dependency injection container for managing service instances."""

    def __init__(self):
        """Initialize the container and register services."""
        # Initialize repository
        self.repository = MemoryRepository()
        
        # Initialize services
        self.cache_service = CacheService(self.repository)
        self.intent_service = IntentService()
        self.model_service = ModelService(self.repository)

    def get_cache_service(self) -> CacheService:
        """Get an instance of CacheService."""
        return self.cache_service

    def get_intent_service(self) -> IntentService:
        """Get an instance of IntentService."""
        return self.intent_service

    def get_model_service(self) -> ModelService:
        """Get an instance of ModelService."""
        return self.model_service

    def get_repository(self) -> MemoryRepository:
        """Get an instance of MemoryRepository."""
        return self.repository


# Create a global container instance
container = Container()
