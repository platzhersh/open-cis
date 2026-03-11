#!/bin/bash

# Open CIS Setup Script
# Run this to set up the development environment

set -e

echo "🏥 Setting up Open CIS..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "pnpm is required but not installed. Aborting." >&2; exit 1; }

# Start Docker services
echo "📦 Starting Docker services..."
docker compose up -d

# Wait for EHRBase to be ready
echo "⏳ Waiting for EHRBase to be ready (this may take 30-60 seconds)..."
until curl -s http://localhost:8080/ehrbase/rest/status > /dev/null 2>&1; do
    sleep 5
    echo "   Still waiting..."
done
echo "✅ EHRBase is ready!"

# Wait for Terminology Server to be ready
echo "⏳ Waiting for Terminology Server (Snowstorm Lite) to be ready..."
until curl -s http://localhost:8081/fhir/metadata > /dev/null 2>&1; do
    sleep 5
    echo "   Still waiting..."
done
echo "✅ Terminology Server is ready!"

# Setup Python API
echo "🐍 Setting up Python API..."
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
prisma generate
prisma migrate dev --name init
cd ..

# Setup Vue frontend
echo "🎨 Setting up Vue frontend..."
cd web
pnpm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  Terminal 1: cd api && source .venv/bin/activate && uvicorn src.main:app --reload --port 8000"
echo "  Terminal 2: cd web && pnpm dev"
echo ""
echo "API will be at: http://localhost:8000"
echo "Web will be at: http://localhost:5173"
echo "EHRBase at: http://localhost:8080/ehrbase/rest/status"
echo "Terminology Server at: http://localhost:8081/fhir/metadata"
