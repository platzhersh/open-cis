import asyncio
import importlib.metadata
import logging
from typing import Any

from src.db.client import prisma
from src.ehrbase.client import ehrbase_client
from src.system.schemas import (
    DbCountsData,
    DbCountsSection,
    HealthCheckItem,
    HealthChecksData,
    HealthChecksSection,
    SectionError,
    SystemInfoResponse,
    TemplateInfo,
    TemplatesSection,
    VersionData,
    VersionSection,
)

logger = logging.getLogger(__name__)


class SystemService:
    async def get_system_info(self) -> SystemInfoResponse:
        """Aggregate system health, versions, templates, and data stats."""
        ehrbase_result, stats_result = await asyncio.gather(
            self._get_ehrbase_info(),
            self._get_data_stats(),
            return_exceptions=True,
        )

        return SystemInfoResponse(
            healthChecks=self._build_health_checks(ehrbase_result),
            version=self._build_version(ehrbase_result),
            templates=self._build_templates(ehrbase_result),
            dbCounts=self._build_db_counts(stats_result),
        )

    def _build_health_checks(
        self, ehrbase_result: dict[str, Any] | BaseException
    ) -> HealthChecksSection:
        db_connected = prisma.is_connected()

        api_item = HealthCheckItem(
            status="ok" if db_connected else "error",
            data={"status": "healthy" if db_connected else "degraded"},
            error=None if db_connected else SectionError(
                code="API_DEGRADED", message="Database not connected"
            ),
        )

        db_item = HealthCheckItem(
            status="ok" if db_connected else "error",
            data={"status": "connected"} if db_connected else None,
            error=None if db_connected else SectionError(
                code="DB_DISCONNECTED", message="Cannot connect to application database"
            ),
        )

        if isinstance(ehrbase_result, BaseException):
            logger.warning("EHRBase info fetch failed: %s", ehrbase_result)
            ehrbase_item = HealthCheckItem(
                status="error",
                data=None,
                error=SectionError(
                    code="EHRBASE_UNAVAILABLE",
                    message="Cannot connect to EHRBase. Is it running?",
                ),
            )
        else:
            ehrbase_status = ehrbase_result.get("status", "unavailable")
            if ehrbase_status == "available":
                ehrbase_item = HealthCheckItem(
                    status="ok", data={"status": "available"}, error=None
                )
            else:
                ehrbase_item = HealthCheckItem(
                    status="error",
                    data=None,
                    error=SectionError(
                        code="EHRBASE_UNAVAILABLE",
                        message="EHRBase is not responding",
                    ),
                )

        items = [api_item, db_item, ehrbase_item]
        error_count = sum(1 for i in items if i.status == "error")

        if error_count == 0:
            section_status = "ok"
            section_error = None
        elif error_count == len(items):
            section_status = "error"
            section_error = SectionError(
                code="ALL_HEALTH_FAILED", message="All health checks failed"
            )
        else:
            section_status = "partial"
            section_error = SectionError(
                code="PARTIAL_HEALTH", message="One or more health checks failed"
            )

        return HealthChecksSection(
            status=section_status,
            data=HealthChecksData(api=api_item, database=db_item, ehrbase=ehrbase_item),
            error=section_error,
        )

    def _build_version(
        self, ehrbase_result: dict[str, Any] | BaseException
    ) -> VersionSection:
        try:
            api_version = importlib.metadata.version("cis-api")
        except importlib.metadata.PackageNotFoundError:
            api_version = "0.3.0"

        ehrbase_version: str | None = None
        if not isinstance(ehrbase_result, BaseException):
            ehrbase_version = ehrbase_result.get("version")

        data = VersionData(api=api_version, ehrbase=ehrbase_version)

        if ehrbase_version is not None:
            return VersionSection(status="ok", data=data, error=None)

        return VersionSection(
            status="partial",
            data=data,
            error=SectionError(
                code="PARTIAL_VERSION",
                message="Could not determine EHRBase version",
            ),
        )

    def _build_templates(
        self, ehrbase_result: dict[str, Any] | BaseException
    ) -> TemplatesSection:
        if isinstance(ehrbase_result, BaseException):
            return TemplatesSection(
                status="error",
                data=None,
                error=SectionError(
                    code="EHRBASE_UNAVAILABLE",
                    message="Cannot fetch templates — EHRBase unavailable",
                ),
            )

        raw_templates = ehrbase_result.get("templates")
        if raw_templates is None:
            return TemplatesSection(
                status="error",
                data=None,
                error=SectionError(
                    code="TEMPLATES_FETCH_FAILED",
                    message="EHRBase reachable but template listing failed",
                ),
            )

        templates = [TemplateInfo(**t) for t in raw_templates]
        return TemplatesSection(status="ok", data=templates, error=None)

    def _build_db_counts(
        self, stats_result: DbCountsData | BaseException
    ) -> DbCountsSection:
        if isinstance(stats_result, BaseException):
            logger.warning("Data stats fetch failed: %s", stats_result)
            return DbCountsSection(
                status="error",
                data=None,
                error=SectionError(
                    code="DB_COUNTS_FAILED",
                    message=f"Could not fetch database counts: {stats_result}",
                ),
            )

        return DbCountsSection(status="ok", data=stats_result, error=None)

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

    async def _get_data_stats(self) -> DbCountsData:
        """Fetch counts from the application database."""
        patients, encounters, audit_logs = await asyncio.gather(
            prisma.patientregistry.count(),
            prisma.encounter.count(),
            prisma.auditlog.count(),
        )
        return DbCountsData(
            patients=patients,
            encounters=encounters,
            audit_logs=audit_logs,
        )


system_service = SystemService()
