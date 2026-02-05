"""Embedding model adapter implementation.

This module provides an adapter for embedding models, handling:
- Model initialization
- Text embedding generation
- Batch embedding support
- Embedding dimension management

Example:
    from app.adapters.embedding_adapter import EmbeddingAdapter
    from app.models import ModelStatus
    
    # Create model configuration
    model_config = ModelStatus(
        model_id="text-embedding-3-small",
        model_type="embedding",
        price_per_1k_tokens=0.00015,
        remaining_tokens=1000000,
        quality_tier="small",
        api_format="openai",
        embedding_dimension=1536
    )
    
    # Create adapter
    adapter = EmbeddingAdapter(model_config)
    
    # Generate embedding
    embedding = adapter.execute(text="Hello, world!")
    print(len(embedding))  # Output: 1536
    
    # Generate batch embeddings
    embeddings = adapter.execute(
        texts=["Hello, world!", "How are you?"]
    )
    print(len(embeddings))  # Output: 2
"""

from typing import List, Optional, Any
from app.adapters.base.core_adapter import BaseAdapter
from app.models import ModelStatus
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


class EmbeddingAdapter(BaseAdapter):
    """Adapter for embedding models.
    
    This adapter handles the initialization and execution of embedding models,
    providing methods for generating text embeddings and batch embeddings.
    """
    
    def initialize(self, model: ModelStatus):
        """Initialize the embedding adapter for the given model.
        
        Args:
            model: The embedding model configuration to initialize with
        """
        with tracer.start_as_current_span("initialize_embedding_adapter", attributes={
            "model_id": model.model_id,
            "model_type": model.model_type,
            "embedding_dimension": model.embedding_dimension,
            "api_format": model.api_format
        }) as span:
            # Validate model type
            if model.model_type != "embedding":
                raise ValueError(f"Expected model_type='embedding', got '{model.model_type}'")
            
            # Initialize API client based on api_format
            # This would be expanded with actual API client initialization
            self.api_format = model.api_format
            self.embedding_dimension = model.embedding_dimension
            
            # Set initialization attributes
            span.set_attribute("initialized", True)
            span.set_attribute("api_format", model.api_format)
            span.set_attribute("embedding_dimension", model.embedding_dimension)
    
    def execute(self, **kwargs) -> Any:
        """Execute the embedding model with the given parameters.
        
        Args:
            text: Single text to embed (for single embedding)
            texts: List of texts to embed (for batch embedding)
            model_id: Optional model ID to override the default
            
        Returns:
            For single text: Embedding vector as list of floats
            For batch texts: List of embedding vectors
        """
        with tracer.start_as_current_span("execute_embedding", attributes={
            "model_id": self.model.model_id,
            "api_format": self.api_format,
            "embedding_dimension": self.embedding_dimension
        }) as span:
            # Determine if this is a single or batch request
            text = kwargs.get("text")
            texts = kwargs.get("texts")
            
            if text and texts:
                raise ValueError("Cannot specify both 'text' and 'texts' parameters")
            
            if not text and not texts:
                raise ValueError("Must specify either 'text' or 'texts' parameter")
            
            # Handle single text embedding
            if text:
                span.set_attribute("request_type", "single")
                span.set_attribute("text_length", len(text))
                
                # Generate embedding (mock implementation)
                # In a real implementation, this would call the actual API
                embedding = self._generate_embedding(text)
                
                span.set_attribute("embedding_generated", True)
                span.set_attribute("embedding_dimension", len(embedding))
                return embedding
            
            # Handle batch text embedding
            elif texts:
                span.set_attribute("request_type", "batch")
                span.set_attribute("text_count", len(texts))
                span.set_attribute("total_text_length", sum(len(t) for t in texts))
                
                # Generate batch embeddings (mock implementation)
                embeddings = [self._generate_embedding(t) for t in texts]
                
                span.set_attribute("embeddings_generated", True)
                span.set_attribute("embedding_count", len(embeddings))
                span.set_attribute("embedding_dimension", len(embeddings[0]) if embeddings else 0)
                return embeddings
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        with tracer.start_as_current_span("generate_embedding", attributes={
            "text_length": len(text),
            "model_id": self.model.model_id
        }) as span:
            # Mock implementation - in a real system, this would call the actual API
            # For example, using OpenAI's API:
            # response = openai.embeddings.create(
            #     model=self.model.model_id,
            #     input=text
            # )
            # return response.data[0].embedding
            
            # Generate a mock embedding with the correct dimension
            embedding = [0.0] * self.embedding_dimension
            
            # Add some variation based on text to make it unique
            for i in range(min(len(text), self.embedding_dimension)):
                embedding[i] = ord(text[i]) / 255.0 - 0.5
            
            span.set_attribute("embedding_generated", True)
            span.set_attribute("embedding_dimension", len(embedding))
            return embedding
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension of the current model.
        
        Returns:
            The embedding dimension
        """
        return self.embedding_dimension
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate an embedding vector.
        
        Args:
            embedding: The embedding vector to validate
            
        Returns:
            True if the embedding is valid, False otherwise
        """
        return (
            isinstance(embedding, list) and
            all(isinstance(x, float) for x in embedding) and
            len(embedding) == self.embedding_dimension
        )
