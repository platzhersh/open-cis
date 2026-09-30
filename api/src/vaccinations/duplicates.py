"""Detect probable duplicate vaccination records (same vaccine + same date)."""

from collections import defaultdict

from src.vaccinations.models import VaccinationRecord


def find_duplicate_groups(
    records: list[VaccinationRecord],
) -> list[list[VaccinationRecord]]:
    groups: dict[tuple[str, str], list[VaccinationRecord]] = defaultdict(list)
    for r in records:
        groups[r.duplicate_key].append(r)
    return [g for g in groups.values() if len(g) > 1]
