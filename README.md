# DSAgent Ralph

Autonomous Data Science Agent with Ralph orchestrator, specialized agents, and cloud-native deployment.

## Quick Start

```bash
# Clone and setup
cp .env.example .env
# Edit .env with your API keys

# Start with Docker
docker-compose up -d

# Or locally
poetry install
poetry run uvicorn dsagent.main:app --reload
```

## Architecture

- **Ralph** - Orchestrator central
- **Agents** - Planner, Executor, Evaluator, Conversational
- **Skills** - Ejecutables en Jupyter kernel
- **API** - FastAPI con SSE streaming

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Lint
poetry run ruff check .
```

## Deployment

See `docs/DEPLOYMENT.md` for Kubernetes and cloud deployment.
