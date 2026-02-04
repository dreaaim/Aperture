"""API middleware for error handling and logging."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
import traceback

from app.utils.logger import default_logger


async def error_handler(request: Request, call_next):
    """Middleware to handle exceptions globally."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the exception
        default_logger.error(f"Unhandled exception: {str(e)}")
        default_logger.error(traceback.format_exc())
        
        # Return a JSON response with error details
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(e),
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        )
