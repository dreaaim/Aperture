"""Dependency injection container.

This module provides a simple dependency injection container for managing service instances.

The Container class is responsible for:
- Initializing and managing repository instances
- Initializing and managing service instances
- Providing access to service instances through getter methods

This container follows the singleton pattern, providing a single instance
of each service throughout the application.

Example:
    from app.services.container import container
    
    # Get services from the container
    repository = container.get_repository()
    cache_service = container.get_cache_service()
    intent_service = container.get_intent_service()
    model_service = container.get_model_service()
    
    # Use the services
    query = "帮我写个Python脚本"
    embedding = cache_service.embed_text(query)
    intent = intent_service.classify_intent(query)
    model = model_service.select_model(intent)
"""

from app.repositories.postgresql_repository import PostgreSQLRepository
from app.services.cache_service import CacheService
from app.services.intent_service import IntentService
from app.services.enhanced_intent_service import EnhancedIntentService
from app.services.model_service import ModelService
from app.adapters.types.llm_adapter import LLMAdapter
from app.adapters.types.embedding_adapter import EmbeddingAdapter
from app.adapters.types.reranker_adapter import RerankerAdapter
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


class Container:
    """Dependency injection container for managing service instances.
    
    This class provides a centralized way to manage and access service instances
    throughout the application. It ensures that each service is initialized only once
    and that dependencies between services are properly managed.
    
    Attributes:
        repository: The PostgreSQLRepository instance
        cache_service: The CacheService instance
        intent_service: The IntentService instance
        model_service: The ModelService instance
    """

    def __init__(self):
        """Initialize the container and register services.
        
        This method initializes the repository and all services, ensuring that
        dependencies are properly injected.
        """
        # Create span for container initialization
        with tracer.start_as_current_span("container_init") as span:
            # Initialize repository
            # The repository is a dependency for some services
            self.repository = PostgreSQLRepository()
            # Initialize default models
            self.repository.initialize_models()
            span.set_attribute("repository_initialized", True)
            
            # Initialize services
            # CacheService depends on the repository
            self.cache_service = CacheService(self.repository)
            span.set_attribute("cache_service_initialized", True)
            # IntentService has no dependencies
            self.intent_service = IntentService()
            span.set_attribute("intent_service_initialized", True)
            # EnhancedIntentService has no dependencies
            self.enhanced_intent_service = EnhancedIntentService()
            span.set_attribute("enhanced_intent_service_initialized", True)
            # ModelService depends on the repository
            self.model_service = ModelService(self.repository)
            span.set_attribute("model_service_initialized", True)
            
            # Initialize model adapters
            # Get models for adapters
            try:
                # Get embedding model
                embedding_model = self.model_service.select_embedding_model()
                self.embedding_adapter = EmbeddingAdapter(embedding_model)
                span.set_attribute("embedding_adapter_initialized", True)
                
                # Get reranker model
                reranker_model = self.model_service.select_reranker_model()
                self.reranker_adapter = RerankerAdapter(reranker_model)
                span.set_attribute("reranker_adapter_initialized", True)
                
                # Get default LLM model
                llm_model = self.model_service.select_model("chat")
                self.llm_adapter = LLMAdapter(llm_model)
                span.set_attribute("llm_adapter_initialized", True)
                
                span.set_attribute("adapters_initialized", 3)
            except Exception as e:
                span.set_attribute("adapter_initialization_error", str(e)[:100])
            
            # Set span attributes
            span.set_attribute("services_initialized", 5)

    def get_cache_service(self) -> CacheService:
        """Get an instance of CacheService.
        
        Returns:
            The CacheService instance
            
        Example:
            >>> container = Container()
            >>> cache_service = container.get_cache_service()
            >>> type(cache_service)
            <class 'app.services.cache_service.CacheService'>
        """
        # Create span for cache service retrieval
        with tracer.start_as_current_span("get_cache_service") as span:
            span.set_attribute("service_type", "CacheService")
            return self.cache_service

    def get_intent_service(self) -> IntentService:
        """Get an instance of IntentService.
        
        Returns:
            The IntentService instance
            
        Example:
            >>> container = Container()
            >>> intent_service = container.get_intent_service()
            >>> type(intent_service)
            <class 'app.services.intent_service.IntentService'>
        """
        # Create span for intent service retrieval
        with tracer.start_as_current_span("get_intent_service") as span:
            span.set_attribute("service_type", "IntentService")
            return self.intent_service
    
    def get_enhanced_intent_service(self) -> EnhancedIntentService:
        """Get an instance of EnhancedIntentService.
        
        Returns:
            The EnhancedIntentService instance
            
        Example:
            >>> container = Container()
            >>> enhanced_intent_service = container.get_enhanced_intent_service()
            >>> type(enhanced_intent_service)
            <class 'app.services.enhanced_intent_service.EnhancedIntentService'>
        """
        # Create span for enhanced intent service retrieval
        with tracer.start_as_current_span("get_enhanced_intent_service") as span:
            span.set_attribute("service_type", "EnhancedIntentService")
            return self.enhanced_intent_service

    def get_model_service(self) -> ModelService:
        """Get an instance of ModelService.
        
        Returns:
            The ModelService instance
            
        Example:
            >>> container = Container()
            >>> model_service = container.get_model_service()
            >>> type(model_service)
            <class 'app.services.model_service.ModelService'>
        """
        # Create span for model service retrieval
        with tracer.start_as_current_span("get_model_service") as span:
            span.set_attribute("service_type", "ModelService")
            return self.model_service

    def get_repository(self) -> PostgreSQLRepository:
        """Get an instance of PostgreSQLRepository.
        
        Returns:
            The PostgreSQLRepository instance
            
        Example:
            >>> container = Container()
            >>> repository = container.get_repository()
            >>> type(repository)
            <class 'app.repositories.postgresql_repository.PostgreSQLRepository'>
        """
        # Create span for repository retrieval
        with tracer.start_as_current_span("get_repository") as span:
            span.set_attribute("service_type", "PostgreSQLRepository")
            return self.repository
    
    def get_llm_adapter(self) -> LLMAdapter:
        """Get an instance of LLMAdapter.
        
        Returns:
            The LLMAdapter instance
            
        Example:
            >>> container = Container()
            >>> adapter = container.get_llm_adapter()
            >>> type(adapter)
            <class 'app.adapters.types.llm_adapter.LLMAdapter'>
        """
        # Create span for LLM adapter retrieval
        with tracer.start_as_current_span("get_llm_adapter") as span:
            span.set_attribute("adapter_type", "LLMAdapter")
            return self.llm_adapter
    
    def get_embedding_adapter(self) -> EmbeddingAdapter:
        """Get an instance of EmbeddingAdapter.
        
        Returns:
            The EmbeddingAdapter instance
            
        Example:
            >>> container = Container()
            >>> adapter = container.get_embedding_adapter()
            >>> type(adapter)
            <class 'app.adapters.types.embedding_adapter.EmbeddingAdapter'>
        """
        # Create span for embedding adapter retrieval
        with tracer.start_as_current_span("get_embedding_adapter") as span:
            span.set_attribute("adapter_type", "EmbeddingAdapter")
            return self.embedding_adapter
    
    def get_reranker_adapter(self) -> RerankerAdapter:
        """Get an instance of RerankerAdapter.
        
        Returns:
            The RerankerAdapter instance
            
        Example:
            >>> container = Container()
            >>> adapter = container.get_reranker_adapter()
            >>> type(adapter)
            <class 'app.adapters.types.reranker_adapter.RerankerAdapter'>
        """
        # Create span for reranker adapter retrieval
        with tracer.start_as_current_span("get_reranker_adapter") as span:
            span.set_attribute("adapter_type", "RerankerAdapter")
            return self.reranker_adapter


# Create a global container instance
# This global instance is used throughout the application to access services
container = Container()
