"""Unit tests for model management and selection service.

This module contains unit tests for the ModelService class, testing:
- Model selection based on intent
- Few-shot model selection
- Difficulty estimation based on intent

The tests verify that the model service correctly selects appropriate models
based on intent and difficulty, and that few-shot scenarios use the small model.
"""

from app.services.model_service import ModelService
from app.repositories.memory_repository import MemoryRepository


def test_select_model() -> None:
    """Test model selection based on intent.
    
    This test verifies that the select_model method correctly returns
    a valid model for different intent categories.
    
    Test steps:
    1. Create a MemoryRepository instance
    2. Create a ModelService instance with the repository
    3. Test model selection for code intent
    4. Test model selection for chat intent
    5. Verify valid models are returned
    """
    # Create repository and service instances
    repository = MemoryRepository()
    service = ModelService(repository)
    
    # Test code intent model selection
    model = service.select_model("code")
    assert model is not None
    assert model.model_id in ["gpt-4o", "claude-3.5-sonnet", "gpt-4o-mini", "llama-3-8b"]
    
    # Test chat intent model selection
    model = service.select_model("chat")
    assert model is not None
    assert model.model_id in ["gpt-4o", "claude-3.5-sonnet", "gpt-4o-mini", "llama-3-8b"]


def test_select_few_shot_model() -> None:
    """Test few-shot model selection always returns small model.
    
    This test verifies that the select_few_shot_model method always
    returns the small model (llama-3-8b) for few-shot scenarios.
    
    Test steps:
    1. Create a MemoryRepository instance
    2. Create a ModelService instance with the repository
    3. Get few-shot model
    4. Verify small model is returned
    """
    # Create repository and service instances
    repository = MemoryRepository()
    service = ModelService(repository)
    
    # Get few-shot model
    model = service.select_few_shot_model()
    
    # Verify small model is returned
    assert model is not None
    assert model.quality_tier == "small"
    assert model.model_id == "llama-3-8b"


def test_estimate_difficulty() -> None:
    """Test difficulty estimation based on intent.
    
    This test verifies that the estimate_difficulty method correctly
    estimates difficulty based on intent, returning "low" for new intents
    with no historical data.
    
    Test steps:
    1. Create a MemoryRepository instance
    2. Create a ModelService instance with the repository
    3. Estimate difficulty for code intent (no history)
    4. Verify difficulty is "low"
    """
    # Create repository and service instances
    repository = MemoryRepository()
    service = ModelService(repository)
    
    # Test with no history (new intent)
    difficulty = service.estimate_difficulty("code")
    assert difficulty == "low"
