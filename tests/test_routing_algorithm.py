"""Tests for the routing algorithm improvements.

This module tests the enhanced routing algorithm with:
1. Intent complexity evaluation
2. Dynamic weight adjustment
3. Concurrency control
4. Circuit breaker execution
5. Gateway service integration

Example:
    $ python -m pytest tests/test_routing_algorithm.py -v
"""

import pytest
import asyncio
from app.repositories.memory_repository import MemoryRepository
from app.services.model_service import ModelService
from app.services.routing_service import RoutingService
from app.services.gateway_service import GatewayService


class TestRoutingAlgorithm:
    """Test suite for routing algorithm improvements."""
    
    @pytest.fixture
    def setup_services(self):
        """Setup test services."""
        repository = MemoryRepository()
        model_service = ModelService(repository)
        routing_service = RoutingService(model_service)
        gateway_service = GatewayService(model_service, routing_service)
        return {
            "repository": repository,
            "model_service": model_service,
            "routing_service": routing_service,
            "gateway_service": gateway_service
        }
    
    def test_intent_complexity_evaluation(self, setup_services):
        """Test intent complexity evaluation."""
        routing_service = setup_services["routing_service"]
        
        # Test different queries with expected complexity ranges
        test_cases = [
            ("帮我写个Python脚本", 0.6, 0.9),  # code intent, high complexity
            ("今天天气怎么样", 0.2, 0.4),  # chat intent, low complexity
            ("为什么天空是蓝色的", 0.5, 0.8),  # reasoning intent, medium-high complexity
            ("帮我写个营销文案", 0.4, 0.7),  # creative intent, medium complexity
            ("这是一个普通的问题", 0.3, 0.5)  # general intent, medium-low complexity
        ]
        
        for query, min_complexity, max_complexity in test_cases:
            complexity = routing_service.get_intent_complexity(query)
            assert min_complexity <= complexity <= max_complexity, \
                f"Complexity for '{query}' should be between {min_complexity} and {max_complexity}, got {complexity}"
    
    def test_model_weight_calculation(self, setup_services):
        """Test model weight calculation with dynamic adjustments."""
        routing_service = setup_services["routing_service"]
        model_service = setup_services["model_service"]
        
        # Get a model to test
        models = model_service.get_available_models()
        assert len(models) > 0, "No models available for testing"
        test_model = models[0]
        
        # Test weight calculation with different complexities
        weights = []
        for complexity in [0.1, 0.5, 0.9]:
            weight = routing_service._calculate_model_weight(test_model, "code", complexity)
            weights.append(weight)
            assert weight > 0, f"Weight should be positive, got {weight}"
        
        # Test that higher complexity gives higher weight to larger models
        if test_model.quality_tier == "large":
            assert weights[2] > weights[1] > weights[0], \
                "Large model should get higher weight with higher complexity"
        elif test_model.quality_tier == "small":
            assert weights[0] > weights[1] > weights[2], \
                "Small model should get higher weight with lower complexity"
    
    def test_cold_start_strategy(self, setup_services):
        """Test cold start strategy for new models."""
        model_service = setup_services["model_service"]
        
        # Test initial rating for a model
        models = model_service.get_available_models()
        assert len(models) > 0, "No models available for testing"
        test_model = models[0]
        
        initial_rating = model_service.get_initial_model_rating(test_model.model_id)
        assert 0.0 <= initial_rating <= 1.0, \
            f"Initial rating should be between 0.0 and 1.0, got {initial_rating}"
        
        # Test exploration budget
        exploration_budget = model_service.get_exploration_budget(test_model.model_id)
        assert 0.0 <= exploration_budget <= 0.2, \
            f"Exploration budget should be between 0.0 and 0.2, got {exploration_budget}"
    
    def test_circuit_breaker_execution(self, setup_services):
        """Test circuit breaker execution with fallback."""
        routing_service = setup_services["routing_service"]
        
        # Test execute_with_fallback with a valid model
        messages = [{"role": "user", "content": "Test message"}]
        response = asyncio.run(routing_service.execute_with_fallback("gpt-4o-mini", messages))
        
        assert "model" in response, "Response should contain model"
        assert "text" in response, "Response should contain text"
        assert "usage" in response, "Response should contain usage"
        assert response["text"] != "", "Response text should not be empty"
    
    def test_gateway_service_integration(self, setup_services):
        """Test gateway service integration."""
        gateway_service = setup_services["gateway_service"]
        
        # Test processing a simple query
        query = "今天天气怎么样"
        result = asyncio.run(gateway_service.process_query(query))
        
        assert "content" in result, "Result should contain content"
        assert "type" in result, "Result should contain type"
        assert "intent" in result, "Result should contain intent"
        assert "confidence" in result, "Result should contain confidence"
        assert result["content"] != "", "Result content should not be empty"
    
    def test_batch_processing(self, setup_services):
        """Test batch processing of multiple queries."""
        gateway_service = setup_services["gateway_service"]
        
        # Test batch processing
        queries = [
            "帮我写个Python脚本",
            "今天天气怎么样",
            "为什么天空是蓝色的"
        ]
        results = asyncio.run(gateway_service.batch_process_queries(queries))
        
        assert len(results) == len(queries), \
            f"Expected {len(queries)} results, got {len(results)}"
        
        for i, result in enumerate(results):
            assert "content" in result, f"Result {i} should contain content"
            assert "type" in result, f"Result {i} should contain type"
            assert "intent" in result, f"Result {i} should contain intent"
            assert result["content"] != "", f"Result {i} content should not be empty"
    
    def test_concurrency_control(self, setup_services):
        """Test concurrency control."""
        routing_service = setup_services["routing_service"]
        
        # Clear active requests before test
        routing_service.active_requests.clear()
        
        # Get initial active requests count
        initial_count = len(routing_service.active_requests)
        
        # Get model by weight to increment active requests
        selected_model = routing_service.get_model_by_weight("code", complexity=0.5)
        
        # Check if active requests was incremented
        new_count = routing_service.active_requests.get(selected_model.model_id, 0)
        assert new_count > 0, \
            f"Active requests should be incremented for model {selected_model.model_id}, got {new_count}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
