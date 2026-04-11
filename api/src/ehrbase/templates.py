"""Template management for EHRBase."""

import hashlib
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import aiofiles
import httpx
from openehr_sdk.client import EHRBaseError

from src.ehrbase.client import ehrbase_client

logger = logging.getLogger(__name__)


def _xml_hash(xml_content: str) -> str:
    """Compute a hash of XML content using C14N (canonical XML) for deterministic comparison.

    This normalises whitespace, attribute order, and namespace declarations
    so that semantically identical documents produce the same hash, even if
    their raw text differs.
    """
    try:
        canonical = ET.canonicalize(xml_data=xml_content)
        return hashlib.sha256(canonical.encode()).hexdigest()
    except ET.ParseError:
        # Fallback: hash the stripped raw text if XML parsing fails
        return hashlib.sha256(xml_content.strip().encode()).hexdigest()

# Web template cache status, populated by warm_web_template_cache()
_web_template_cache_status: dict[str, bool] = {}

# Template files that must be registered in EHRBase
# Filename must be "{template_id}.opt"
REQUIRED_TEMPLATES = [
    "IDCR - Vital Signs Encounter.v1",
    "Open CIS - Adverse Reaction List.v1",
]


async def list_templates() -> list[dict[str, Any]]:
    """List all available operational templates."""
    return await ehrbase_client.list_templates()


async def upload_template(template_content: str) -> dict[str, Any]:
    """Upload an operational template (OPT) to EHRBase."""
    return await ehrbase_client.upload_template(template_content)


async def get_registered_template_ids() -> list[str]:
    """Get list of template IDs registered in EHRBase."""
    try:
        templates = await list_templates()
        return [t.get("template_id", "") for t in templates]
    except Exception as e:
        logger.warning(f"Failed to list EHRBase templates: {e}")
        return []


async def upload_template_file(template_id: str, template_content: str) -> bool:
    """Upload a single template to EHRBase."""
    try:
        await upload_template(template_content)
        logger.info(f"Template {template_id} uploaded successfully")
        return True
    except httpx.HTTPStatusError as e:
        # 409 Conflict means template already exists - that's OK
        if e.response.status_code == 409:
            logger.info(f"Template {template_id} already exists")
            return True
        logger.error(f"Failed to upload template {template_id}: HTTP {e.response.status_code}")
        return False
    except EHRBaseError as e:
        # oehrpy may wrap 409 as EHRBaseError; check message for conflict
        if "409" in str(e) or "conflict" in str(e).lower():
            logger.info(f"Template {template_id} already exists")
            return True
        logger.error(f"Failed to upload template {template_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to upload template {template_id}: {e}")
        return False


async def _sync_template(template_id: str, local_content: str) -> bool:
    """Sync a single template: skip if unchanged, update or upload as needed.

    Returns True if the template is now in sync, False on failure.
    """
    # Try to fetch the currently registered OPT from EHRBase
    try:
        remote_opt = await ehrbase_client.get_template_opt(template_id)
    except Exception as e:
        logger.warning(f"Could not fetch existing OPT for {template_id}: {e}")
        remote_opt = None

    if remote_opt is not None:
        # Template exists in EHRBase — compare with local version
        local_hash = _xml_hash(local_content)
        remote_hash = _xml_hash(remote_opt)

        if local_hash == remote_hash:
            logger.info(f"Template {template_id} is up to date")
            return True

        # Template has changed — attempt to update via PUT
        logger.info(f"Template {template_id} has changed, updating...")
        try:
            updated = await ehrbase_client.update_template_opt(template_id, local_content)
            if updated:
                logger.info(f"Template {template_id} updated successfully")
                return True
            logger.warning(
                f"EHRBase rejected PUT update for {template_id}, "
                "template may be in use by existing compositions"
            )
            return False
        except Exception as e:
            logger.warning(f"Could not update template {template_id}: {e}")
            return False
    else:
        # Template not yet registered — upload it
        return await upload_template_file(template_id, local_content)


async def ensure_templates_registered() -> dict[str, bool]:
    """
    Ensure all required templates are registered in EHRBase.

    Called during API startup. For each template:
    - If not registered: uploads it.
    - If registered and unchanged: skips it.
    - If registered and changed: attempts to update via PUT.

    Returns a dict mapping template_id to success status.
    """
    results: dict[str, bool] = {}

    logger.info("Checking openEHR templates...")

    if not REQUIRED_TEMPLATES:
        logger.info("No required templates configured")
        return results

    # Find templates directory (relative to this file)
    templates_dir = Path(__file__).parent.parent.parent / "templates"

    if not templates_dir.exists():
        logger.warning(f"Templates directory not found: {templates_dir}")
        return results

    # Check what's already registered
    try:
        existing = await get_registered_template_ids()
        logger.info(f"EHRBase has {len(existing)} registered template(s)")
    except Exception as e:
        logger.warning(f"Could not connect to EHRBase to check templates: {e}")
        return results

    for template_id in REQUIRED_TEMPLATES:
        template_file = templates_dir / f"{template_id}.opt"

        if not template_file.exists():
            logger.warning(f"Template file not found: {template_file}")
            results[template_id] = False
            continue

        try:
            async with aiofiles.open(template_file, encoding="utf-8") as f:
                local_content = await f.read()
            results[template_id] = await _sync_template(template_id, local_content)
        except Exception as e:
            logger.error(f"Failed to read template file {template_file}: {e}")
            results[template_id] = False

    # Summary
    successful = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    if failed:
        logger.warning(f"Template check complete: {successful} OK, {failed} failed")
    else:
        total_templates = len(REQUIRED_TEMPLATES)
        logger.info(f"Template check complete: {successful}/{total_templates} templates ready")

    return results


async def warm_web_template_cache() -> dict[str, bool]:
    """Fetch and cache Web Templates for all required templates.

    Called during API startup after templates are registered.
    Web Templates provide the authoritative FLAT paths for composition building.
    See ADR-0009: oehrpy Web Template Integration for FLAT Path Sourcing.

    Returns a dict mapping template_id to success status.
    """
    global _web_template_cache_status
    results: dict[str, bool] = {}

    for template_id in REQUIRED_TEMPLATES:
        try:
            web_template = await ehrbase_client.get_web_template(template_id)
            if "error" in web_template:
                logger.warning(
                    f"Could not fetch web template for {template_id}: {web_template['error']}"
                )
                results[template_id] = False
            else:
                logger.info(f"Web template cached for {template_id}")
                results[template_id] = True
        except Exception as e:
            logger.warning(f"Failed to fetch web template for {template_id}: {e}")
            results[template_id] = False

    _web_template_cache_status = results
    successful = sum(1 for v in results.values() if v)
    logger.info(f"Web template cache: {successful}/{len(REQUIRED_TEMPLATES)} templates cached")

    return results


def get_web_template_cache_status() -> dict[str, bool]:
    """Return the current web template cache status per template_id."""
    return _web_template_cache_status
