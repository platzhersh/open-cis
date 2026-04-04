"""Template management for EHRBase."""

import logging
from pathlib import Path
from typing import Any

import aiofiles
import httpx
from openehr_sdk.client import EHRBaseError

from src.ehrbase.client import ehrbase_client

logger = logging.getLogger(__name__)

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


async def ensure_templates_registered() -> dict[str, bool]:
    """
    Ensure all required templates are registered in EHRBase.

    Called during API startup. Returns a dict mapping template_id to success status.
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

    # Upload all required templates (always re-upload to keep in sync)
    for template_id in REQUIRED_TEMPLATES:
        template_file = templates_dir / f"{template_id}.opt"

        if not template_file.exists():
            logger.warning(f"Template file not found: {template_file}")
            results[template_id] = False
            continue

        # Always upload to ensure the template matches the repo version.
        # EHRBase returns 409 if the template already exists and is identical,
        # which upload_template_file handles gracefully.
        logger.info(f"Uploading template {template_id}...")
        try:
            async with aiofiles.open(template_file, encoding="utf-8") as f:
                template_content = await f.read()
            results[template_id] = await upload_template_file(template_id, template_content)
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
