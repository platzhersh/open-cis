"""Pytest fixtures for API tests."""

from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.auth.dependencies import get_current_user
from src.db.client import prisma
from src.main import app


def _make_mock_user(role: str = "CLINICIAN") -> MagicMock:
    user = MagicMock()
    user.id = "test-user-id"
    user.externalId = "test-external-id"
    user.email = "test@open-cis.local"
    user.name = "Test User"
    user.role = role
    return user


@pytest_asyncio.fixture
async def client():
    """Create an async test client with auth bypassed (CLINICIAN role)."""
    mock_user = _make_mock_user("CLINICIAN")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def admin_client():
    """Create an async test client with ADMIN role."""
    mock_user = _make_mock_user("ADMIN")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_current_user, None)


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
