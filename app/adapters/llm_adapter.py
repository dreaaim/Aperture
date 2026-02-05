"""LLM model adapter implementation.

This module provides an adapter for LLM models, handling:
- Model initialization
- Text generation
- Chat completion
- Reasoning level support
- Token usage tracking

Example:
    from app.adapters.llm_adapter import LLMAdapter
    from app.models import ModelStatus
    
    # Create model configuration
    model_config = ModelStatus(
        model_id="gpt-4o",
        model_type="llm",
        price_per_1k_tokens=0.005,
        remaining_tokens=100000,
        quality_tier="large",
        api_format="openai",
        reasoning_support=True
    )
    
    # Create adapter
    adapter = LLMAdapter(model_config)
    
    # Generate text
    result = adapter.execute(
        prompt="Write a short story about a robot learning to paint"
    )
    print(result["text"])
    
    # Chat completion
    chat_result = adapter.execute(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    )
    print(chat_result["text"])
"""

from typing import List, Dict, Any, Optional
from app.adapters.base_adapter import BaseAdapter
from app.models import ModelStatus
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


class LLMAdapter(BaseAdapter):
    """Adapter for LLM models.
    
    This adapter handles the initialization and execution of LLM models,
    providing methods for text generation, chat completion, and other LLM-specific tasks.
    """
    
    def initialize(self, model: ModelStatus):
        """Initialize the LLM adapter for the given model.
        
        Args:
            model: The LLM model configuration to initialize with
        """
        with tracer.start_as_current_span("initialize_llm_adapter", attributes={
            "model_id": model.model_id,
            "model_type": model.model_type,
            "quality_tier": model.quality_tier,
            "api_format": model.api_format,
            "reasoning_support": model.reasoning_support
        }) as span:
            # Validate model type
            if model.model_type != "llm":
                raise ValueError(f"Expected model_type='llm', got '{model.model_type}'")
            
            # Initialize API client based on api_format
            # This would be expanded with actual API client initialization
            self.api_format = model.api_format
            self.reasoning_support = model.reasoning_support
            
            # Set initialization attributes
            span.set_attribute("initialized", True)
            span.set_attribute("api_format", model.api_format)
            span.set_attribute("reasoning_support", model.reasoning_support)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the LLM model with the given parameters.
        
        Args:
            prompt: Text prompt for text generation
            messages: List of messages for chat completion
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum number of tokens to generate
            reasoning_level: Reasoning level (low/medium/high)
            model_id: Optional model ID to override the default
            
        Returns:
            Dictionary with generated text and metadata
        """
        with tracer.start_as_current_span("execute_llm", attributes={
            "model_id": self.model.model_id,
            "api_format": self.api_format,
            "reasoning_support": self.reasoning_support
        }) as span:
            # Determine if this is a text generation or chat completion request
            prompt = kwargs.get("prompt")
            messages = kwargs.get("messages")
            
            if prompt and messages:
                raise ValueError("Cannot specify both 'prompt' and 'messages' parameters")
            
            if not prompt and not messages:
                raise ValueError("Must specify either 'prompt' or 'messages' parameter")
            
            # Get additional parameters
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            reasoning_level = kwargs.get("reasoning_level", "medium")
            
            span.set_attribute("request_type", "prompt" if prompt else "chat")
            span.set_attribute("temperature", temperature)
            span.set_attribute("max_tokens", max_tokens)
            span.set_attribute("reasoning_level", reasoning_level)
            
            if prompt:
                span.set_attribute("prompt_length", len(prompt))
            else:
                span.set_attribute("message_count", len(messages))
                span.set_attribute("total_message_length", sum(len(msg.get("content", "")) for msg in messages))
            
            # Execute model (mock implementation)
            # In a real implementation, this would call the actual API
            result = self._execute_model(
                prompt=prompt,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                reasoning_level=reasoning_level
            )
            
            span.set_attribute("execution_completed", True)
            span.set_attribute("generated_text_length", len(result["text"]))
            span.set_attribute("tokens_used", result["tokens_used"])
            
            return result
    
    def _execute_model(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        reasoning_level: str = "medium"
    ) -> Dict[str, Any]:
        """Execute the model with the given parameters.
        
        Args:
            prompt: Text prompt for text generation
            messages: List of messages for chat completion
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            reasoning_level: Reasoning level
            
        Returns:
            Dictionary with generated text and metadata
        """
        with tracer.start_as_current_span("execute_model", attributes={
            "temperature": temperature,
            "max_tokens": max_tokens,
            "reasoning_level": reasoning_level
        }) as span:
            # Mock implementation - in a real system, this would call the actual API
            # For example, using OpenAI's API:
            # if prompt:
            #     response = openai.completions.create(
            #         model=self.model.model_id,
            #         prompt=prompt,
            #         temperature=temperature,
            #         max_tokens=max_tokens
            #     )
            #     return {
            #         "text": response.choices[0].text,
            #         "tokens_used": response.usage.total_tokens
            #     }
            # else:
            #     response = openai.chat.completions.create(
            #         model=self.model.model_id,
            #         messages=messages,
            #         temperature=temperature,
            #         max_tokens=max_tokens
            #     )
            #     return {
            #         "text": response.choices[0].message.content,
            #         "tokens_used": response.usage.total_tokens
            #     }
            
            # Generate mock response
            if prompt:
                generated_text = f"This is a mock response to your prompt: {prompt[:50]}..."
            else:
                last_message = messages[-1]["content"] if messages else ""
                generated_text = f"This is a mock response to your question: {last_message[:50]}..."
            
            # Calculate mock token usage
            input_text = prompt or " ".join(msg.get("content", "") for msg in messages)
            tokens_used = len(input_text.split()) + len(generated_text.split())
            
            result = {
                "text": generated_text,
                "tokens_used": tokens_used,
                "model_id": self.model.model_id,
                "reasoning_level": reasoning_level
            }
            
            span.set_attribute("response_generated", True)
            span.set_attribute("tokens_used", tokens_used)
            
            return result
    
    def get_reasoning_levels(self) -> List[str]:
        """Get the available reasoning levels for the model.
        
        Returns:
            List of available reasoning levels
        """
        if self.reasoning_support:
            return ["low", "medium", "high"]
        else:
            return ["medium"]
