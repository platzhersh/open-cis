"""Tests for EHRBase client."""

import pytest
from unittest.mock import AsyncMock, patch

from src.ehrbase.client import EHRBaseClient


@pytest.mark.asyncio
async def test_ehrbase_client_creation():
    """Test EHRBase client can be instantiated."""
    client = EHRBaseClient()
    assert client.base_url is not None
    assert client._client is None


@pytest.mark.asyncio
async def test_ehrbase_client_close():
    """Test EHRBase client close when not connected."""
    client = EHRBaseClient()
    await client.close()
    assert client._client is None
