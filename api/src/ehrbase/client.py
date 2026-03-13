"""EHRBase client wrapper using oehrpy SDK.

Wraps the oehrpy EHRBaseClient to provide a consistent interface
for Open CIS, with logging and error handling.
"""

import logging
from typing import Any

import httpx
from openehr_sdk.client import EHRBaseClient as OehrpyClient
from openehr_sdk.client import EHRBaseError

from src.config import settings
from src.errors import EHRBaseUnavailableError, EHRBaseValidationError

logger = logging.getLogger(__name__)

# EHRBase error message patterns that indicate a validation/composition problem
_VALIDATION_PATTERNS = [
    "could not consume",
    "validation",
    "unknown path",
    "required field",
    "not allowed",
    "unrecognized",
    "parse",
    "missing",
    "invalid",
]


def _is_validation_error(message: str) -> bool:
    """Check if an EHRBase error message indicates a validation problem."""
    lower = message.lower()
    return any(pattern in lower for pattern in _VALIDATION_PATTERNS)


class EHRBaseClient:
    """Async EHRBase client backed by oehrpy SDK."""

    def __init__(self) -> None:
        self.base_url = settings.ehrbase_url
        self._client: OehrpyClient | None = None

    async def _ensure_connected(self) -> OehrpyClient:
        try:
            if self._client is None:
                self._client = OehrpyClient(
                    base_url=settings.ehrbase_url,
                    username=settings.ehrbase_user,
                    password=settings.ehrbase_password,
                )
            await self._client.connect()
            return self._client
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e

    async def create_ehr(self, ehr_id: str | None = None) -> dict[str, Any]:
        """Create a new EHR, optionally with a specific ID."""
        client = await self._ensure_connected()
        try:
            ehr = await client.create_ehr(ehr_id=ehr_id)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise  # unreachable, but satisfies type checkers
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return {"ehr_id": {"value": ehr.ehr_id}, "system_id": ehr.system_id}

    async def get_ehr(self, ehr_id: str) -> dict[str, Any]:
        """Get an EHR by ID."""
        client = await self._ensure_connected()
        try:
            ehr = await client.get_ehr(ehr_id)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return {"ehr_id": {"value": ehr.ehr_id}, "system_id": ehr.system_id}

    async def get_ehr_by_subject(
        self, subject_id: str, subject_namespace: str = "cis"
    ) -> dict[str, Any] | None:
        """Get an EHR by subject (patient) ID."""
        client = await self._ensure_connected()
        try:
            ehr = await client.get_ehr_by_subject(subject_id, subject_namespace)
            return {"ehr_id": {"value": ehr.ehr_id}, "system_id": ehr.system_id}
        except EHRBaseError:
            return None

    async def create_composition(
        self,
        ehr_id: str,
        template_id: str,
        composition: dict[str, Any],
        format: str = "FLAT",
    ) -> dict[str, Any]:
        """Create a composition in an EHR."""
        client = await self._ensure_connected()
        try:
            result = await client.create_composition(
                ehr_id=ehr_id,
                composition=composition,
                template_id=template_id,
                format=format,
            )
        except EHRBaseError as e:
            msg = str(e)
            logger.error("EHRBase create_composition failed: %s", msg)
            if _is_validation_error(msg):
                raise EHRBaseValidationError(
                    message=f"EHRBase rejected the composition: {msg}",
                    details={"template_id": template_id, "format": format},
                ) from e
            raise EHRBaseUnavailableError(
                message=f"EHRBase error: {msg}"
            ) from e
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return {
            "uid": {"value": result.uid},
            "compositionUid": result.uid,
        }

    async def get_composition(self, ehr_id: str, composition_uid: str) -> dict[str, Any]:
        """Get a composition by UID in default format."""
        client = await self._ensure_connected()
        try:
            result = await client.get_composition(ehr_id, composition_uid)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return result.composition or {}

    async def get_composition_formatted(
        self, ehr_id: str, composition_uid: str, format: str = "FLAT"
    ) -> dict[str, Any]:
        """Get a composition in a specific format (FLAT or STRUCTURED)."""
        client = await self._ensure_connected()
        try:
            result = await client.get_composition(ehr_id, composition_uid, format=format)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return result.composition or {}

    async def delete_composition(self, ehr_id: str, composition_uid: str) -> bool:
        """Delete a composition by UID. Returns True if successful."""
        client = await self._ensure_connected()
        try:
            await client.delete_composition(ehr_id, composition_uid)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return True

    async def execute_aql(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an AQL query."""
        client = await self._ensure_connected()
        try:
            result = await client.query(query, query_parameters=parameters)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return {
            "columns": result.columns,
            "rows": result.rows,
        }

    async def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates."""
        client = await self._ensure_connected()
        try:
            templates = await client.list_templates()
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return [
            {
                "template_id": t.template_id,
                "concept": t.concept,
                "archetype_id": t.archetype_id,
            }
            for t in templates
        ]

    async def upload_template(self, template_content: str) -> dict[str, Any]:
        """Upload an operational template (OPT)."""
        client = await self._ensure_connected()
        try:
            result = await client.upload_template(template_content)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return {"template_id": result.template_id, "status": "uploaded"}

    async def get_template_example(
        self, template_id: str, format: str = "FLAT"
    ) -> dict[str, Any]:
        """Get template info."""
        client = await self._ensure_connected()
        try:
            result = await client.get_template(template_id)
        except EHRBaseError as e:
            self._translate_ehrbase_error(e)
            raise
        except (httpx.RequestError, OSError) as e:
            raise EHRBaseUnavailableError(
                message="Cannot connect to EHRBase. Is it running?"
            ) from e
        return {"template_id": result.template_id, "concept": result.concept}

    async def health_check(self) -> bool:
        """Check if EHRBase is available."""
        client = await self._ensure_connected()
        return await client.health_check()

    async def close(self) -> None:
        """Close the underlying client."""
        if self._client:
            await self._client.close()
            self._client = None

    @staticmethod
    def _translate_ehrbase_error(e: EHRBaseError) -> None:
        """Translate EHRBaseError into a domain exception. Always raises."""
        msg = str(e)
        logger.error("EHRBase error: %s", msg)
        if _is_validation_error(msg):
            raise EHRBaseValidationError(
                message=f"EHRBase rejected the request: {msg}",
            ) from e
        raise EHRBaseUnavailableError(
            message=f"EHRBase error: {msg}"
        ) from e


# Singleton instance
ehrbase_client = EHRBaseClient()
