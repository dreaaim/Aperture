"""FastAPI entrypoint implementing the LLM gateway routing flow."""

from fastapi import FastAPI

from app.api.endpoints import router
from app.api.middleware import error_handler
from app.utils.logger import default_logger

app = FastAPI(title="Aperture LLM Router")

# Add middleware
app.middleware("http")(error_handler)

# Include API routes
app.include_router(router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    default_logger.info("Aperture LLM Router starting up...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    default_logger.info("Aperture LLM Router shutting down...")
