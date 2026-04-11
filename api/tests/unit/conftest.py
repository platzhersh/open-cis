"""Conftest for unit tests that do not require database or external services."""

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Override the root conftest setup_db — no database needed for unit tests."""
    yield
