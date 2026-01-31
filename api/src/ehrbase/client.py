"""EHRBase client wrapper using oehrpy SDK.

Wraps the oehrpy EHRBaseClient to provide a consistent interface
for Open CIS, with logging and error handling.
"""

from typing import Any

from openehr_sdk.client import EHRBaseClient as OehrpyClient
from openehr_sdk.client import EHRBaseError

from src.config import settings


class EHRBaseClient:
    """Async EHRBase client backed by oehrpy SDK."""

    def __init__(self) -> None:
        self.base_url = settings.ehrbase_url
        self._client: OehrpyClient | None = None

    async def _ensure_connected(self) -> OehrpyClient:
        if self._client is None:
            self._client = OehrpyClient(
                base_url=settings.ehrbase_url,
                username=settings.ehrbase_user,
                password=settings.ehrbase_password,
            )
        await self._client.connect()
        return self._client

    async def create_ehr(self, ehr_id: str | None = None) -> dict[str, Any]:
        """Create a new EHR, optionally with a specific ID."""
        client = await self._ensure_connected()
        ehr = await client.create_ehr(ehr_id=ehr_id)
        return {"ehr_id": {"value": ehr.ehr_id}, "system_id": ehr.system_id}

    async def get_ehr(self, ehr_id: str) -> dict[str, Any]:
        """Get an EHR by ID."""
        client = await self._ensure_connected()
        ehr = await client.get_ehr(ehr_id)
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
        result = await client.create_composition(
            ehr_id=ehr_id,
            composition=composition,
            template_id=template_id,
            format=format,
        )
        return {
            "uid": {"value": result.uid},
            "compositionUid": result.uid,
        }

    async def get_composition(self, ehr_id: str, composition_uid: str) -> dict[str, Any]:
        """Get a composition by UID in default format."""
        client = await self._ensure_connected()
        result = await client.get_composition(ehr_id, composition_uid)
        return result.composition or {}

    async def get_composition_formatted(
        self, ehr_id: str, composition_uid: str, format: str = "FLAT"
    ) -> dict[str, Any]:
        """Get a composition in a specific format (FLAT or STRUCTURED)."""
        client = await self._ensure_connected()
        result = await client.get_composition(ehr_id, composition_uid, format=format)
        return result.composition or {}

    async def delete_composition(self, ehr_id: str, composition_uid: str) -> bool:
        """Delete a composition by UID. Returns True if successful."""
        client = await self._ensure_connected()
        await client.delete_composition(ehr_id, composition_uid)
        return True

    async def execute_aql(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an AQL query."""
        client = await self._ensure_connected()
        result = await client.query(query, query_parameters=parameters)
        return {
            "columns": result.columns,
            "rows": result.rows,
        }

    async def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates."""
        client = await self._ensure_connected()
        templates = await client.list_templates()
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
        result = await client.upload_template(template_content)
        return {"template_id": result.template_id, "status": "uploaded"}

    async def get_template_example(
        self, template_id: str, format: str = "FLAT"
    ) -> dict[str, Any]:
        """Get template info."""
        client = await self._ensure_connected()
        result = await client.get_template(template_id)
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


# Singleton instance
ehrbase_client = EHRBaseClient()
