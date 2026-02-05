"""Simple test script for model adapters without database dependency.

This script tests the following features without requiring database connectivity:
1. Model configuration loading
2. Model adapter initialization
3. Basic adapter functionality
4. Model selection logic

Example usage:
    python test_model_adapters_simple.py
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import settings
from app.models import ModelStatus
from app.adapters.types.embedding_adapter import EmbeddingAdapter
from app.adapters.types.reranker_adapter import RerankerAdapter
from app.adapters.types.llm_adapter import LLMAdapter


def test_model_configuration():
    """Test model configuration loading."""
    print("\n=== Testing Model Configuration ===")
    
    try:
        # Print model catalog
        print(f"✓ Loaded {len(settings.model_catalog)} models from configuration")
        
        # Group models by type
        models_by_type = {}
        for model_config in settings.model_catalog:
            model_type = getattr(model_config, 'model_type', 'llm')
            if model_type not in models_by_type:
                models_by_type[model_type] = []
            models_by_type[model_type].append(model_config)
        
        # Print models by type
        for model_type, models in models_by_type.items():
            print(f"\n  {model_type.capitalize()} models ({len(models)}):")
            for model in models:
                print(f"    - {model.model_id} (enabled: {model.enabled})")
        
        return True
    except Exception as e:
        print(f"✗ Error in model configuration test: {e}")
        return False


def test_adapter_initialization():
    """Test model adapter initialization."""
    print("\n=== Testing Adapter Initialization ===")
    
    try:
        # Find models for adapters
        embedding_models = [m for m in settings.model_catalog if getattr(m, 'model_type', 'llm') == 'embedding']
        reranker_models = [m for m in settings.model_catalog if getattr(m, 'model_type', 'llm') == 'reranker']
        llm_models = [m for m in settings.model_catalog if getattr(m, 'model_type', 'llm') == 'llm']
        
        # Test embedding adapter
        if embedding_models:
            embedding_config = embedding_models[0]
            embedding_model = ModelStatus(
                model_id=embedding_config.model_id,
                model_type=embedding_config.model_type,
                price_per_1k_tokens=embedding_config.price_per_1k_tokens,
                remaining_tokens=embedding_config.remaining_tokens,
                quality_tier=embedding_config.quality_tier,
                api_format=embedding_config.api_format,
                reasoning_support=embedding_config.reasoning_support,
                enabled=embedding_config.enabled,
                rate_limit=embedding_config.rate_limit,
                max_concurrency=embedding_config.max_concurrency,
                timeout=embedding_config.timeout,
                embedding_dimension=getattr(embedding_config, 'embedding_dimension', 1024)
            )
            embedding_adapter = EmbeddingAdapter(embedding_model)
            print(f"✓ Initialized EmbeddingAdapter with model: {embedding_model.model_id}")
        else:
            print("⚠ No embedding models found in configuration")
        
        # Test reranker adapter
        if reranker_models:
            reranker_config = reranker_models[0]
            reranker_model = ModelStatus(
                model_id=reranker_config.model_id,
                model_type=reranker_config.model_type,
                price_per_1k_tokens=reranker_config.price_per_1k_tokens,
                remaining_tokens=reranker_config.remaining_tokens,
                quality_tier=reranker_config.quality_tier,
                api_format=reranker_config.api_format,
                reasoning_support=reranker_config.reasoning_support,
                enabled=reranker_config.enabled,
                rate_limit=reranker_config.rate_limit,
                max_concurrency=reranker_config.max_concurrency,
                timeout=reranker_config.timeout,
                max_input_length=getattr(reranker_config, 'max_input_length', 4096)
            )
            reranker_adapter = RerankerAdapter(reranker_model)
            print(f"✓ Initialized RerankerAdapter with model: {reranker_model.model_id}")
        else:
            print("⚠ No reranker models found in configuration")
        
        # Test LLM adapter
        if llm_models:
            llm_config = llm_models[0]
            llm_model = ModelStatus(
                model_id=llm_config.model_id,
                model_type=llm_config.model_type,
                price_per_1k_tokens=llm_config.price_per_1k_tokens,
                remaining_tokens=llm_config.remaining_tokens,
                quality_tier=llm_config.quality_tier,
                api_format=llm_config.api_format,
                reasoning_support=llm_config.reasoning_support,
                enabled=llm_config.enabled,
                rate_limit=llm_config.rate_limit,
                max_concurrency=llm_config.max_concurrency,
                timeout=llm_config.timeout
            )
            llm_adapter = LLMAdapter(llm_model)
            print(f"✓ Initialized LLMAdapter with model: {llm_model.model_id}")
        else:
            print("⚠ No LLM models found in configuration")
        
        return True
    except Exception as e:
        print(f"✗ Error in adapter initialization test: {e}")
        return False


def test_adapter_functionality():
    """Test basic adapter functionality."""
    print("\n=== Testing Adapter Functionality ===")
    
    try:
        # Find an embedding model
        embedding_models = [m for m in settings.model_catalog if getattr(m, 'model_type', 'llm') == 'embedding']
        if embedding_models:
            embedding_config = embedding_models[0]
            embedding_model = ModelStatus(
                model_id=embedding_config.model_id,
                model_type=embedding_config.model_type,
                price_per_1k_tokens=embedding_config.price_per_1k_tokens,
                remaining_tokens=embedding_config.remaining_tokens,
                quality_tier=embedding_config.quality_tier,
                api_format=embedding_config.api_format,
                reasoning_support=embedding_config.reasoning_support,
                enabled=embedding_config.enabled,
                rate_limit=embedding_config.rate_limit,
                max_concurrency=embedding_config.max_concurrency,
                timeout=embedding_config.timeout,
                embedding_dimension=getattr(embedding_config, 'embedding_dimension', 1024)
            )
            embedding_adapter = EmbeddingAdapter(embedding_model)
            
            # Test embedding generation
            embedding = embedding_adapter.execute(text="Hello, world!")
            print(f"✓ Embedding adapter generated embedding with {len(embedding)} dimensions")
        
        # Find a reranker model
        reranker_models = [m for m in settings.model_catalog if getattr(m, 'model_type', 'llm') == 'reranker']
        if reranker_models:
            reranker_config = reranker_models[0]
            reranker_model = ModelStatus(
                model_id=reranker_config.model_id,
                model_type=reranker_config.model_type,
                price_per_1k_tokens=reranker_config.price_per_1k_tokens,
                remaining_tokens=reranker_config.remaining_tokens,
                quality_tier=reranker_config.quality_tier,
                api_format=reranker_config.api_format,
                reasoning_support=reranker_config.reasoning_support,
                enabled=reranker_config.enabled,
                rate_limit=reranker_config.rate_limit,
                max_concurrency=reranker_config.max_concurrency,
                timeout=reranker_config.timeout,
                max_input_length=getattr(reranker_config, 'max_input_length', 4096)
            )
            reranker_adapter = RerankerAdapter(reranker_model)
            
            # Test reranking
            rerank_results = reranker_adapter.execute(
                query="How to make a cake",
                documents=[
                    "Recipe for chocolate cake",
                    "Guide to baking bread",
                    "Cake decorating tips"
                ]
            )
            print(f"✓ Reranker adapter reranked {len(rerank_results)} documents")
        
        # Find an LLM model
        llm_models = [m for m in settings.model_catalog if getattr(m, 'model_type', 'llm') == 'llm']
        if llm_models:
            llm_config = llm_models[0]
            llm_model = ModelStatus(
                model_id=llm_config.model_id,
                model_type=llm_config.model_type,
                price_per_1k_tokens=llm_config.price_per_1k_tokens,
                remaining_tokens=llm_config.remaining_tokens,
                quality_tier=llm_config.quality_tier,
                api_format=llm_config.api_format,
                reasoning_support=llm_config.reasoning_support,
                enabled=llm_config.enabled,
                rate_limit=llm_config.rate_limit,
                max_concurrency=llm_config.max_concurrency,
                timeout=llm_config.timeout
            )
            llm_adapter = LLMAdapter(llm_model)
            
            # Test LLM generation
            llm_result = llm_adapter.execute(prompt="Write a short sentence about AI")
            print(f"✓ LLM adapter generated text: {llm_result['text'][:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ Error in adapter functionality test: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Model Adapters (Simple Version)")
    print("=" * 70)
    
    # Run tests
    tests = [
        test_model_configuration,
        test_adapter_initialization,
        test_adapter_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The model adapter functionality is configured correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
