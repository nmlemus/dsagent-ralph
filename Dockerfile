FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./

# Install dependencies with uv (much faster than poetry)
RUN uv sync --frozen --no-dev -p 3.11

# Copy source code
COPY src/ ./src/

# Create directories
RUN mkdir -p /artifacts /projects

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "dsagent.main:app", "--host", "0.0.0.0", "--port", "8000"]
