"""Routing logic for intent detection and model selection.

This module provides the core routing functionality for the LLM router, including:
- Intent classification based on keyword matching
- Model selection based on weighted scoring
- Difficulty estimation for tasks
- Model catalog management

The routing system uses a combination of intent detection and model scoring
to select the most appropriate model for each user query.
"""

from app.config import settings
from app.models import ModelStatus
from app.storage import store


INTENT_KEYWORDS = {
    # Keyword-based intent tagging for the prototype.
    "code": ["代码", "python", "java", "algorithm", "bug", "脚本"],
    "chat": ["天气", "你好", "闲聊", "心情", "笑话"],
    "reasoning": ["证明", "推理", "分析", "原因", "为什么"],
    "creative": ["写作", "故事", "创意", "营销", "文案"],
}
"""Keyword-based intent mapping.

This dictionary maps intent categories to lists of keywords used for
intent classification. When a query contains any of the keywords
for a category, it's classified as that intent.
"""


MODEL_CATALOG = [
    # Demo model catalog with pricing and quota metadata.
    ModelStatus(
        model_id="gpt-4o",
        price_per_1k_tokens=5.0,
        remaining_tokens=400000,
        quality_tier="large",
    ),
    ModelStatus(
        model_id="claude-3.5-sonnet",
        price_per_1k_tokens=3.5,
        remaining_tokens=300000,
        quality_tier="large",
    ),
    ModelStatus(
        model_id="gpt-4o-mini",
        price_per_1k_tokens=0.8,
        remaining_tokens=600000,
        quality_tier="medium",
    ),
    ModelStatus(
        model_id="llama-3-8b",
        price_per_1k_tokens=0.2,
        remaining_tokens=1000000,
        quality_tier="small",
    ),
]
"""Model catalog with pricing and quota metadata.

This list contains ModelStatus objects for all available models,
including their pricing, remaining quota, and quality tier.
"""


def classify_intent(query: str) -> str:
    """Classify a query into an intent category based on keywords.
    
    This function uses keyword matching to classify the intent of a user query.
    It checks if the query contains any keywords from the INTENT_KEYWORDS dictionary.
    
    Args:
        query: User query text to classify
        
    Returns:
        str: Intent category (code, chat, reasoning, creative, or general)
        
    Example:
        >>> classify_intent("如何用Python编写一个排序算法？")
        "code"
        >>> classify_intent("今天天气怎么样？")
        "chat"
        >>> classify_intent("什么是量子计算？")
        "general"
    """
    # Convert query to lowercase for case-insensitive matching
    lowered = query.lower()
    
    # Check each intent category for matching keywords
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    
    # Default to general intent if no keywords match
    return "general"


def estimate_difficulty(intent: str) -> str:
    """Estimate task difficulty based on historical ratings.
    
    This function estimates the difficulty of a task based on
    historical user ratings for the given intent category.
    
    Args:
        intent: Intent category to estimate difficulty for
        
    Returns:
        str: Difficulty level (low, medium, or high)
        
    Example:
        >>> estimate_difficulty("code")
        "medium"
        >>> estimate_difficulty("chat")
        "low"
    """
    # Get all request logs for the given intent
    logs = [log for log in store.request_logs if log.intent_tag == intent]
    
    # Default to low difficulty if no historical data
    if not logs:
        return "low"
    
    # Calculate average user rating (default to 3 if no rating)
    avg_rating = sum(log.user_rating or 3 for log in logs) / len(logs)
    
    # Determine difficulty based on average rating
    if avg_rating < 3.4:
        return "high"  # Lower ratings indicate higher difficulty
    return "medium"


def score_model(model: ModelStatus, difficulty: str) -> float:
    """Compute a weighted score for a model given task difficulty.
    
    This function calculates a composite score for a model based on multiple factors:
    - Historical performance (user ratings)
    - Price (inverse of cost per token)
    - Remaining quota
    - Match between model capability and task difficulty
    
    Args:
        model: ModelStatus object to score
        difficulty: Task difficulty level (low, medium, or high)
        
    Returns:
        float: Weighted score for the model
        
    Example:
        >>> model = MODEL_CATALOG[0]  # gpt-4o
        >>> score_model(model, "high")
        0.85  # Example score
    """
    # Get historical rating for the model
    history_score = store.get_model_rating(model.model_id)
    
    # Calculate price score (inverse of price, so lower price = higher score)
    price_score = 1 / model.price_per_1k_tokens
    
    # Calculate quota score (normalized to 0-1 range)
    max_quota = max(m.remaining_tokens for m in MODEL_CATALOG) if MODEL_CATALOG else 1
    quota_score = model.remaining_tokens / max_quota
    
    # Calculate difficulty match score based on model quality tier
    if difficulty == "high":
        # High difficulty tasks require large models
        difficulty_score = 1.0 if model.quality_tier == "large" else 0.0
    elif difficulty == "medium":
        # Medium difficulty tasks can use medium or large models
        difficulty_score = 1.0 if model.quality_tier in {"medium", "large"} else 0.4
    else:
        # Low difficulty tasks can use any model
        difficulty_score = 1.0

    # Get routing weights from settings
    weights = settings.router_weights
    
    # Calculate weighted sum
    return (
        history_score * weights.history
        + price_score * weights.price
        + quota_score * weights.quota
        + difficulty_score * weights.difficulty_match
    )


def select_model(intent: str) -> ModelStatus:
    """Select the highest scoring model for the given intent.
    
    This function estimates the difficulty of the task based on the intent,
    scores all available models, and returns the highest scoring one.
    
    Args:
        intent: Intent category to select a model for
        
    Returns:
        ModelStatus: Highest scoring model for the given intent
        
    Example:
        >>> select_model("code")
        ModelStatus(model_id="gpt-4o", ...)  # Example result
    """
    # Estimate task difficulty
    difficulty = estimate_difficulty(intent)
    
    # Score all models
    scored = [(model, score_model(model, difficulty)) for model in MODEL_CATALOG]
    
    # Sort models by score in descending order
    scored.sort(key=lambda item: item[1], reverse=True)
    
    # Return the highest scoring model
    return scored[0][0]


def select_few_shot_model() -> ModelStatus:
    """Select a low-cost model for few-shot learning.
    
    This function returns the smallest/cheapest model available
    for use in few-shot learning scenarios.
    
    Returns:
        ModelStatus: Low-cost model for few-shot learning
        
    Example:
        >>> select_few_shot_model()
        ModelStatus(model_id="llama-3-8b", ...)  # Example result
    """
    # Return the first small-tier model found
    return next(model for model in MODEL_CATALOG if model.quality_tier == "small")
