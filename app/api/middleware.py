"""API middleware for error handling and logging.

This module contains middleware functions for the FastAPI application, including:
- `error_handler`: Global exception handler for catching and logging errors
- Error response formatting with consistent structure
- Request ID tracking for error correlation

Example:
    # In main.py
    from app.api.middleware import error_handler
    
    app = FastAPI()
    app.middleware("http")(error_handler)

    # When an exception occurs in a route handler
    # The middleware will catch it and return:
    # {
    #     "error": "Internal Server Error",
    #     "message": "Error details",
    #     "request_id": "uuid"
    # }
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
import traceback
from typing import Callable, Awaitable, Any

from app.utils.logger import default_logger


async def error_handler(request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
    """Global exception handler middleware.
    
    This middleware catches all exceptions raised during request processing,
    logs the error details, and returns a standardized JSON error response.
    
    Args:
        request: The FastAPI request object
        call_next: A callable that processes the request and returns a response
        
    Returns:
        If no exception occurs: The response from the route handler
        If an exception occurs: A JSONResponse with error details
        
    Example:
        # This middleware is automatically applied to all routes
        # When a route handler raises an exception:
        
        @app.get("/error")
        def raise_error():
            raise ValueError("Something went wrong")
        
        # The middleware will catch this and return:
        # {
        #     "error": "Internal Server Error",
        #     "message": "Something went wrong",
        #     "request_id": "uuid"
        # }
    """
    try:
        # Call the next middleware or route handler
        # This is where the actual request processing happens
        response = await call_next(request)
        return response
    except Exception as e:
        # Step 1: Log the exception details
        # Log the error message
        default_logger.error(f"Unhandled exception: {str(e)}")
        # Log the full traceback for debugging
        default_logger.error(traceback.format_exc())
        
        # Step 2: Get the request ID if available
        # The request ID is set in the route_query function
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Step 3: Return a standardized JSON error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(e),
                "request_id": request_id
            }
        )
