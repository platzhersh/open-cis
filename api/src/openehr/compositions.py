"""Composition building helpers using oehrpy SDK."""

from datetime import datetime
from typing import Any

from openehr_sdk.templates import VitalSignsBuilder

VITAL_SIGNS_TEMPLATE_ID = VitalSignsBuilder.template_id


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
