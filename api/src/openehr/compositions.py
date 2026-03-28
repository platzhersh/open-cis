"""Composition building helpers using oehrpy SDK."""

from datetime import UTC, datetime
from typing import Any

from openehr_sdk.templates import VitalSignsBuilder

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
) -> dict[str, Any]:
    """Build an adverse reaction FLAT composition.

    Returns a FLAT dict ready to submit to EHRBase.
    """
    now = datetime.now(UTC).isoformat()
    prefix = "adverse_reaction_list"
    # The template nests the evaluation inside a SECTION archetype
    eval_prefix = (
        f"{prefix}/allergies_and_adverse_reactions/adverse_reaction_risk:0"
    )

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
        # Template renames at0002 "Substance/Agent" to "Causative agent"
        f"{eval_prefix}/causative_agent": substance,
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
            reaction_prefix = f"{eval_prefix}/reaction_event:{i}"

            # Manifestation is required - raise clear error if missing
            if "manifestation" not in reaction:
                raise ValueError(
                    f"Missing required 'manifestation' key in reaction at index {i} "
                    f"(reaction_prefix: {reaction_prefix}). Reaction data: {reaction}"
                )

            flat[f"{reaction_prefix}/manifestation:0"] = reaction[
                "manifestation"
            ]

            sev = reaction.get("severity", "moderate")
            sev_code, sev_value = _SEVERITY_CODES.get(
                sev, ("at0092", "Moderate")
            )
            flat[f"{reaction_prefix}/severity_of_reaction|code"] = sev_code
            flat[f"{reaction_prefix}/severity_of_reaction|value"] = sev_value
            flat[f"{reaction_prefix}/severity_of_reaction|terminology"] = "local"

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
) -> dict[str, Any]:
    """Build a 'No Known Allergies' FLAT composition.

    Uses the exclusion_global archetype to explicitly declare NKA.
    """
    now = datetime.now(UTC).isoformat()
    prefix = "adverse_reaction_list"
    # The exclusion_global is nested inside SECTION.adhoc within the SECTION
    excl_prefix = (
        f"{prefix}/allergies_and_adverse_reactions/ad_hoc_heading/exclusion_global:0"
    )

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
        f"{excl_prefix}/global_exclusion_of_adverse_reactions": (
            "No known allergies"
        ),
        f"{excl_prefix}/language|code": "en",
        f"{excl_prefix}/language|terminology": "ISO_639-1",
        f"{excl_prefix}/encoding|code": "UTF-8",
        f"{excl_prefix}/encoding|terminology": "IANA_character-sets",
    }