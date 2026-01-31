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


async def delete_composition(ehr_id: str, composition_uid: str) -> bool:
    """Delete a composition."""
    return await ehrbase_client.delete_composition(ehr_id, composition_uid)
