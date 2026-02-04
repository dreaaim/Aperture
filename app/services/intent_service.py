"""Intent classification service.

This module provides a service for classifying user intent from queries based on keyword matching.

The IntentService class uses a keyword-based approach to classify user queries into different intent categories:
- code: Queries related to programming and code
- chat: Queries related to casual conversation
- reasoning: Queries that require reasoning or analysis
- creative: Queries related to creative writing or content creation
- general: Queries that don't fit into any specific category

Example:
    from app.services.intent_service import IntentService
    
    service = IntentService()
    intent = service.classify_intent("帮我写个Python脚本")
    print(intent)  # Output: "code"
"""

from app.config import settings


class IntentService:
    """Service for classifying user intent from queries.
    
    This service uses keyword matching to classify user queries into different intent categories.
    The intent categories and their associated keywords are defined in the application settings.
    
    Attributes:
        intent_keywords: A dictionary mapping intent categories to lists of keywords
    """

    def __init__(self):
        """Initialize the intent service with settings.
        
        The service is initialized with the intent keywords from the application settings.
        These keywords are used to classify user queries into different intent categories.
        """
        # Load intent keywords from settings
        # This allows for easy configuration of intent categories and keywords
        self.intent_keywords = settings.intent_keywords

    def classify_intent(self, query: str) -> str:
        """Classify a user query into an intent category.
        
        Args:
            query: The user's query string
            
        Returns:
            The classified intent category as a string
            Possible values: "code", "chat", "reasoning", "creative", "general"
            
        Example:
            >>> service = IntentService()
            >>> service.classify_intent("帮我写个Python脚本")
            "code"
            
            >>> service.classify_intent("今天天气怎么样")
            "chat"
            
            >>> service.classify_intent("为什么天空是蓝色的")
            "reasoning"
            
            >>> service.classify_intent("帮我写个营销文案")
            "creative"
            
            >>> service.classify_intent("这是一个普通的问题")
            "general"
        """
        # Convert query to lowercase for case-insensitive matching
        lowered = query.lower()
        
        # Iterate through each intent category and its keywords
        for intent, keywords in self.intent_keywords.items():
            # Check if any keyword from the current intent is present in the query
            if any(keyword in lowered for keyword in keywords):
                # Return the first matching intent
                return intent
        
        # If no keywords match, return "general" intent
        return "general"
