"""Unit tests for model management and selection service."""

from app.services.model_service import ModelService
from app.repositories.memory_repository import MemoryRepository


def test_select_model() -> None:
    """Test model selection based on intent."""
    repository = MemoryRepository()
    service = ModelService(repository)
    
    # Test code intent
    model = service.select_model("code")
    assert model is not None
    assert model.model_id in ["gpt-4o", "claude-3.5-sonnet", "gpt-4o-mini", "llama-3-8b"]
    
    # Test chat intent
    model = service.select_model("chat")
    assert model is not None
    assert model.model_id in ["gpt-4o", "claude-3.5-sonnet", "gpt-4o-mini", "llama-3-8b"]


def test_select_few_shot_model() -> None:
    """Test few-shot model selection always returns small model."""
    repository = MemoryRepository()
    service = ModelService(repository)
    
    model = service.select_few_shot_model()
    assert model is not None
    assert model.quality_tier == "small"
    assert model.model_id == "llama-3-8b"


def test_estimate_difficulty() -> None:
    """Test difficulty estimation based on intent."""
    repository = MemoryRepository()
    service = ModelService(repository)
    
    # Test with no history
    difficulty = service.estimate_difficulty("code")
    assert difficulty == "low"
