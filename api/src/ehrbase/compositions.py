"""Composition CRUD operations for EHRBase."""

from typing import Any

from src.ehrbase.client import ehrbase_client


async def create_composition(
    ehr_id: str,
    template_id: str,
    composition_data: dict[str, Any],
    format: str = "FLAT"
) -> dict[str, Any]:
    """Create a new composition in an EHR."""
    return await ehrbase_client.create_composition(
        ehr_id=ehr_id,
        template_id=template_id,
        composition=composition_data,
        format=format
    )


async def get_composition(ehr_id: str, composition_uid: str) -> dict[str, Any]:
    """Get a composition by its UID."""
    return await ehrbase_client.get_composition(ehr_id, composition_uid)


async def update_composition(
    ehr_id: str,
    composition_uid: str,
    template_id: str,
    composition_data: dict[str, Any],
    format: str = "FLAT"
) -> dict[str, Any]:
    """Update an existing composition."""
    client = await ehrbase_client._get_client()
    response = await client.put(
        f"/ehr/{ehr_id}/composition/{composition_uid}",
        json=composition_data,
        headers={
            "Prefer": "return=representation",
            "Content-Type": "application/json"
        },
        params={"templateId": template_id, "format": format},
    )
    response.raise_for_status()
    return response.json()


async def delete_composition(ehr_id: str, composition_uid: str) -> None:
    """Delete a composition."""
    client = await ehrbase_client._get_client()
    response = await client.delete(f"/ehr/{ehr_id}/composition/{composition_uid}")
    response.raise_for_status()
