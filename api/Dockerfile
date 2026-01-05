FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by Prisma (needs libatomic for Node.js)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (before installing dependencies so cache is owned correctly)
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set Prisma binary cache to a location accessible by appuser
ENV PRISMA_BINARY_CACHE_DIR=/home/appuser/.cache/prisma-python

# Install dependencies (paths relative to repo root since Railway uses repo root as build context)
COPY api/pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source
COPY api/src ./src
COPY api/prisma ./prisma
COPY api/templates ./templates

# Copy seed scripts (from repo root)
COPY scripts /scripts

# Generate Prisma client (binaries will be cached in PRISMA_BINARY_CACHE_DIR)
RUN prisma generate

# Grant non-root user ownership of app directory, scripts, and Prisma binaries
RUN chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /scripts && \
    chown -R appuser:appgroup /home/appuser/.cache && \
    chown -R appuser:appgroup /usr/local/lib/python*/site-packages/prisma/

USER appuser

EXPOSE 8000

# Use Railway's $PORT if available, otherwise default to 8000
# Use shell form to allow environment variable substitution
# Run migrations before starting the server
# Conditionally seed staging data if RAILWAY_ENVIRONMENT=staging
CMD sh -c "echo 'Running database migrations...' && \
  prisma migrate deploy && \
  if [ \"$RAILWAY_ENVIRONMENT\" = \"staging\" ]; then \
    echo 'Seeding staging data...' && python /scripts/seed_staging.py; \
  fi && \
  echo 'Starting uvicorn on port ${PORT:-8000}...' && \
  uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
