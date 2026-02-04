"""API endpoints for the LLM gateway."""

from fastapi import APIRouter, Request

from app.services.container import container
from app.models import QueryRequest, QueryResponse
from app.config import settings
from app.utils.logger import default_logger

router = APIRouter()

# Get services from container
repository = container.get_repository()
cache_service = container.get_cache_service()
intent_service = container.get_intent_service()
model_service = container.get_model_service()

def generate_response(query: str, model_id: str, context: str | None = None) -> tuple[str, int]:
    """Generate a stubbed answer and estimate token usage."""
    answer = f"[{model_id}] {context or ''} {query}".strip()
    token_estimate = max(1, len(query) // 4)
    return answer, token_estimate


@router.post("/v1/query", response_model=QueryResponse)
def route_query(request: Request, payload: QueryRequest) -> QueryResponse:
    """Route a query through cache, few-shot fallback, or full routing."""
    from typing import Literal
    request_id = repository.generate_request_id()
    # Store request_id in request state for error handling
    request.state.request_id = request_id
    
    # Log incoming request
    default_logger.info(f"Received request {request_id}: {payload.query[:50]}...")
    
    try:
        # Embed query for semantic cache lookup.
        query_embedding = cache_service.embed_text(payload.query)
        cached_entry, similarity = cache_service.find_similar(query_embedding)

        # Initialize variables
        cache_status: Literal['HIT', 'FEW_SHOT', 'MISS']
        model_id: str
        answer: str
        tokens_used: int

        if cached_entry and similarity >= settings.cache_thresholds.direct_hit:
            # High similarity -> direct cache return.
            cache_status = "HIT"
            model_id = cached_entry.model_id
            answer = cached_entry.answer
            tokens_used = 0
            default_logger.info(f"Request {request_id}: Cache HIT with similarity {similarity:.2f}")
        elif cached_entry and similarity >= settings.cache_thresholds.few_shot:
            # Mid similarity -> few-shot augmentation with a small model.
            cache_status = "FEW_SHOT"
            model = model_service.select_few_shot_model()
            model_id = model.model_id
            context = f"历史问题: {cached_entry.query}\n历史答案: {cached_entry.answer}"
            answer, tokens_used = generate_response(payload.query, model_id, context=context)
            default_logger.info(f"Request {request_id}: Cache FEW_SHOT with similarity {similarity:.2f}, using model {model_id}")
        else:
            # Cache miss -> full routing based on intent and difficulty.
            cache_status = "MISS"
            intent = intent_service.classify_intent(payload.query)
            model = model_service.select_model(intent)
            model_id = model.model_id
            answer, tokens_used = generate_response(payload.query, model_id)
            default_logger.info(f"Request {request_id}: Cache MISS, classified as {intent}, using model {model_id}")

        # Always log the request for future difficulty estimation.
        intent_tag = intent_service.classify_intent(payload.query)
        repository.add_request_log(
            request_id=request_id,
            query=payload.query,
            query_embedding=query_embedding,
            intent_tag=intent_tag,
            router_decision=model_id,
            response_content=answer,
            cache_status=cache_status,
            tokens_used=tokens_used,
        )

        if cache_status != "HIT":
            # Only cache non-hit responses to avoid duplicating stored entries.
            cache_service.upsert_cache(payload.query, query_embedding, answer, model_id)
            default_logger.info(f"Request {request_id}: Cached response for future use")

        # Log response
        default_logger.info(f"Request {request_id}: Completed with model {model_id}, tokens used: {tokens_used}")

        return QueryResponse(
            request_id=request_id,
            answer=answer,
            model_id=model_id,
            cache_status=cache_status,
        )
    except Exception as e:
        # Log error
        default_logger.error(f"Request {request_id}: Error processing request: {str(e)}")
        raise
