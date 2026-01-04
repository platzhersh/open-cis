FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by Prisma (needs libatomic for Node.js)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (paths relative to repo root since Railway uses repo root as build context)
COPY api/pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source
COPY api/src ./src
COPY api/prisma ./prisma
COPY api/templates ./templates

# Generate Prisma client
RUN prisma generate

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser && \
    chown -R appuser:appgroup /app && \
    # Grant non-root user ownership of Prisma query engine binary in site-packages
    chown -R appuser:appgroup /usr/local/lib/python*/site-packages/prisma/

USER appuser

EXPOSE 8000

# Use Railway's $PORT if available, otherwise default to 8000
# Use shell form to allow environment variable substitution
# Run migrations before starting the server
CMD sh -c "echo 'Running database migrations...' && prisma migrate deploy && echo 'Starting uvicorn on port ${PORT:-8000}...' && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
