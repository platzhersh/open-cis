FROM python:3.11-slim

WORKDIR /app

# Install dependencies (paths relative to repo root since Railway uses repo root as build context)
COPY api/pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source
COPY api/src ./src
COPY api/prisma ./prisma

# Generate Prisma client
RUN prisma generate

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
