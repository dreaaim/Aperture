"""FastAPI entrypoint implementing the LLM gateway routing flow.

This module serves as the entrypoint for the FastAPI application, responsible for:
- Creating and configuring the FastAPI app instance
- Adding middleware for error handling and logging
- Including API routes from the endpoints module
- Setting up startup and shutdown events

Example:
    # To run the application:
    # uvicorn app.main:app --reload
    
    # To access the API documentation:
    # http://localhost:8000/docs
    # http://localhost:8000/redoc
"""

from fastapi import FastAPI

from app.api.endpoints import router
from app.api.middleware import error_handler
from app.utils.logger import default_logger
from app.utils.telemetry import setup_instrumentation

# Create FastAPI application instance
# The title parameter sets the application name in the API documentation
app = FastAPI(title="Aperture LLM Router")

# Set up OpenTelemetry instrumentation
# This instruments the FastAPI application and requests library
setup_instrumentation(app)

# Add HTTP middleware for global error handling
# This middleware catches all exceptions and returns standardized error responses
app.middleware("http")(error_handler)

# Include API routes from the endpoints module
# This adds all the routes defined in the router to the application
app.include_router(router)

# Startup event handler
# This function is called when the application starts up
@app.on_event("startup")
async def startup_event():
    """Log application startup event.
    
    This function is called when the FastAPI application starts up.
    It logs a startup message to indicate that the application is starting.
    """
    default_logger.info("Aperture LLM Router starting up...")

# Shutdown event handler
# This function is called when the application shuts down
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown event.
    
    This function is called when the FastAPI application shuts down.
    It logs a shutdown message to indicate that the application is shutting down.
    """
    default_logger.info("Aperture LLM Router shutting down...")
