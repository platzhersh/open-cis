"""Unit tests for CH VACD ↔ openEHR vaccination mapping (no EHRBase needed)."""

import io
import json
import zipfile
from pathlib import Path

import pytest

from src.vaccinations.duplicates import find_duplicate_groups
from src.vaccinations.exporter import record_to_bundle
from src.vaccinations.flat import build_vaccination_flat, parse_vaccination_flat
from src.vaccinations.parser import VacdParseError, parse_bundle
from src.vaccinations.xdm import read_xdm_zip

FIX = Path(__file__).parent.parent / "fixtures" / "ch-vacd"


def _bundles() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(FIX.glob("DOC*.JSON"))]


def build_xdm_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.write(FIX / "METADATA.XML", "IHE_XDM/SUBSET01/METADATA.XML")
        for p in FIX.glob("DOC*.JSON"):
            zf.write(p, f"IHE_XDM/SUBSET01/{p.name}")
        zf.writestr("IHE_XDM/SUBSET01/DOC00099.PDF", b"%PDF")
    return buf.getvalue()


def test_parse_all_fixtures() -> None:
    recs = [parse_bundle(b) for b in _bundles()]
    assert len(recs) == 6
    first = recs[0]
    assert first.vaccine.code == "450"
    assert first.target_diseases[0].code == "34015007"
    assert first.dose_number == 1
    assert first.organization_name == "Praxis Beispiel"


def test_placeholders_become_none_and_patient_author_kept() -> None:
    rec = parse_bundle(_bundles()[5])
    assert rec.lot_number is None
    assert rec.performer_name is None
    assert rec.organization_name is None
    assert rec.author_kind == "patient"


def test_flat_round_trip() -> None:
    for b in _bundles():
        rec = parse_bundle(b)
        back = parse_vaccination_flat(build_vaccination_flat(rec))
        assert back is not None
        assert back.vaccine == rec.vaccine
        assert back.target_diseases == rec.target_diseases
        assert (back.dose_number, back.lot_number) == (rec.dose_number, rec.lot_number)
        assert back.occurrence == rec.occurrence
        assert back.author_kind == rec.author_kind
        assert back.identifier == rec.identifier


def test_export_round_trip_is_semantically_equal() -> None:
    for b in _bundles():
        rec = parse_bundle(b)
        again = parse_bundle(record_to_bundle(rec))
        assert again.vaccine == rec.vaccine
        assert again.target_diseases == rec.target_diseases
        assert again.dose_number == rec.dose_number
        assert again.occurrence == rec.occurrence
        assert again.lot_number == rec.lot_number
        assert again.author_kind == rec.author_kind
        assert again.identifier == rec.identifier


def test_duplicates_detected() -> None:
    groups = find_duplicate_groups([parse_bundle(b) for b in _bundles()])
    assert len(groups) == 1
    assert {r.dose_number for r in groups[0]} == {3, 1}


def test_xdm_reader_picks_vacd_and_skips_others() -> None:
    xdm = read_xdm_zip(build_xdm_zip())
    assert len(xdm.bundles) == 6
    assert xdm.skipped == ["DOC00099.PDF"]


def test_parse_rejects_non_bundle() -> None:
    with pytest.raises(VacdParseError):
        parse_bundle({"resourceType": "Patient"})
