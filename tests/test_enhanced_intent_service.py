"""Unit tests for enhanced intent classification service.

This module contains unit tests for the EnhancedIntentService class, testing:
- Code intent classification
- Chat intent classification
- Reasoning intent classification
- Creative intent classification
- General intent classification

The tests verify that the enhanced intent service correctly classifies different types of queries
into their respective intent categories using the hybrid approach.
"""

from app.services.enhanced_intent_service import EnhancedIntentService

def test_enhanced_intent_service_code():
    """Test code intent classification with enhanced service."""
    service = EnhancedIntentService()
    query = "帮我写个Python脚本"
    result = service.classify_intent(query)
    assert result['intent'] == "code"
    assert result['confidence'] > 0.0

def test_enhanced_intent_service_chat():
    """Test chat intent classification with enhanced service."""
    service = EnhancedIntentService()
    query = "今天天气怎么样"
    result = service.classify_intent(query)
    assert result['intent'] == "chat"
    assert result['confidence'] > 0.0

def test_enhanced_intent_service_reasoning():
    """Test reasoning intent classification with enhanced service."""
    service = EnhancedIntentService()
    query = "为什么天空是蓝色的"
    result = service.classify_intent(query)
    assert result['intent'] == "reasoning"
    assert result['confidence'] > 0.0

def test_enhanced_intent_service_creative():
    """Test creative intent classification with enhanced service."""
    service = EnhancedIntentService()
    query = "帮我写个营销文案"
    result = service.classify_intent(query)
    assert result['intent'] == "creative"
    assert result['confidence'] > 0.0

def test_enhanced_intent_service_general():
    """Test general intent classification with enhanced service."""
    service = EnhancedIntentService()
    query = "这是一个普通的问题"
    result = service.classify_intent(query)
    assert result['intent'] == "general"
    assert result['confidence'] > 0.0
