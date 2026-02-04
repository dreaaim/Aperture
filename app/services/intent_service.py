"""Intent classification service."""

from app.config import settings


class IntentService:
    """Service for classifying user intent from queries."""

    def __init__(self):
        """Initialize the intent service with settings."""
        self.intent_keywords = settings.intent_keywords

    def classify_intent(self, query: str) -> str:
        """Map a query into a coarse intent bucket."""
        lowered = query.lower()
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                return intent
        return "general"
