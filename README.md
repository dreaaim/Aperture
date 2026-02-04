# Aperture
Intelligent LLM Router

## Overview
This repository provides a lightweight LLM MoE router + semantic cache prototype. It implements:

- Semantic cache with direct-hit and few-shot fallback.
- Intent classification + difficulty estimation.
- Weighted multi-factor routing (history, price, quota, difficulty match).
- Request logging for feedback loops.
- Model API adapters for different API formats (OpenAI, Claude, etc.).
- Enhanced model status management with detailed configuration options.

## Documentation

For detailed documentation, please refer to the [docs](./docs/) directory:

- [Home](./docs/index.md) - Overview of the project
- [Architecture](./docs/architecture.md) - Detailed architecture design
- [Usage](./docs/usage.md) - Installation and usage guide
- [Core Features](./docs/core-features.md) - Detailed explanation of core features
- [Development](./docs/development.md) - Development guide for contributors

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Example request:
```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "帮我写个Python贪吃蛇"}'
```

### Additional Examples

#### With User ID

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "帮我写个Python贪吃蛇", "user_id": "user123"}'
```

#### With Custom Configuration

```python
import requests
import json

url = "http://localhost:8000/v1/query"
payload = {
    "query": "解释量子计算的基本原理",
    "user_id": "researcher456"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.json())
```

#### Using Different Models

Aperture automatically selects the best model based on the query, but you can also configure specific models for different use cases:

```python
from app.models import ModelStatus
from app.services.model_adapters.claude_adapter import ClaudeAdapter

# Configure a specialized model for code generation
code_model = ModelStatus(
    model_id="gpt-4o",
    price_per_1k_tokens=5.0,
    remaining_tokens=400000,
    quality_tier="large",
    api_format="openai",
    reasoning_support=True,
    enabled=True,
    rate_limit=60,
    max_concurrency=10,
    timeout=30,
    reasoning_level="high"
)

# Configure a cost-effective model for simple queries
chat_model = ModelStatus(
    model_id="llama-3-8b",
    price_per_1k_tokens=0.2,
    remaining_tokens=1000000,
    quality_tier="small",
    api_format="openai",
    reasoning_support=False,
    enabled=True,
    rate_limit=100,
    max_concurrency=20,
    timeout=20,
    reasoning_level="low"
)
```

## How it works
1. The query is embedded and compared against cached entries.
2. If similarity >= 0.95, return cached answer (HIT).
3. If similarity >= 0.85, inject cached QA as few-shot and force a small model (FEW_SHOT).
4. Otherwise, estimate intent + difficulty and score all models to select the best one (MISS).

## Core Features

### Semantic Cache
- Direct-hit and few-shot fallback mechanisms
- Cosine similarity-based search
- Efficient memory storage

### Intent Classification & Difficulty Estimation
- Keyword-based intent tagging
- Historical data-driven difficulty estimation
- Support for multiple intent categories

### Intelligent Model Selection
- Weighted multi-factor scoring (history, price, quota, difficulty match)
- Dynamic model ranking
- Quality-tier based model selection

### Model API Adapters
- Support for different API formats (OpenAI, Claude, etc.)
- Unified request/response handling
- Format conversion between different API standards
- Error handling and normalization

### Enhanced Model Management
- Detailed model status tracking
- Support for reasoning levels
- Rate limiting and concurrency control
- Timeout management

### Request Logging & Analytics
- Comprehensive request tracking
- Feedback loop support
- Performance metrics collection

## Model API Adapters

### Overview
Aperture provides a flexible model adapter system that allows seamless integration with different LLM API formats. This system enables the router to work with various model providers without changing the core routing logic.

### Supported Adapters

#### OpenAI Adapter
- Supports OpenAI's chat completion API format
- Handles request formatting and response parsing
- Provides error normalization

#### Claude Adapter
- Supports Anthropic's Claude API format
- Converts between Claude and OpenAI formats
- Handles Claude-specific response structures

### Usage Example

```python
from app.services.model_adapters.claude_adapter import ClaudeAdapter
from app.models import ModelStatus

# Define a model with Claude API format
model = ModelStatus(
    model_id="claude-3.5-sonnet",
    price_per_1k_tokens=3.5,
    remaining_tokens=300000,
    quality_tier="large",
    api_format="claude"
)

# Create an adapter for the model
adapter = ClaudeAdapter(model)

# Format a request
request = adapter.format_request("Hello, how are you?")

# Parse a response
response = {"content": [{"type": "text", "text": "I'm doing well, thank you!"}]}
parsed = adapter.parse_response(response)

# Convert to OpenAI format
openai_format = adapter.convert_to_openai(response)
```

### Creating Custom Adapters

To create a custom adapter for a new API format:

1. Extend the `ModelAdapter` base class
2. Implement the required methods:
   - `format_request()`: Format a query for the API
   - `parse_response()`: Parse the API's response
   - `convert_to_openai()`: Convert response to OpenAI format
   - `handle_error()`: Handle API errors

```python
from app.services.model_adapters.base_adapter import ModelAdapter
from app.models import ModelStatus

class CustomAdapter(ModelAdapter):
    def format_request(self, query, **kwargs):
        # Implementation
        pass
    
    def parse_response(self, response):
        # Implementation
        pass
    
    def convert_to_openai(self, response):
        # Implementation
        pass
    
    def handle_error(self, error):
        # Implementation
        pass
```

## Extending
- Replace `embed_text` with your embedding provider.
- Integrate a real vector DB and a model gateway (LiteLLM, LangChain, etc.).
- Customize intent classification and model selection strategies.
- Create custom model adapters for additional API formats.
- Extend ModelStatus with additional fields for custom use cases.

### Adding Custom Model Adapters

To add support for a new API format:

1. Create a new adapter class that extends `ModelAdapter`
2. Implement the required methods for request formatting, response parsing, and error handling
3. Register the adapter in the model service
4. Update the model configuration to use the new API format

### Example: Custom Adapter

```python
from app.services.model_adapters.base_adapter import ModelAdapter
from app.models import ModelStatus

class CustomAPIAdapter(ModelAdapter):
    def format_request(self, query, **kwargs):
        """Format a query for the custom API."""
        return {
            "prompt": query,
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7)
        }
    
    def parse_response(self, response):
        """Parse the custom API response."""
        return response.get("output", "")
    
    def convert_to_openai(self, response):
        """Convert to OpenAI format."""
        return {
            "id": "custom-1",
            "object": "chat.completion",
            "created": 1234567890,
            "model": self.model.model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": self.parse_response(response)
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {}
        }
    
    def handle_error(self, error):
        """Handle API errors."""
        return {
            "error": {
                "message": str(error),
                "type": error.__class__.__name__,
                "code": "custom_api_error"
            }
        }
```

## Configuration

### Model Status Configuration

Aperture provides detailed configuration options for each model through the `ModelStatus` class. Here are the available fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model_id` | string | - | Unique identifier for the model |
| `price_per_1k_tokens` | float | - | Price per 1000 tokens |
| `remaining_tokens` | int | - | Remaining token quota |
| `quality_tier` | string | - | Model quality tier (small/medium/large) |
| `api_format` | string | "openai" | API format type (openai/claude/custom) |
| `reasoning_support` | bool | false | Whether the model supports reasoning levels |
| `enabled` | bool | true | Whether the model is enabled |
| `rate_limit` | int | 60 | Rate limit per minute |
| `max_concurrency` | int | 10 | Maximum concurrent requests |
| `timeout` | int | 30 | Request timeout in seconds |
| `reasoning_level` | string | "medium" | Current reasoning level |
| `processing_time` | float | 0.0 | Processing time in milliseconds |

### Example Model Configuration

```python
from app.models import ModelStatus

# OpenAI model configuration
openai_model = ModelStatus(
    model_id="gpt-4o",
    price_per_1k_tokens=5.0,
    remaining_tokens=400000,
    quality_tier="large",
    api_format="openai",
    reasoning_support=True,
    enabled=True,
    rate_limit=60,
    max_concurrency=10,
    timeout=30,
    reasoning_level="high"
)

# Claude model configuration
claude_model = ModelStatus(
    model_id="claude-3.5-sonnet",
    price_per_1k_tokens=3.5,
    remaining_tokens=300000,
    quality_tier="large",
    api_format="claude",
    reasoning_support=False,
    enabled=True,
    rate_limit=60,
    max_concurrency=10,
    timeout=30
)
```

## API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
