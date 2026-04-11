"""Composition enrichment: resolve coded display terms via terminology server.

Walks an openEHR composition JSON tree (STRUCTURED format) and populates
DV_CODED_TEXT.value fields that are missing or contain raw codes.
"""

import asyncio
import copy
import logging
import re
from typing import Any

from src.terminology.client import TerminologyClient
from src.terminology.systems import INTERNAL_TERMINOLOGIES, to_fhir_system

logger = logging.getLogger(__name__)

# Pattern that looks like a raw code rather than a display term
_RAW_CODE_PATTERN = re.compile(r"^\d[\d.\-]*$")


def _looks_like_raw_code(value: str) -> bool:
    """Return True if the value looks like a raw code rather than a display term."""
    return bool(_RAW_CODE_PATTERN.match(value))


def _collect_coded_text_nodes(
    data: Any, results: list[dict[str, Any]]
) -> None:
    """Recursively find DV_CODED_TEXT nodes that need display term enrichment."""
    if isinstance(data, dict):
        if data.get("_type") == "DV_CODED_TEXT":
            defining_code = data.get("defining_code", {})
            terminology_id = defining_code.get("terminology_id", {}).get("value", "")
            code_string = defining_code.get("code_string", "")
            current_value = data.get("value", "")

            if (
                terminology_id.lower() not in INTERNAL_TERMINOLOGIES
                and code_string
                and (not current_value or _looks_like_raw_code(current_value))
            ):
                fhir_system = to_fhir_system(terminology_id)
                if fhir_system:
                    results.append({
                        "node": data,
                        "system": fhir_system,
                        "code": code_string,
                    })

        for v in data.values():
            _collect_coded_text_nodes(v, results)
    elif isinstance(data, list):
        for item in data:
            _collect_coded_text_nodes(item, results)


async def enrich_composition(
    composition: dict[str, Any],
    client: TerminologyClient,
) -> dict[str, Any]:
    """Enrich DV_CODED_TEXT display terms in a composition (STRUCTURED format).

    Returns a deep copy with resolved display terms.
    The original composition is never modified.
    Failures are silent — unresolved codes keep their original value.
    """
    enriched = copy.deepcopy(composition)

    nodes: list[dict[str, Any]] = []
    _collect_coded_text_nodes(enriched, nodes)

    if not nodes:
        return enriched

    # Deduplicate lookups by (system, code)
    unique_pairs = list({(n["system"], n["code"]) for n in nodes})
    logger.debug("Enriching %d unique codes from %d nodes", len(unique_pairs), len(nodes))

    # Batch-resolve all unique codes concurrently
    results = await asyncio.gather(
        *[client.lookup(system, code) for system, code in unique_pairs],
        return_exceptions=True,
    )

    # Build lookup map
    resolved: dict[tuple[str, str], str | None] = {}
    for pair, result in zip(unique_pairs, results, strict=True):
        if isinstance(result, BaseException):
            logger.debug("Lookup failed for %s: %s", pair, result)
            resolved[pair] = None
        else:
            resolved[pair] = result

    # Apply resolved display terms
    for node_info in nodes:
        display = resolved.get((node_info["system"], node_info["code"]))
        if display:
            node_info["node"]["value"] = display

    return enriched


async def enrich_flat_composition(
    composition: dict[str, Any],
    client: TerminologyClient,
) -> dict[str, Any]:
    """Enrich coded values in a FLAT format composition.

    FLAT format stores codes as path|code, path|value, path|terminology pairs.
    This function looks for paths where |value is missing or looks like a raw code,
    and resolves it via the terminology server.

    Returns a copy with resolved display terms.
    """
    enriched = dict(composition)

    # Find paths with |code suffix that might need enrichment
    code_paths: dict[str, tuple[str, str]] = {}  # base_path → (terminology, code)
    for key, value in composition.items():
        if key.endswith("|code") and isinstance(value, str):
            base_path = key[: -len("|code")]
            terminology_key = f"{base_path}|terminology"
            value_key = f"{base_path}|value"

            terminology = composition.get(terminology_key, "")
            current_value = composition.get(value_key, "")

            if (
                terminology
                and terminology.lower() not in INTERNAL_TERMINOLOGIES
                and (
                    not current_value
                    or _looks_like_raw_code(str(current_value))
                    or str(current_value) == value  # value == code means unresolved
                )
            ):
                fhir_system = to_fhir_system(terminology)
                if fhir_system:
                    code_paths[base_path] = (fhir_system, value)

    if not code_paths:
        return enriched

    unique_pairs = list(set(code_paths.values()))
    results = await asyncio.gather(
        *[client.lookup(system, code) for system, code in unique_pairs],
        return_exceptions=True,
    )

    resolved: dict[tuple[str, str], str | None] = {}
    for pair, result in zip(unique_pairs, results, strict=True):
        if isinstance(result, BaseException):
            resolved[pair] = None
        else:
            resolved[pair] = result

    for base_path, pair in code_paths.items():
        display = resolved.get(pair)
        if display:
            enriched[f"{base_path}|value"] = display

    return enriched
