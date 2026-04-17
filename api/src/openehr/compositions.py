"""Composition building helpers using oehrpy SDK."""

from datetime import UTC, datetime
from typing import Any

from oehrpy.templates import VitalSignsBuilder

# VitalSignsBuilder FLAT path constants are sourced from the Web Template:
#   IDCR - Vital Signs Encounter.v1
# Retrieved from EHRBase 2.26.0 via:
#   GET /rest/openehr/v1/definition/template/adl1.4/{id}
#   Accept: application/openehr.wt+json
# See ADR-0009 and oehrpy ADR-0003 for derivation process.
VITAL_SIGNS_TEMPLATE_ID = VitalSignsBuilder.template_id

# Template ID for adverse reaction list
# This uses a manual FLAT composition since oehrpy may not have a dedicated builder
ADVERSE_REACTION_TEMPLATE_ID = "Open CIS - Adverse Reaction List.v1"

# Mappings from application enum values to openEHR local terminology at-codes
# Each maps to (at_code, display_text) tuples
_STATUS_CODES: dict[str, tuple[str, str]] = {
    "active": ("at0127", "Suspected"),
    "inactive": ("at0127", "Suspected"),
    "resolved": ("at0065", "Confirmed"),
    "refuted": ("at0065", "Confirmed"),
}

_CRITICALITY_CODES: dict[str, tuple[str, str]] = {
    "low": ("at0102", "Low"),
    "high": ("at0103", "High"),
    "indeterminate": ("at0124", "Indeterminate"),
}

_CATEGORY_CODES: dict[str, tuple[str, str]] = {
    "food": ("at0121", "Food"),
    "medication": ("at0122", "Medication"),
    "environment": ("at0123", "Other"),
    "other": ("at0123", "Other"),
}

_SEVERITY_CODES: dict[str, tuple[str, str]] = {
    "mild": ("at0093", "Mild"),
    "moderate": ("at0092", "Moderate"),
    "severe": ("at0090", "Severe"),
}


def build_vital_signs_flat(
    systolic: int | None = None,
    diastolic: int | None = None,
    pulse_rate: int | None = None,
    recorded_at: datetime | None = None,
    composer_name: str = "CIS System",
) -> dict[str, Any]:
    """Build a vital signs FLAT composition using oehrpy VitalSignsBuilder.

    Returns a validated FLAT dict ready to submit to EHRBase.
    """
    builder = VitalSignsBuilder(
        composer_name=composer_name,
        language="en",
        territory="US",
    )

    time = recorded_at.isoformat() if recorded_at else None

    if systolic is not None and diastolic is not None:
        builder.add_blood_pressure(
            systolic=float(systolic),
            diastolic=float(diastolic),
            time=time,
        )

    if pulse_rate is not None:
        builder.add_pulse(
            rate=float(pulse_rate),
            time=time,
        )

    return builder.build()


def build_adverse_reaction_flat(
    substance: str,
    category: str = "other",
    reaction_type: str = "unknown",
    criticality: str = "indeterminate",
    status: str = "active",
    onset_date: datetime | None = None,
    comment: str | None = None,
    reactions: list[dict[str, Any]] | None = None,
    composer_name: str = "CIS System",
    resolved_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build an adverse reaction FLAT composition.

    Args:
        resolved_paths: Optional dict of dynamically resolved FLAT IDs from
            the web template. If None, uses hardcoded defaults.

    Returns a FLAT dict ready to submit to EHRBase.
    """
    now = datetime.now(UTC).isoformat()
    prefix = "adverse_reaction_list"

    # Use dynamically resolved path IDs if available, otherwise defaults
    p = resolved_paths or {}
    section_id = p.get("section_id", "allergies_and_adverse_reactions")
    reaction_id = p.get("adverse_reaction_id", "adverse_reaction_risk")
    substance_id = p.get("substance_id", "causative_agent")
    reaction_event_id = p.get("reaction_event_id", "reaction_event")
    manifestation_id = p.get("manifestation_id", "manifestation")
    severity_id = p.get("severity_id", "severity_of_reaction")

    # The template nests the evaluation inside a SECTION archetype
    eval_prefix = f"{prefix}/{section_id}/{reaction_id}:0"

    status_code, status_value = _STATUS_CODES.get(
        status, ("at0127", "Suspected")
    )
    crit_code, crit_value = _CRITICALITY_CODES.get(
        criticality, ("at0124", "Indeterminate")
    )
    cat_code, cat_value = _CATEGORY_CODES.get(category, ("at0123", "Other"))

    flat: dict[str, Any] = {
        # Composition context
        f"{prefix}/context/start_time": now,
        f"{prefix}/context/setting|code": "238",
        f"{prefix}/context/setting|value": "other care",
        f"{prefix}/context/setting|terminology": "openehr",
        f"{prefix}/category|code": "433",
        f"{prefix}/category|value": "event",
        f"{prefix}/category|terminology": "openehr",
        f"{prefix}/language|code": "en",
        f"{prefix}/language|terminology": "ISO_639-1",
        f"{prefix}/territory|code": "US",
        f"{prefix}/territory|terminology": "ISO_3166-1",
        f"{prefix}/composer|name": composer_name,
        # Adverse reaction evaluation
        f"{eval_prefix}/{substance_id}": substance,
        f"{eval_prefix}/status|code": status_code,
        f"{eval_prefix}/status|value": status_value,
        f"{eval_prefix}/status|terminology": "local",
        f"{eval_prefix}/criticality|code": crit_code,
        f"{eval_prefix}/criticality|value": crit_value,
        f"{eval_prefix}/criticality|terminology": "local",
        f"{eval_prefix}/category|code": cat_code,
        f"{eval_prefix}/category|value": cat_value,
        f"{eval_prefix}/category|terminology": "local",
        f"{eval_prefix}/language|code": "en",
        f"{eval_prefix}/language|terminology": "ISO_639-1",
        f"{eval_prefix}/encoding|code": "UTF-8",
        f"{eval_prefix}/encoding|terminology": "IANA_character-sets",
    }

    if onset_date:
        flat[f"{eval_prefix}/onset_of_last_reaction"] = onset_date.isoformat()

    if comment:
        flat[f"{eval_prefix}/comment"] = comment

    # Add reaction events
    if reactions:
        for i, reaction in enumerate(reactions):
            reaction_prefix = f"{eval_prefix}/{reaction_event_id}:{i}"

            # Manifestation is required - raise clear error if missing
            if "manifestation" not in reaction:
                raise ValueError(
                    f"Missing required 'manifestation' key in reaction at index {i} "
                    f"(reaction_prefix: {reaction_prefix}). Reaction data: {reaction}"
                )

            flat[f"{reaction_prefix}/{manifestation_id}:0"] = reaction[
                "manifestation"
            ]

            sev = reaction.get("severity", "moderate")
            sev_code, sev_value = _SEVERITY_CODES.get(
                sev, ("at0092", "Moderate")
            )
            # Severity is a CHOICE type (DV_CODED_TEXT | DV_TEXT).
            # Use DV_CODED_TEXT with proper suffixes as that's the primary type.
            flat[f"{reaction_prefix}/{severity_id}|code"] = sev_code
            flat[f"{reaction_prefix}/{severity_id}|value"] = sev_value
            flat[f"{reaction_prefix}/{severity_id}|terminology"] = "local"

            if reaction.get("onset_date"):
                onset = reaction["onset_date"]
                flat[f"{reaction_prefix}/onset_of_reaction"] = (
                    onset.isoformat() if isinstance(onset, datetime) else str(onset)
                )

            if reaction.get("description"):
                flat[f"{reaction_prefix}/reaction_description"] = reaction[
                    "description"
                ]

    return flat


def build_nka_flat(
    composer_name: str = "CIS System",
    resolved_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a 'No Known Allergies' FLAT composition.

    Uses the exclusion_global archetype to explicitly declare NKA.

    Args:
        resolved_paths: Optional dict of dynamically resolved FLAT IDs from
            the web template. If None, uses hardcoded defaults.
    """
    now = datetime.now(UTC).isoformat()
    prefix = "adverse_reaction_list"

    # Use dynamically resolved path IDs if available, otherwise defaults
    p = resolved_paths or {}
    stmt_id = p.get("exclusion_statement_id", "global_exclusion_of_adverse_reactions")

    # Use the full FLAT prefix resolved from the web template tree walk.
    # This avoids hardcoding intermediate sections (like SECTION.adhoc) which
    # may differ between EHRBase versions.
    if "exclusion_flat_prefix" in p:
        excl_prefix = f"{prefix}/{p['exclusion_flat_prefix']}"
    else:
        # Fallback: assemble from individual IDs
        section_id = p.get("section_id", "allergies_and_adverse_reactions")
        adhoc_id = p.get("ad_hoc_heading_id", "ad_hoc_heading")
        excl_id = p.get("exclusion_global_id", "exclusion_global")
        excl_prefix = f"{prefix}/{section_id}/{adhoc_id}/{excl_id}"

    return {
        f"{prefix}/context/start_time": now,
        f"{prefix}/context/setting|code": "238",
        f"{prefix}/context/setting|value": "other care",
        f"{prefix}/context/setting|terminology": "openehr",
        f"{prefix}/category|code": "433",
        f"{prefix}/category|value": "event",
        f"{prefix}/category|terminology": "openehr",
        f"{prefix}/language|code": "en",
        f"{prefix}/language|terminology": "ISO_639-1",
        f"{prefix}/territory|code": "US",
        f"{prefix}/territory|terminology": "ISO_3166-1",
        f"{prefix}/composer|name": composer_name,
        # Exclusion global - NKA
        f"{excl_prefix}/{stmt_id}": "No known allergies",
        f"{excl_prefix}/language|code": "en",
        f"{excl_prefix}/language|terminology": "ISO_639-1",
        f"{excl_prefix}/encoding|code": "UTF-8",
        f"{excl_prefix}/encoding|terminology": "IANA_character-sets",
    }
