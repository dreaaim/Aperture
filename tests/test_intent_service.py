"""Unit tests for intent classification service.

This module contains unit tests for the IntentService class, testing:
- Code intent classification
- Chat intent classification
- Reasoning intent classification
- Creative intent classification
- General intent classification

The tests verify that the intent service correctly classifies different types of queries
into their respective intent categories based on keyword matching.
"""

from app.services.intent_service import IntentService


def test_classify_intent_code() -> None:
    """Test code intent classification.
    
    This test verifies that queries related to coding are correctly
    classified as "code" intent.
    
    Test steps:
    1. Create an IntentService instance
    2. Test with a code-related query
    3. Verify the intent is classified as "code"
    """
    # Create IntentService instance
    service = IntentService()
    
    # Test query with code-related content
    query = "帮我写个Python脚本"
    
    # Classify intent
    intent = service.classify_intent(query)
    
    # Verify intent classification
    assert intent == "code"


def test_classify_intent_chat() -> None:
    """Test chat intent classification.
    
    This test verifies that queries related to chat/conversation are correctly
    classified as "chat" intent.
    
    Test steps:
    1. Create an IntentService instance
    2. Test with a chat-related query
    3. Verify the intent is classified as "chat"
    """
    # Create IntentService instance
    service = IntentService()
    
    # Test query with chat-related content
    query = "今天天气怎么样"
    
    # Classify intent
    intent = service.classify_intent(query)
    
    # Verify intent classification
    assert intent == "chat"


def test_classify_intent_reasoning() -> None:
    """Test reasoning intent classification.
    
    This test verifies that queries related to reasoning/analysis are correctly
    classified as "reasoning" intent.
    
    Test steps:
    1. Create an IntentService instance
    2. Test with a reasoning-related query
    3. Verify the intent is classified as "reasoning"
    """
    # Create IntentService instance
    service = IntentService()
    
    # Test query with reasoning-related content
    query = "为什么天空是蓝色的"
    
    # Classify intent
    intent = service.classify_intent(query)
    
    # Verify intent classification
    assert intent == "reasoning"


def test_classify_intent_creative() -> None:
    """Test creative intent classification.
    
    This test verifies that queries related to creative content are correctly
    classified as "creative" intent.
    
    Test steps:
    1. Create an IntentService instance
    2. Test with a creative-related query
    3. Verify the intent is classified as "creative"
    """
    # Create IntentService instance
    service = IntentService()
    
    # Test query with creative-related content
    query = "帮我写个营销文案"
    
    # Classify intent
    intent = service.classify_intent(query)
    
    # Verify intent classification
    assert intent == "creative"


def test_classify_intent_general() -> None:
    """Test general intent classification.
    
    This test verifies that queries with no specific intent are correctly
    classified as "general" intent.
    
    Test steps:
    1. Create an IntentService instance
    2. Test with a general query
    3. Verify the intent is classified as "general"
    """
    # Create IntentService instance
    service = IntentService()
    
    # Test query with general content
    query = "这是一个普通的问题"
    
    # Classify intent
    intent = service.classify_intent(query)
    
    # Verify intent classification
    assert intent == "general"
