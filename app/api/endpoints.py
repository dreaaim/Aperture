"""API endpoints for the LLM gateway.

This module contains the API endpoints for the LLM gateway, including:
- `/v1/query` endpoint for processing user queries
- Request routing through cache, few-shot fallback, or full routing
- Response generation and logging

Example:
    POST /v1/query
    {
        "query": "帮我写个Python脚本",
        "user_id": "user123"
    }

    Response:
    {
        "request_id": "uuid",
        "answer": "[gpt-4o] 帮我写个Python脚本",
        "model_id": "gpt-4o",
        "cache_status": "MISS"
    }
"""

from fastapi import APIRouter, Request
from typing import Literal, Tuple

from app.services.container import container
from app.models import QueryRequest, QueryResponse
from app.config import settings
from app.utils.logger import default_logger

router = APIRouter()

# Get services from container
# These services are initialized in the container and injected here
repository = container.get_repository()
cache_service = container.get_cache_service()
intent_service = container.get_intent_service()
model_service = container.get_model_service()

def generate_response(query: str, model_id: str, context: str | None = None) -> Tuple[str, int]:
    """Generate a stubbed answer and estimate token usage.
    
    Args:
        query: The user's query string
        model_id: The ID of the model used to generate the response
        context: Optional context to include in the response
        
    Returns:
        A tuple containing:
        - answer: The generated answer string
        - token_estimate: An estimate of the number of tokens used
        
    Example:
        >>> generate_response("你好", "gpt-4o")
        ("[gpt-4o] 你好", 1)
        
        >>> generate_response("你好", "gpt-4o", "历史问题: 今天天气怎么样\n历史答案: 今天天气很好")
        ("[gpt-4o] 历史问题: 今天天气怎么样\n历史答案: 今天天气很好 你好", 1)
    """
    # Generate a formatted answer with model ID and optional context
    answer = f"[{model_id}] {context or ''} {query}".strip()
    # Estimate token usage based on query length
    # This is a simple estimate - in a real implementation, you would use a tokenizer
    token_estimate = max(1, len(query) // 4)
    return answer, token_estimate


@router.post("/v1/query", response_model=QueryResponse)
def route_query(request: Request, payload: QueryRequest) -> QueryResponse:
    """Route a query through cache, few-shot fallback, or full routing.
    
    Args:
        request: The FastAPI request object
        payload: The query request payload containing the user's query
        
    Returns:
        A QueryResponse object containing:
        - request_id: A unique ID for the request
        - answer: The generated answer
        - model_id: The ID of the model used
        - cache_status: The cache status (HIT, FEW_SHOT, or MISS)
        
    Raises:
        Exception: If an error occurs during processing
        
    Example:
        # Request with a query that will be routed through the full routing path
        POST /v1/query
        {
            "query": "帮我写个Python脚本"
        }
        
        # Response
        {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "answer": "[gpt-4o] 帮我写个Python脚本",
            "model_id": "gpt-4o",
            "cache_status": "MISS"
        }
    """
    # Generate a unique request ID for tracking
    request_id = repository.generate_request_id()
    # Store request_id in request state for error handling
    request.state.request_id = request_id
    
    # Log incoming request (truncate query to 50 characters for brevity)
    default_logger.info(f"Received request {request_id}: {payload.query[:50]}...")
    
    try:
        # Step 1: Embed query for semantic cache lookup
        # The embedding is used to find similar queries in the cache
        query_embedding = cache_service.embed_text(payload.query)
        # Find the most similar cached entry and its similarity score
        cached_entry, similarity = cache_service.find_similar(query_embedding)

        # Initialize variables for response
        cache_status: Literal['HIT', 'FEW_SHOT', 'MISS']
        model_id: str
        answer: str
        tokens_used: int

        # Step 2: Determine routing path based on cache similarity
        if cached_entry and similarity >= settings.cache_thresholds.direct_hit:
            # High similarity (>= direct_hit threshold) -> direct cache return
            # This means we found a very similar query in the cache
            cache_status = "HIT"
            model_id = cached_entry.model_id
            answer = cached_entry.answer
            tokens_used = 0  # No tokens used for cache hits
            default_logger.info(f"Request {request_id}: Cache HIT with similarity {similarity:.2f}")
        elif cached_entry and similarity >= settings.cache_thresholds.few_shot:
            # Medium similarity (>= few_shot threshold) -> few-shot augmentation
            # Use a small model with cached context to generate a response
            cache_status = "FEW_SHOT"
            # Select a small model for few-shot learning
            model = model_service.select_few_shot_model()
            model_id = model.model_id
            # Create context from cached entry
            context = f"历史问题: {cached_entry.query}\n历史答案: {cached_entry.answer}"
            # Generate response with context
            answer, tokens_used = generate_response(payload.query, model_id, context=context)
            default_logger.info(f"Request {request_id}: Cache FEW_SHOT with similarity {similarity:.2f}, using model {model_id}")
        else:
            # Low similarity (< few_shot threshold) -> full routing
            # Classify intent and select an appropriate model
            cache_status = "MISS"
            # Classify the intent of the query
            intent = intent_service.classify_intent(payload.query)
            # Select a model based on the classified intent
            model = model_service.select_model(intent)
            model_id = model.model_id
            # Generate response without context
            answer, tokens_used = generate_response(payload.query, model_id)
            default_logger.info(f"Request {request_id}: Cache MISS, classified as {intent}, using model {model_id}")

        # Step 3: Log the request for future difficulty estimation
        # Re-classify intent for logging (ensuring consistency)
        intent_tag = intent_service.classify_intent(payload.query)
        # Add request log to repository
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

        # Step 4: Cache non-hit responses for future use
        if cache_status != "HIT":
            # Only cache non-hit responses to avoid duplicating stored entries
            cache_service.upsert_cache(payload.query, query_embedding, answer, model_id)
            default_logger.info(f"Request {request_id}: Cached response for future use")

        # Step 5: Log response details
        default_logger.info(f"Request {request_id}: Completed with model {model_id}, tokens used: {tokens_used}")

        # Step 6: Return the response
        return QueryResponse(
            request_id=request_id,
            answer=answer,
            model_id=model_id,
            cache_status=cache_status,
        )
    except Exception as e:
        # Log any errors that occur during processing
        default_logger.error(f"Request {request_id}: Error processing request: {str(e)}")
        # Re-raise the exception to be handled by the global error handler
        raise
