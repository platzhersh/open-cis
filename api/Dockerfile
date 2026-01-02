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

# Generate Prisma client
RUN prisma generate

EXPOSE 8000

# Use Railway's $PORT if available, otherwise default to 8000
# Use shell form to allow environment variable substitution
CMD sh -c "echo 'Starting uvicorn on port ${PORT:-8000}...' && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
