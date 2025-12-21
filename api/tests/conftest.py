"""Pytest fixtures for API tests."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.db.client import prisma
from src.main import app


@pytest_asyncio.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Connect and disconnect from the database for each test."""
    await prisma.connect()
    yield
    await prisma.disconnect()


@pytest.fixture
def sample_patient_data():
    """Sample patient data for tests."""
    return {
        "mrn": "TEST-001",
        "given_name": "John",
        "family_name": "Doe",
        "birth_date": "1990-01-15"
    }
