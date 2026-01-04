#!/usr/bin/env python3
"""Upload openEHR templates to EHRBase.

Usage:
    python scripts/upload_templates.py [--check-only]

This script uploads all OPT templates from the templates/ directory to EHRBase.
Run this after starting EHRBase to ensure all required templates are available.
"""

import asyncio
import sys
from pathlib import Path

import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings


async def list_templates(client: httpx.AsyncClient) -> list[str]:
    """List existing templates in EHRBase."""
    response = await client.get("/openehr/v1/definition/template/adl1.4")
    if response.status_code == 200:
        templates = response.json()
        return [t.get("template_id", "") for t in templates]
    return []


async def upload_template(client: httpx.AsyncClient, template_path: Path) -> bool:
    """Upload a single template to EHRBase."""
    template_content = template_path.read_text()
    template_id = template_path.stem  # filename without extension

    print(f"  Uploading {template_id}...")

    response = await client.post(
        "/openehr/v1/definition/template/adl1.4",
        content=template_content,
        headers={"Content-Type": "application/xml"},
    )

    if response.status_code in (200, 201, 204):
        print(f"  ✓ {template_id} uploaded successfully")
        return True
    elif response.status_code == 409:
        print(f"  ○ {template_id} already exists")
        return True
    else:
        print(f"  ✗ {template_id} failed: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"    Error: {error_detail}")
        except Exception:
            print(f"    Response: {response.text[:500]}")
        return False


async def main(check_only: bool = False):
    """Upload all templates to EHRBase."""
    templates_dir = Path(__file__).parent.parent / "templates"

    if not templates_dir.exists():
        print(f"Templates directory not found: {templates_dir}")
        sys.exit(1)

    template_files = list(templates_dir.glob("*.opt"))
    if not template_files:
        print("No .opt template files found")
        sys.exit(0)

    print(f"Found {len(template_files)} template(s)")
    print(f"EHRBase URL: {settings.ehrbase_url}")
    print()

    auth = None
    if settings.ehrbase_user and settings.ehrbase_password:
        auth = httpx.BasicAuth(settings.ehrbase_user, settings.ehrbase_password)

    async with httpx.AsyncClient(base_url=settings.ehrbase_url, auth=auth) as client:
        # Check EHRBase connectivity
        try:
            response = await client.get("/ehrbase/rest/status")
            if response.status_code != 200:
                print(f"EHRBase not ready: {response.status_code}")
                sys.exit(1)
            print("EHRBase is ready")
        except httpx.ConnectError:
            print("Cannot connect to EHRBase")
            sys.exit(1)

        # List existing templates
        existing = await list_templates(client)
        print(f"Existing templates: {len(existing)}")
        for t in existing:
            print(f"  - {t}")
        print()

        if check_only:
            print("Check only mode - not uploading")
            return

        # Upload templates
        print("Uploading templates...")
        success_count = 0
        for template_path in template_files:
            if await upload_template(client, template_path):
                success_count += 1

        print()
        print(f"Uploaded {success_count}/{len(template_files)} templates")


if __name__ == "__main__":
    check_only = "--check-only" in sys.argv
    asyncio.run(main(check_only))
