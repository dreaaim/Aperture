"""Routing logic for intent detection and model selection."""

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


def classify_intent(query: str) -> str:
    """Map a query into a coarse intent bucket."""
    lowered = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    return "general"


def estimate_difficulty(intent: str) -> str:
    """Estimate task difficulty based on historical ratings."""
    logs = [log for log in store.request_logs if log.intent_tag == intent]
    if not logs:
        return "low"
    avg_rating = sum(log.user_rating or 3 for log in logs) / len(logs)
    if avg_rating < 3.4:
        return "high"
    return "medium"


def score_model(model: ModelStatus, difficulty: str) -> float:
    """Compute a weighted score for a model given difficulty."""
    history_score = store.get_model_rating(model.model_id)
    price_score = 1 / model.price_per_1k_tokens
    quota_score = model.remaining_tokens / max(1, max(m.remaining_tokens for m in MODEL_CATALOG))
    if difficulty == "high":
        difficulty_score = 1.0 if model.quality_tier == "large" else 0.0
    elif difficulty == "medium":
        difficulty_score = 1.0 if model.quality_tier in {"medium", "large"} else 0.4
    else:
        difficulty_score = 1.0

    weights = settings.router_weights
    return (
        history_score * weights.history
        + price_score * weights.price
        + quota_score * weights.quota
        + difficulty_score * weights.difficulty_match
    )


def select_model(intent: str) -> ModelStatus:
    """Select the highest scoring model for the given intent."""
    difficulty = estimate_difficulty(intent)
    scored = [(model, score_model(model, difficulty)) for model in MODEL_CATALOG]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[0][0]


def select_few_shot_model() -> ModelStatus:
    """Force a low-cost model when using few-shot cache augmentation."""
    return next(model for model in MODEL_CATALOG if model.quality_tier == "small")
