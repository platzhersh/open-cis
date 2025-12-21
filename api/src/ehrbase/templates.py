"""Template management for EHRBase."""

from typing import Any

from src.ehrbase.client import ehrbase_client


async def list_templates() -> list[dict[str, Any]]:
    """List all available operational templates."""
    return await ehrbase_client.list_templates()


async def upload_template(template_content: str) -> dict[str, Any]:
    """Upload an operational template (OPT) to EHRBase."""
    return await ehrbase_client.upload_template(template_content)


async def get_template_example(template_id: str, format: str = "FLAT") -> dict[str, Any]:
    """Get an example composition for a template."""
    client = await ehrbase_client._get_client()
    response = await client.get(
        f"/definition/template/adl1.4/{template_id}/example",
        params={"format": format}
    )
    response.raise_for_status()
    return response.json()
