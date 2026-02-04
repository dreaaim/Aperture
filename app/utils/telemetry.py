"""OpenTelemetry configuration and utilities for distributed tracing.

This module provides configuration and utilities for OpenTelemetry,
including:
- Tracer provider initialization
- Exporter configuration
- Instrumentation setup
- Helper functions for creating spans
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Create a tracer provider with resource information
resource = Resource(
    attributes={
        ResourceAttributes.SERVICE_NAME: "aperture-llm-router",
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development"
    }
)

# Initialize tracer provider
tracer_provider = TracerProvider(resource=resource)

# Add console exporter for debugging
# This will print traces to the console, which is useful for testing
console_exporter = ConsoleSpanExporter()
# Use SimpleSpanProcessor for immediate processing of spans
# This is better for debugging as spans are processed immediately
console_processor = SimpleSpanProcessor(console_exporter)
tracer_provider.add_span_processor(console_processor)

# Configure OTLP HTTP exporter (optional)
# This will send traces to a local collector if available
# For production, you would configure this to send to your tracing backend
# Uncomment the following lines if you have an OTLP collector running
# span_exporter = OTLPSpanExporter(
#     endpoint="http://localhost:4318/v1/traces",  # Default OTLP HTTP endpoint
# )
# span_processor = BatchSpanProcessor(span_exporter)
# tracer_provider.add_span_processor(span_processor)

# Set the global tracer provider
trace.set_tracer_provider(tracer_provider)



def setup_instrumentation(app):
    """Set up instrumentation for the application.
    
    This function instruments the FastAPI application and requests library
    to automatically capture spans for HTTP requests.
    
    Args:
        app: FastAPI application instance
    """
    # Instrument FastAPI application
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument requests library
    RequestsInstrumentor().instrument()


def get_tracer(name=None):
    """Get the global tracer instance.
    
    Args:
        name: Optional name for the tracer. If not provided, uses the default name.
    
    Returns:
        Tracer: OpenTelemetry tracer instance
    """
    if name:
        return trace.get_tracer(name)
    return trace.get_tracer(__name__)
