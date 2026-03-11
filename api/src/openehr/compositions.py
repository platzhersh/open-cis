"""Composition building helpers using oehrpy SDK."""

from datetime import UTC, datetime
from typing import Any

from openehr_sdk.templates import VitalSignsBuilder

VITAL_SIGNS_TEMPLATE_ID = VitalSignsBuilder.template_id

# Template ID for adverse reaction list
# This uses a manual FLAT composition since oehrpy may not have a dedicated builder
ADVERSE_REACTION_TEMPLATE_ID = "Open CIS - Adverse Reaction List.v1"


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

    flat: dict[str, Any] = {
        # Composition context
        f"{prefix}/context/start_time": now,
        f"{prefix}/context/setting|code": "238",
        f"{prefix}/context/setting|value": "other care",
        f"{prefix}/context/setting|terminology": "openehr",
        f"{prefix}/category|code": "431",
        f"{prefix}/category|value": "persistent",
        f"{prefix}/category|terminology": "openehr",
        f"{prefix}/language|code": "en",
        f"{prefix}/language|terminology": "ISO_639-1",
        f"{prefix}/territory|code": "US",
        f"{prefix}/territory|terminology": "ISO_3166-1",
        f"{prefix}/composer|name": composer_name,
        # Adverse reaction evaluation
        f"{prefix}/adverse_reaction_risk:0/substance|value": substance,
        f"{prefix}/adverse_reaction_risk:0/status|code": status,
        f"{prefix}/adverse_reaction_risk:0/status|value": status,
        f"{prefix}/adverse_reaction_risk:0/criticality|code": criticality,
        f"{prefix}/adverse_reaction_risk:0/criticality|value": criticality,
        f"{prefix}/adverse_reaction_risk:0/category|code": category,
        f"{prefix}/adverse_reaction_risk:0/category|value": category,
        f"{prefix}/adverse_reaction_risk:0/reaction_type|code": reaction_type,
        f"{prefix}/adverse_reaction_risk:0/reaction_type|value": reaction_type,
        f"{prefix}/adverse_reaction_risk:0/language|code": "en",
        f"{prefix}/adverse_reaction_risk:0/language|terminology": "ISO_639-1",
        f"{prefix}/adverse_reaction_risk:0/encoding|code": "UTF-8",
        f"{prefix}/adverse_reaction_risk:0/encoding|terminology": "IANA_character-sets",
    }

    if onset_date:
        flat[f"{prefix}/adverse_reaction_risk:0/onset_of_last_reaction|value"] = (
            onset_date.isoformat()
        )

    if comment:
        flat[f"{prefix}/adverse_reaction_risk:0/comment|value"] = comment

    # Add reaction events
    if reactions:
        for i, reaction in enumerate(reactions):
            reaction_prefix = (
                f"{prefix}/adverse_reaction_risk:0/reaction:{i}"
            )
            flat[f"{reaction_prefix}/manifestation:0|value"] = reaction[
                "manifestation"
            ]
            flat[f"{reaction_prefix}/severity|code"] = reaction.get(
                "severity", "moderate"
            )
            flat[f"{reaction_prefix}/severity|value"] = reaction.get(
                "severity", "moderate"
            )
            flat[f"{reaction_prefix}/certainty|code"] = reaction.get(
                "certainty", "suspected"
            )
            flat[f"{reaction_prefix}/certainty|value"] = reaction.get(
                "certainty", "suspected"
            )

            if reaction.get("onset_date"):
                onset = reaction["onset_date"]
                flat[f"{reaction_prefix}/onset_of_reaction|value"] = (
                    onset.isoformat() if isinstance(onset, datetime) else str(onset)
                )

            if reaction.get("description"):
                flat[f"{reaction_prefix}/reaction_description|value"] = reaction[
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

    return {
        f"{prefix}/context/start_time": now,
        f"{prefix}/context/setting|code": "238",
        f"{prefix}/context/setting|value": "other care",
        f"{prefix}/context/setting|terminology": "openehr",
        f"{prefix}/category|code": "431",
        f"{prefix}/category|value": "persistent",
        f"{prefix}/category|terminology": "openehr",
        f"{prefix}/language|code": "en",
        f"{prefix}/language|terminology": "ISO_639-1",
        f"{prefix}/territory|code": "US",
        f"{prefix}/territory|terminology": "ISO_3166-1",
        f"{prefix}/composer|name": composer_name,
        # Exclusion global - NKA
        f"{prefix}/exclusion_global:0/global_exclusion_of_adverse_reactions|value": (
            "No known allergies"
        ),
        f"{prefix}/exclusion_global:0/language|code": "en",
        f"{prefix}/exclusion_global:0/language|terminology": "ISO_639-1",
        f"{prefix}/exclusion_global:0/encoding|code": "UTF-8",
        f"{prefix}/exclusion_global:0/encoding|terminology": "IANA_character-sets",
    }
