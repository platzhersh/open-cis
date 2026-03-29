"""Dynamic FLAT path resolver using EHRBase web templates.

Instead of hardcoding FLAT path IDs (which depend on the exact template
version uploaded to EHRBase), this module discovers the correct IDs by
fetching the web template at runtime and searching for nodes by archetype
node ID (at-code) or RM type.
"""

import logging
from typing import Any

from src.ehrbase.client import ehrbase_client

logger = logging.getLogger(__name__)

# Cache: template_id -> resolved paths dict
_cache: dict[str, dict[str, str]] = {}


def _find_node_by_at_code(
    tree: dict[str, Any],
    at_code: str,
    parent_at_code: str | None = None,
) -> dict[str, Any] | None:
    """Find a node in the web template tree by its archetype node ID."""
    aql_path = tree.get("aqlPath", "") or ""

    # Check if this node matches
    if at_code in aql_path:
        # If parent constraint specified, check parent is in the path too
        if parent_at_code is None or parent_at_code in aql_path:
            return tree

    for child in tree.get("children", []):
        result = _find_node_by_at_code(child, at_code, parent_at_code)
        if result:
            return result

    return None


def _find_node_by_id_pattern(
    tree: dict[str, Any],
    id_contains: str,
    rm_type: str | None = None,
) -> dict[str, Any] | None:
    """Find a node in the web template tree by partial ID match."""
    node_id = tree.get("id", "")

    if id_contains in node_id:
        if rm_type is None or tree.get("rmType", "") == rm_type:
            return tree

    for child in tree.get("children", []):
        result = _find_node_by_id_pattern(child, id_contains, rm_type)
        if result:
            return result

    return None


def _collect_all_ids(tree: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """Collect all node IDs with their full paths for debugging."""
    node_id = tree.get("id", "")
    rm_type = tree.get("rmType", "")
    current = f"{prefix}/{node_id}" if prefix else node_id

    result = {}
    if node_id:
        result[current] = rm_type

    for child in tree.get("children", []):
        result.update(_collect_all_ids(child, current))

    return result


def _find_child_id(node: dict[str, Any], at_code: str) -> str | None:
    """Find a direct or nested child's ID by its at-code in the aqlPath."""
    for child in node.get("children", []):
        aql = child.get("aqlPath", "")
        if at_code in aql:
            return child.get("id")
        # Recurse
        result = _find_child_id(child, at_code)
        if result:
            return result
    return None


async def resolve_adverse_reaction_paths(
    template_id: str,
) -> dict[str, str]:
    """Resolve FLAT path IDs for the adverse reaction template.

    Returns a dict with keys like 'severity', 'exclusion_statement', etc.
    mapped to the actual web template IDs.
    """
    if template_id in _cache:
        return _cache[template_id]

    try:
        web_template = await ehrbase_client.get_web_template(template_id)
    except Exception as e:
        logger.warning(f"Could not fetch web template for {template_id}: {e}")
        return _get_defaults()

    tree = (
        web_template.get("webTemplate", {}).get("tree")
        or web_template.get("tree")
    )
    if not tree:
        logger.warning(f"No tree found in web template for {template_id}")
        return _get_defaults()

    # Collect all paths for debugging
    all_ids = _collect_all_ids(tree)
    logger.info(f"Web template has {len(all_ids)} nodes")

    paths: dict[str, str] = {}

    # Find the exclusion_global evaluation node
    excl_node = _find_node_by_id_pattern(tree, "exclusion", "EVALUATION")
    if excl_node:
        paths["exclusion_global_id"] = excl_node.get("id", "exclusion_global")
        # Find the exclusion statement element within it
        stmt_id = _find_child_id(excl_node, "at0002")
        if stmt_id:
            paths["exclusion_statement_id"] = stmt_id
        else:
            # Try searching by pattern
            for child in excl_node.get("children", []):
                cid = child.get("id", "")
                if "exclusion" in cid or "statement" in cid:
                    paths["exclusion_statement_id"] = cid
                    break
    else:
        logger.warning("Could not find exclusion_global node in web template")

    # Find the ad_hoc_heading section (between section and exclusion)
    adhoc_node = _find_node_by_id_pattern(tree, "ad_hoc", "SECTION")
    if adhoc_node:
        paths["ad_hoc_heading_id"] = adhoc_node.get("id", "ad_hoc_heading")

    # Find the adverse_reaction_risk evaluation node
    reaction_node = _find_node_by_id_pattern(
        tree, "adverse_reaction", "EVALUATION"
    )
    if reaction_node:
        paths["adverse_reaction_id"] = reaction_node.get(
            "id", "adverse_reaction_risk"
        )

        # Find the severity element within reaction_event cluster
        sev_id = _find_child_id(reaction_node, "at0089")
        if sev_id:
            paths["severity_id"] = sev_id

        # Find the reaction_event cluster
        event_id = _find_child_id(reaction_node, "at0009")
        if event_id:
            paths["reaction_event_id"] = event_id

        # Find the manifestation element
        manif_id = _find_child_id(reaction_node, "at0011")
        if manif_id:
            paths["manifestation_id"] = manif_id

        # Find the substance/causative agent element
        subst_id = _find_child_id(reaction_node, "at0002")
        if subst_id:
            paths["substance_id"] = subst_id

    # Find the section node
    section_node = _find_node_by_id_pattern(
        tree, "allergies", "SECTION"
    )
    if section_node:
        paths["section_id"] = section_node.get(
            "id", "allergies_and_adverse_reactions"
        )

    logger.info(f"Resolved FLAT paths for {template_id}: {paths}")

    # Cache the result
    _cache[template_id] = paths
    return paths


def _get_defaults() -> dict[str, str]:
    """Return default path IDs (current best guesses)."""
    return {
        "exclusion_global_id": "exclusion_global",
        "exclusion_statement_id": "global_exclusion_of_adverse_reactions",
        "ad_hoc_heading_id": "ad_hoc_heading",
        "adverse_reaction_id": "adverse_reaction_risk",
        "severity_id": "severity_of_reaction",
        "reaction_event_id": "reaction_event",
        "manifestation_id": "manifestation",
        "substance_id": "causative_agent",
        "section_id": "allergies_and_adverse_reactions",
    }


def clear_cache() -> None:
    """Clear the path resolution cache."""
    _cache.clear()
