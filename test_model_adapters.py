"""Test script for model adapters and extended model service functionality.

This script tests the following features:
1. Model service's ability to select embedding models
2. Model service's ability to select reranker models
3. Model service's ability to filter models by type
4. Model adapter initialization and execution
5. Container integration of model adapters

Example usage:
    python test_model_adapters.py
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.container import container
from app.services.model_service import ModelService
from app.repositories.postgresql_repository import PostgreSQLRepository
from app.adapters.embedding_adapter import EmbeddingAdapter
from app.adapters.reranker_adapter import RerankerAdapter
from app.adapters.llm_adapter import LLMAdapter


def test_model_selection():
    """Test model selection functionality."""
    print("\n=== Testing Model Selection ===")
    
    try:
        # Test embedding model selection
        embedding_model = container.model_service.select_embedding_model()
        print(f"✓ Selected embedding model: {embedding_model.model_id}")
        print(f"  - Type: {embedding_model.model_type}")
        print(f"  - Quality tier: {embedding_model.quality_tier}")
        print(f"  - Embedding dimension: {embedding_model.embedding_dimension}")
        print(f"  - Price per 1k tokens: ${embedding_model.price_per_1k_tokens}")
        
        # Test reranker model selection
        reranker_model = container.model_service.select_reranker_model()
        print(f"\n✓ Selected reranker model: {reranker_model.model_id}")
        print(f"  - Type: {reranker_model.model_type}")
        print(f"  - Quality tier: {reranker_model.quality_tier}")
        print(f"  - Max input length: {reranker_model.max_input_length}")
        print(f"  - Price per 1k tokens: ${reranker_model.price_per_1k_tokens}")
        
        # Test LLM model selection
        llm_model = container.model_service.select_model("chat")
        print(f"\n✓ Selected LLM model: {llm_model.model_id}")
        print(f"  - Type: {llm_model.model_type}")
        print(f"  - Quality tier: {llm_model.quality_tier}")
        print(f"  - Reasoning support: {llm_model.reasoning_support}")
        print(f"  - Price per 1k tokens: ${llm_model.price_per_1k_tokens}")
        
        # Test model filtering by type
        embedding_models = container.model_service.get_models_by_type("embedding")
        print(f"\n✓ Found {len(embedding_models)} embedding models:")
        for model in embedding_models:
            print(f"  - {model.model_id} (enabled: {model.enabled})")
        
        reranker_models = container.model_service.get_models_by_type("reranker")
        print(f"\n✓ Found {len(reranker_models)} reranker models:")
        for model in reranker_models:
            print(f"  - {model.model_id} (enabled: {model.enabled})")
        
        llm_models = container.model_service.get_models_by_type("llm")
        print(f"\n✓ Found {len(llm_models)} LLM models:")
        for model in llm_models:
            print(f"  - {model.model_id} (enabled: {model.enabled})")
        
        return True
    except Exception as e:
        print(f"✗ Error in model selection: {e}")
        return False


def test_model_adapters():
    """Test model adapter functionality."""
    print("\n=== Testing Model Adapters ===")
    
    try:
        # Test embedding adapter
        print("\nTesting Embedding Adapter:")
        embedding = container.get_embedding_adapter().execute(text="Hello, world!")
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
        
        # Test batch embedding
        embeddings = container.get_embedding_adapter().execute(
            texts=["Hello, world!", "How are you?"]
        )
        print(f"✓ Generated {len(embeddings)} batch embeddings")
        print(f"  - Each embedding has {len(embeddings[0])} dimensions")
        
        # Test reranker adapter
        print("\nTesting Reranker Adapter:")
        rerank_results = container.get_reranker_adapter().execute(
            query="How to make a cake",
            documents=[
                "Recipe for chocolate cake",
                "Guide to baking bread",
                "Cake decorating tips"
            ]
        )
        print(f"✓ Reranked {len(rerank_results)} documents")
        print("  - Top results:")
        for i, result in enumerate(rerank_results[:2]):
            print(f"    {i+1}. {result['document'][:50]}... (score: {result['relevance_score']:.2f})")
        
        # Test LLM adapter
        print("\nTesting LLM Adapter:")
        llm_result = container.get_llm_adapter().execute(
            prompt="Write a short sentence about AI"
        )
        print(f"✓ Generated text: {llm_result['text'][:100]}...")
        print(f"  - Tokens used: {llm_result['tokens_used']}")
        
        return True
    except Exception as e:
        print(f"✗ Error in model adapter test: {e}")
        return False


def test_container_integration():
    """Test container integration of model adapters."""
    print("\n=== Testing Container Integration ===")
    
    try:
        # Test adapter retrieval from container
        print("Testing adapter retrieval:")
        
        # Get embedding adapter
        embedding_adapter = container.get_embedding_adapter()
        print(f"✓ Got embedding adapter: {type(embedding_adapter).__name__}")
        print(f"  - Model: {embedding_adapter.model.model_id}")
        
        # Get reranker adapter
        reranker_adapter = container.get_reranker_adapter()
        print(f"✓ Got reranker adapter: {type(reranker_adapter).__name__}")
        print(f"  - Model: {reranker_adapter.model.model_id}")
        
        # Get LLM adapter
        llm_adapter = container.get_llm_adapter()
        print(f"✓ Got LLM adapter: {type(llm_adapter).__name__}")
        print(f"  - Model: {llm_adapter.model.model_id}")
        
        return True
    except Exception as e:
        print(f"✗ Error in container integration test: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Model Adapters and Extended Model Service Functionality")
    print("=" * 70)
    
    # Run tests
    tests = [
        test_model_selection,
        test_model_adapters,
        test_container_integration
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
        print("✓ All tests passed! The model adapter functionality is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
