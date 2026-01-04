from typing import Any

import httpx

from src.config import settings


class EHRBaseClient:
    """Async client for EHRBase REST API."""

    def __init__(self):
        self.base_url = settings.ehrbase_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            auth = None
            if settings.ehrbase_user and settings.ehrbase_password:
                auth = httpx.BasicAuth(settings.ehrbase_user, settings.ehrbase_password)

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=auth,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def create_ehr(self, ehr_id: str | None = None) -> dict[str, Any]:
        """Create a new EHR, optionally with a specific ID."""
        client = await self._get_client()
        headers = {"Prefer": "return=representation"}

        if ehr_id:
            response = await client.put(f"/openehr/v1/ehr/{ehr_id}", headers=headers)
        else:
            response = await client.post("/openehr/v1/ehr", headers=headers)

        response.raise_for_status()
        return response.json()

    async def get_ehr(self, ehr_id: str) -> dict[str, Any]:
        """Get an EHR by ID."""
        client = await self._get_client()
        response = await client.get(f"/openehr/v1/ehr/{ehr_id}")
        response.raise_for_status()
        return response.json()

    async def get_ehr_by_subject(
        self, subject_id: str, subject_namespace: str = "cis"
    ) -> dict[str, Any] | None:
        """Get an EHR by subject (patient) ID."""
        client = await self._get_client()
        response = await client.get(
            "/openehr/v1/ehr",
            params={"subject_id": subject_id, "subject_namespace": subject_namespace}
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def create_composition(
        self,
        ehr_id: str,
        template_id: str,
        composition: dict[str, Any],
        format: str = "FLAT"
    ) -> dict[str, Any]:
        """Create a composition in an EHR."""
        client = await self._get_client()
        response = await client.post(
            f"/openehr/v1/ehr/{ehr_id}/composition",
            json=composition,
            headers={
                "Prefer": "return=representation",
                "Content-Type": "application/json"
            },
            params={"templateId": template_id, "format": format},
        )
        response.raise_for_status()
        return response.json()

    async def get_composition(self, ehr_id: str, composition_uid: str) -> dict[str, Any]:
        """Get a composition by UID."""
        client = await self._get_client()
        response = await client.get(f"/openehr/v1/ehr/{ehr_id}/composition/{composition_uid}")
        response.raise_for_status()
        return response.json()

    async def execute_aql(
        self,
        query: str,
        parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute an AQL query."""
        client = await self._get_client()
        payload: dict[str, Any] = {"q": query}
        if parameters:
            payload["query_parameters"] = parameters

        response = await client.post("/openehr/v1/query/aql", json=payload)
        response.raise_for_status()
        return response.json()

    async def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates."""
        client = await self._get_client()
        response = await client.get("/openehr/v1/definition/template/adl1.4")
        response.raise_for_status()
        return response.json()

    async def upload_template(self, template_content: str) -> dict[str, Any]:
        """Upload an operational template (OPT)."""
        client = await self._get_client()
        response = await client.post(
            "/openehr/v1/definition/template/adl1.4",
            content=template_content,
            headers={
                "Content-Type": "application/xml",
                "Accept": "application/json, application/xml",
            }
        )
        response.raise_for_status()
        # EHRBase may return empty response or XML on success
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return {"status": "uploaded"}

    async def get_template_example(
        self, template_id: str, format: str = "FLAT"
    ) -> dict[str, Any]:
        """Get an example composition for a template."""
        client = await self._get_client()
        response = await client.get(
            f"/openehr/v1/definition/template/adl1.4/{template_id}/example",
            params={"format": format},
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
ehrbase_client = EHRBaseClient()
