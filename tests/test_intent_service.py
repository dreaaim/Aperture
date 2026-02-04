"""Unit tests for intent classification service."""

from app.services.intent_service import IntentService


def test_classify_intent_code() -> None:
    """Test code intent classification."""
    service = IntentService()
    query = "帮我写个Python脚本"
    intent = service.classify_intent(query)
    assert intent == "code"


def test_classify_intent_chat() -> None:
    """Test chat intent classification."""
    service = IntentService()
    query = "今天天气怎么样"
    intent = service.classify_intent(query)
    assert intent == "chat"


def test_classify_intent_reasoning() -> None:
    """Test reasoning intent classification."""
    service = IntentService()
    query = "为什么天空是蓝色的"
    intent = service.classify_intent(query)
    assert intent == "reasoning"


def test_classify_intent_creative() -> None:
    """Test creative intent classification."""
    service = IntentService()
    query = "帮我写个营销文案"
    intent = service.classify_intent(query)
    assert intent == "creative"


def test_classify_intent_general() -> None:
    """Test general intent classification."""
    service = IntentService()
    query = "这是一个普通的问题"
    intent = service.classify_intent(query)
    assert intent == "general"
