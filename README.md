# Aperture
Intelligent LLM Router

## Overview
This repository provides a lightweight LLM MoE router + semantic cache prototype. It implements:

- Semantic cache with direct-hit and few-shot fallback.
- Intent classification + difficulty estimation.
- Weighted multi-factor routing (history, price, quota, difficulty match).
- Request logging for feedback loops.

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

## How it works
1. The query is embedded and compared against cached entries.
2. If similarity >= 0.95, return cached answer (HIT).
3. If similarity >= 0.85, inject cached QA as few-shot and force a small model (FEW_SHOT).
4. Otherwise, estimate intent + difficulty and score all models to select the best one (MISS).

## Extending
- Replace `embed_text` with your embedding provider.
- Integrate a real vector DB and a model gateway (LiteLLM, LangChain, etc.).
- Customize intent classification and model selection strategies.

## API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
