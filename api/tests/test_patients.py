"""Tests for patient endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_list_patients_empty(client: AsyncClient):
    """Test listing patients when none exist."""
    response = await client.get("/api/patients")
    assert response.status_code == 200
    assert response.json() == []
