"""Tests for audit service (api/src/audit/service.py)."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.audit.service import log_action


class TestLogAction:
    @pytest.mark.asyncio
    async def test_log_action_creates_audit_entry(self):
        """log_action creates an auditlog entry with correct fields."""
        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock()

            await log_action(
                user_id="user-1",
                action="CREATE",
                resource="Patient",
                resource_id="patient-1",
            )

            mock_prisma.auditlog.create.assert_called_once()
            call_data = mock_prisma.auditlog.create.call_args[1]["data"]
            assert call_data["userId"] == "user-1"
            assert call_data["action"] == "CREATE"
            assert call_data["resource"] == "Patient"
            assert call_data["resourceId"] == "patient-1"

    @pytest.mark.asyncio
    async def test_log_action_with_all_optional_params(self):
        """log_action passes ehr_id and metadata correctly."""
        from prisma import Json

        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock()

            await log_action(
                user_id="user-2",
                action="UPDATE",
                resource="Encounter",
                resource_id="enc-42",
                ehr_id="ehr-99",
                metadata={"reason": "correction", "field": "status"},
            )

            call_data = mock_prisma.auditlog.create.call_args[1]["data"]
            assert call_data["userId"] == "user-2"
            assert call_data["action"] == "UPDATE"
            assert call_data["resource"] == "Encounter"
            assert call_data["resourceId"] == "enc-42"
            assert call_data["ehrId"] == "ehr-99"
            # metadata should be wrapped in Json
            assert isinstance(call_data["metadata"], Json)

    @pytest.mark.asyncio
    async def test_log_action_without_optional_params_uses_none(self):
        """log_action uses None for optional resource_id, ehr_id, metadata."""
        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock()

            await log_action(
                user_id="user-3",
                action="DELETE",
                resource="NKA",
            )

            call_data = mock_prisma.auditlog.create.call_args[1]["data"]
            assert call_data["resourceId"] is None
            assert call_data["ehrId"] is None
            assert call_data["metadata"] is None

    @pytest.mark.asyncio
    async def test_log_action_swallows_exception_does_not_raise(self):
        """log_action catches exceptions and does not propagate them."""
        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock(side_effect=Exception("DB error"))

            # Should not raise
            await log_action(
                user_id="user-4",
                action="CREATE",
                resource="VitalSigns",
                resource_id="vs-1",
            )

    @pytest.mark.asyncio
    async def test_log_action_logs_exception_on_failure(self, caplog):
        """log_action logs an error message when the DB write fails."""
        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock(side_effect=RuntimeError("connection refused"))

            with caplog.at_level(logging.ERROR, logger="src.audit.service"):
                await log_action(
                    user_id="user-5",
                    action="DELETE",
                    resource="CaveEntry",
                )

            assert any("Failed to write audit log" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_log_action_metadata_none_when_not_provided(self):
        """metadata field is None (not Json(None)) when omitted."""
        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock()

            await log_action(user_id="u", action="A", resource="R")

            call_data = mock_prisma.auditlog.create.call_args[1]["data"]
            assert call_data["metadata"] is None

    @pytest.mark.asyncio
    async def test_log_action_empty_metadata_dict_is_wrapped(self):
        """Empty dict metadata is still wrapped in Json (not None)."""
        from prisma import Json

        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock()

            await log_action(
                user_id="u",
                action="A",
                resource="R",
                metadata={},
            )

            call_data = mock_prisma.auditlog.create.call_args[1]["data"]
            assert isinstance(call_data["metadata"], Json)

    @pytest.mark.asyncio
    async def test_log_action_returns_none(self):
        """log_action is a void function and returns None."""
        with patch("src.audit.service.prisma") as mock_prisma:
            mock_prisma.auditlog.create = AsyncMock()

            result = await log_action(user_id="u", action="A", resource="R")
            assert result is None