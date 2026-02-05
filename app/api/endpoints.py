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

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from typing import Literal, Tuple, AsyncGenerator
import asyncio

from app.services.container import container
from app.models import QueryRequest, QueryResponse
from app.config import settings
from app.utils.logger import default_logger
from opentelemetry import trace
from opentelemetry.trace import set_span_in_context
from app.services.fault_tolerance_service import FaultToleranceService
from app.services.routing_service import RoutingService
from app.services.background_task_service import background_task_service
from app.services.security_service import security_service

router = APIRouter()

# Get services from container
# These services are initialized in the container and injected here
repository = container.get_repository()
cache_service = container.get_cache_service()
intent_service = container.get_intent_service()
model_service = container.get_model_service()

# Initialize routing and fault tolerance services
routing_service = RoutingService(model_service)
fault_tolerance_service = FaultToleranceService(routing_service)

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

async def fake_stream_generator(text: str, chunk_size: int = 5) -> AsyncGenerator[str, None]:
    """Generate a fake streaming response for cached answers.
    
    Args:
        text: The full text to stream
        chunk_size: The size of each chunk to yield
        
    Yields:
        Chunks of the text
        
    Example:
        >>> async for chunk in fake_stream_generator("Hello world", chunk_size=3):
        ...     print(chunk)
        Hel
        lo 
        wor
        ld
    """
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        yield chunk
        await asyncio.sleep(0.02)  # Simulate typing speed
    # End of stream
    yield ""


@router.post("/v1/query")
def route_query(request: Request, payload: QueryRequest):
    """Route a query through cache, few-shot fallback, or full routing.
    
    Args:
        request: The FastAPI request object
        payload: The query request payload containing the user's query
        
    Returns:
        Either a QueryResponse object or a StreamingResponse for cache hits
        
    Raises:
        HTTPException: If a security threat is detected
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
    # Get OpenTelemetry tracer
    tracer = trace.get_tracer(__name__)
    
    # Generate a unique request ID for tracking
    request_id = repository.generate_request_id()
    # Store request_id in request state for error handling
    request.state.request_id = request_id
    
    # Log incoming request (truncate query to 50 characters for brevity)
    default_logger.info(f"Received request {request_id}: {payload.query[:50]}...")
    
    # Get current span (should be the server span created by FastAPI)
    current_span = trace.get_current_span()
    default_logger.info(f"Current span: {current_span}")
    
    # Create main span for the request processing
    # Use the current span as the parent
    with tracer.start_as_current_span("route_query", attributes={
        "request_id": request_id,
        "query": payload.query[:50],  # Truncate for span attributes
        "user_id": payload.user_id or "anonymous"
    }) as main_span:
        # Log main span
        default_logger.info(f"Main span: {main_span}")
        default_logger.info(f"Main span context: {main_span.get_span_context()}")
        try:
            # Step 0: Security scan for Prompt Injection
            with tracer.start_as_current_span("security_scan") as security_span:
                security_span.set_attribute("query_length", len(payload.query))
                # Scan prompt for security threats
                security_result = security_service.scan_prompt(payload.query)
                
                if not security_result.is_safe:
                    # Log security event
                    security_service.log_security_event(
                        payload.query,
                        security_result,
                        payload.user_id
                    )
                    # Set span attributes
                    security_span.set_attribute("security_threat_detected", True)
                    security_span.set_attribute("threat_type", security_result.threat_type)
                    security_span.set_attribute("threat_reason", security_result.reason)
                    # Return error response
                    default_logger.warning(f"Request {request_id}: Security threat detected - {security_result.reason}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Security error: {security_result.reason}"
                    )
                
                # Prompt is safe
                security_span.set_attribute("security_threat_detected", False)
                security_service.log_security_event(
                    payload.query,
                    security_result,
                    payload.user_id
                )
            
            # Step 1: Embed query for semantic cache lookup
            with tracer.start_as_current_span("embed_query") as embed_span:
                embed_span.set_attribute("query", payload.query[:50])
                # The embedding is used to find similar queries in the cache
                query_embedding = cache_service.embed_text(payload.query)
                # Find the most similar cached entry and its similarity score
                cached_entry, similarity = cache_service.find_similar(query_embedding)
                embed_span.set_attribute("similarity_score", similarity)
                embed_span.set_attribute("cache_entry_found", cached_entry is not None)

            # Initialize variables for response
            cache_status: Literal['HIT', 'FEW_SHOT', 'MISS']
            model_id: str
            answer: str
            tokens_used: int

            # Step 2: Determine routing path based on cache similarity
            with tracer.start_as_current_span("determine_routing") as routing_span:
                routing_span.set_attribute("similarity_score", similarity)
                routing_span.set_attribute("direct_hit_threshold", settings.cache_thresholds.direct_hit)
                routing_span.set_attribute("few_shot_threshold", settings.cache_thresholds.few_shot)
                
                if cached_entry and similarity >= settings.cache_thresholds.direct_hit:
                    # High similarity (>= direct_hit threshold) -> direct cache return
                    # This means we found a very similar query in the cache
                    cache_status = "HIT"
                    model_id = cached_entry.model_id
                    answer = cached_entry.answer
                    tokens_used = 0  # No tokens used for cache hits
                    routing_span.set_attribute("cache_status", cache_status)
                    routing_span.set_attribute("model_id", model_id)
                    default_logger.info(f"Request {request_id}: Cache HIT with similarity {similarity:.2f}")
                elif cached_entry and similarity >= settings.cache_thresholds.few_shot:
                    # Medium similarity (>= few_shot threshold) -> few-shot augmentation
                    # Use a small model with cached context to generate a response
                    cache_status = "FEW_SHOT"
                    try:
                        # Select a small model for few-shot learning with failover
                        model = fault_tolerance_service.get_model_with_failover("few_shot")
                        model_id = model.model_id
                        # Create context from cached entry
                        context = f"历史问题: {cached_entry.query}\n历史答案: {cached_entry.answer}"
                        # Generate response with context using fault tolerance
                        def generate_with_context():
                            return generate_response(payload.query, model_id, context=context)
                        answer, tokens_used = fault_tolerance_service.execute_with_retry(
                            generate_with_context, model
                        )
                        routing_span.set_attribute("cache_status", cache_status)
                        routing_span.set_attribute("model_id", model_id)
                        routing_span.set_attribute("tokens_used", tokens_used)
                        default_logger.info(f"Request {request_id}: Cache FEW_SHOT with similarity {similarity:.2f}, using model {model_id}")
                    except Exception as e:
                        # Fallback to default model if all fail
                        routing_span.set_attribute("error", str(e)[:100])
                        default_logger.error(f"Request {request_id}: FEW_SHOT model selection failed, using fallback: {e}")
                        model = model_service.select_few_shot_model()
                        model_id = model.model_id
                        context = f"历史问题: {cached_entry.query}\n历史答案: {cached_entry.answer}"
                        answer, tokens_used = generate_response(payload.query, model_id, context=context)
                else:
                    # Low similarity (< few_shot threshold) -> full routing
                    # Classify intent and select an appropriate model
                    cache_status = "MISS"
                    try:
                        # Classify the intent of the query
                        intent = intent_service.classify_intent(payload.query)
                        # Select a model based on the classified intent with failover
                        model = fault_tolerance_service.get_model_with_failover(intent)
                        model_id = model.model_id
                        # Generate response without context using fault tolerance
                        def generate_without_context():
                            return generate_response(payload.query, model_id)
                        answer, tokens_used = fault_tolerance_service.execute_with_retry(
                            generate_without_context, model
                        )
                        routing_span.set_attribute("cache_status", cache_status)
                        routing_span.set_attribute("intent", intent)
                        routing_span.set_attribute("model_id", model_id)
                        routing_span.set_attribute("tokens_used", tokens_used)
                        default_logger.info(f"Request {request_id}: Cache MISS, classified as {intent}, using model {model_id}")
                    except Exception as e:
                        # Fallback to default model if all fail
                        routing_span.set_attribute("error", str(e)[:100])
                        default_logger.error(f"Request {request_id}: Model selection failed, using fallback: {e}")
                        intent = intent_service.classify_intent(payload.query)
                        model = model_service.select_model(intent)
                        model_id = model.model_id
                        answer, tokens_used = generate_response(payload.query, model_id)
                        routing_span.set_attribute("cache_status", cache_status)
                        routing_span.set_attribute("intent", intent)
                        routing_span.set_attribute("model_id", model_id)
                        routing_span.set_attribute("tokens_used", tokens_used)

            # Step 3: Log the request for future difficulty estimation
            with tracer.start_as_current_span("log_request") as log_span:
                log_span.set_attribute("request_id", request_id)
                # Re-classify intent for logging (ensuring consistency)
                intent_tag = intent_service.classify_intent(payload.query)
                
                # Add request log to repository (synchronous, minimal data)
                repository.add_request_log(
                    request_id=request_id,
                    query=payload.query,
                    query_embedding=[0.0],  # Empty embedding for now
                    intent_tag=intent_tag,
                    router_decision=model_id,
                    response_content=answer,
                    cache_status=cache_status,
                    tokens_used=tokens_used,
                )
                log_span.set_attribute("intent_tag", intent_tag)
                
                # Queue background task for embedding computation and log update
                background_task_service.queue_embedding_task(
                    request_id=request_id,
                    query=payload.query
                )
                log_span.set_attribute("embedding_task_queued", True)

            # Step 4: Cache non-hit responses for future use
            if cache_status != "HIT":
                with tracer.start_as_current_span("cache_response") as cache_span:
                    cache_span.set_attribute("cache_status", cache_status)
                    cache_span.set_attribute("model_id", model_id)
                    # Queue background task for cache update
                    background_task_service.queue_cache_update_task(
                        query=payload.query,
                        answer=answer,
                        model_id=model_id
                    )
                    cache_span.set_attribute("cache_update_task_queued", True)
                    default_logger.info(f"Request {request_id}: Queued cache update task for future use")

            # Step 5: Log response details
            default_logger.info(f"Request {request_id}: Completed with model {model_id}, tokens used: {tokens_used}")
            
            # Set main span attributes
            main_span.set_attribute("cache_status", cache_status)
            main_span.set_attribute("model_id", model_id)
            main_span.set_attribute("tokens_used", tokens_used)

            # Step 6: Return the response
            if cache_status == "HIT":
                # For cache hits, return a streaming response to simulate real model behavior
                async def stream_response() -> AsyncGenerator[str, None]:
                    # First yield the response metadata as a JSON object
                    import json
                    metadata = {
                        "request_id": request_id,
                        "model_id": model_id,
                        "cache_status": cache_status,
                        "streaming": True
                    }
                    yield json.dumps(metadata) + "\n"
                    
                    # Then stream the answer in chunks
                    async for chunk in fake_stream_generator(answer):
                        if chunk:
                            chunk_data = {
                                "chunk": chunk,
                                "finish_reason": None
                            }
                            yield json.dumps(chunk_data) + "\n"
                    
                    # Finally yield the finish message
                    finish_data = {
                        "chunk": "",
                        "finish_reason": "stop"
                    }
                    yield json.dumps(finish_data) + "\n"
                
                return StreamingResponse(
                    stream_response(),
                    media_type="application/x-ndjson"
                )
            else:
                # For non-cache hits, return the regular JSON response
                return QueryResponse(
                    request_id=request_id,
                    answer=answer,
                    model_id=model_id,
                    cache_status=cache_status,
                )
        except Exception as e:
            # Log any errors that occur during processing
            default_logger.error(f"Request {request_id}: Error processing request: {str(e)}")
            # Set error attribute on span
            main_span.set_attribute("error", True)
            main_span.set_attribute("error_message", str(e))
            # Re-raise the exception to be handled by the global error handler
            raise
