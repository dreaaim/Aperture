"""FastAPI entrypoint implementing the LLM gateway routing flow."""

from fastapi import FastAPI

from app.cache import embed_text, find_similar, upsert_cache
from app.config import settings
from app.models import QueryRequest, QueryResponse, RequestLog
from app.router import classify_intent, select_few_shot_model, select_model
from app.storage import store

app = FastAPI(title="Aperture LLM Router")


def generate_response(query: str, model_id: str, context: str | None = None) -> tuple[str, int]:
    """Generate a stubbed answer and estimate token usage."""
    answer = f"[{model_id}] {context or ''} {query}".strip()
    token_estimate = max(1, len(query) // 4)
    return answer, token_estimate


@app.post("/v1/query", response_model=QueryResponse)
def route_query(payload: QueryRequest) -> QueryResponse:
    """Route a query through cache, few-shot fallback, or full routing."""
    request_id = store.generate_request_id()
    # Embed query for semantic cache lookup.
    query_embedding = embed_text(payload.query)
    cached_entry, similarity = find_similar(query_embedding)

    if cached_entry and similarity >= settings.cache_thresholds.direct_hit:
        # High similarity -> direct cache return.
        cache_status = "HIT"
        model_id = cached_entry.model_id
        answer = cached_entry.answer
        tokens_used = 0
    elif cached_entry and similarity >= settings.cache_thresholds.few_shot:
        # Mid similarity -> few-shot augmentation with a small model.
        cache_status = "FEW_SHOT"
        model = select_few_shot_model()
        model_id = model.model_id
        context = f"历史问题: {cached_entry.query}\n历史答案: {cached_entry.answer}"
        answer, tokens_used = generate_response(payload.query, model_id, context=context)
    else:
        # Cache miss -> full routing based on intent and difficulty.
        cache_status = "MISS"
        intent = classify_intent(payload.query)
        model = select_model(intent)
        model_id = model.model_id
        answer, tokens_used = generate_response(payload.query, model_id)

    # Always log the request for future difficulty estimation.
    intent_tag = classify_intent(payload.query)
    store.add_request_log(
        RequestLog(
            request_id=request_id,
            query=payload.query,
            query_embedding=query_embedding,
            intent_tag=intent_tag,
            router_decision=model_id,
            response_content=answer,
            cache_status=cache_status,
            tokens_used=tokens_used,
        )
    )

    if cache_status != "HIT":
        # Only cache non-hit responses to avoid duplicating stored entries.
        upsert_cache(payload.query, query_embedding, answer, model_id)

    return QueryResponse(
        request_id=request_id,
        answer=answer,
        model_id=model_id,
        cache_status=cache_status,
    )
