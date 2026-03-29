import asyncio
import importlib.metadata
import logging
from typing import Any

from src.db.client import prisma
from src.ehrbase.client import ehrbase_client
from src.system.schemas import (
    DataStats,
    HealthInfo,
    SystemInfoResponse,
    TemplateInfo,
    VersionInfo,
)

logger = logging.getLogger(__name__)


class SystemService:
    async def get_system_info(self) -> SystemInfoResponse:
        """Aggregate system health, versions, templates, and data stats."""
        # Run all checks concurrently; failures are isolated per section
        ehrbase_result, stats_result = await asyncio.gather(
            self._get_ehrbase_info(),
            self._get_data_stats(),
            return_exceptions=True,
        )

        # API version
        try:
            api_version = importlib.metadata.version("cis-api")
        except importlib.metadata.PackageNotFoundError:
            api_version = "0.3.0"

        # Database health
        db_connected = prisma.is_connected()

        # Process EHRBase result
        ehrbase_version: str | None = None
        ehrbase_status = "unavailable"
        templates: list[TemplateInfo] | None = None

        if isinstance(ehrbase_result, Exception):
            logger.warning("EHRBase info fetch failed: %s", ehrbase_result)
        else:
            ehrbase_version = ehrbase_result.get("version")
            ehrbase_status = ehrbase_result.get("status", "unavailable")
            raw_templates = ehrbase_result.get("templates")
            if raw_templates is not None:
                templates = [TemplateInfo(**t) for t in raw_templates]

        # Process stats result
        stats: DataStats | None = None
        if isinstance(stats_result, Exception):
            logger.warning("Data stats fetch failed: %s", stats_result)
        else:
            stats = stats_result

        return SystemInfoResponse(
            versions=VersionInfo(api=api_version, ehrbase=ehrbase_version),
            health=HealthInfo(
                api="healthy" if db_connected else "degraded",
                database="connected" if db_connected else "disconnected",
                ehrbase=ehrbase_status,
            ),
            templates=templates,
            stats=stats,
        )

    async def _get_ehrbase_info(self) -> dict[str, Any]:
        """Fetch EHRBase health, version, and templates."""
        result: dict[str, Any] = {"status": "unavailable", "version": None, "templates": None}

        try:
            healthy = await ehrbase_client.health_check()
            result["status"] = "available" if healthy else "unavailable"
        except Exception:
            return result

        # Fetch version from EHRBase status endpoint
        try:
            client = await ehrbase_client._ensure_connected()
            response = await client.client.get("/rest/status")
            if response.status_code == 200:
                data = response.json()
                result["version"] = data.get("version", "unknown")
        except Exception as e:
            logger.debug("Could not fetch EHRBase version: %s", e)

        # Fetch templates
        try:
            result["templates"] = await ehrbase_client.list_templates()
        except Exception as e:
            logger.debug("Could not fetch templates: %s", e)

        return result

    async def _get_data_stats(self) -> DataStats:
        """Fetch counts from the application database."""
        patients, encounters, audit_logs = await asyncio.gather(
            prisma.patientregistry.count(),
            prisma.encounter.count(),
            prisma.auditlog.count(),
        )
        return DataStats(
            patients=patients,
            encounters=encounters,
            audit_logs=audit_logs,
        )


system_service = SystemService()
