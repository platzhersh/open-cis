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
    return [json.loads(p.read_text()) for p in sorted(FIX.glob("immunization-*.json"))]


def build_xdm_zip() -> bytes:
    """Assemble an XDM package (METADATA.XML + documents + a PDF) from fixtures."""
    ns = "urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0"
    scheme = "urn:uuid:a09d5840-386c-46f2-b5ad-9c3699a4309d"

    def obj(uri: str, fmt: str) -> str:
        return (
            f'<ExtrinsicObject><Slot name="URI"><ValueList><Value>{uri}</Value>'
            f'</ValueList></Slot><Classification classificationScheme="{scheme}" '
            f'nodeRepresentation="{fmt}"/></ExtrinsicObject>'
        )

    files = sorted(FIX.glob("immunization-*.json"))
    objs = "".join(
        obj(f"DOC{i:05d}.JSON", "urn:che:epr:ch-vacd:immunization-administration:2022")
        for i in range(1, len(files) + 1)
    ) + obj("DOC00099.PDF", "urn:ihe:iti:xds:2017:mimeTypeSufficient")
    meta = (
        f'<SubmitObjectsRequest xmlns="{ns}"><RegistryObjectList>{objs}'
        "</RegistryObjectList></SubmitObjectsRequest>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("IHE_XDM/SUBSET01/METADATA.XML", meta)
        for i, p in enumerate(files, 1):
            zf.write(p, f"IHE_XDM/SUBSET01/DOC{i:05d}.JSON")
        zf.writestr("IHE_XDM/SUBSET01/DOC00099.PDF", b"%PDF")
    return buf.getvalue()


def test_parse_all_fixtures() -> None:
    recs = [parse_bundle(b) for b in _bundles()]
    assert len(recs) == 16
    assert len({r.identifier for r in recs}) == 16  # Bundle.identifier is unique
    first = recs[0]
    assert first.vaccine.system.endswith("ch-vacd-swissmedic-cs")
    assert first.target_diseases and first.dose_number is not None


def test_placeholders_become_none_and_patient_author_kept() -> None:
    recs = [parse_bundle(b) for b in _bundles()]
    assert recs[0].lot_number is None  # "-" placeholder
    assert recs[2].lot_number == "UF3F411V"  # real lot kept
    assert all(r.performer_name is None for r in recs)
    assert all(r.author_kind == "patient" for r in recs)
    assert recs[15].organization_name is None  # org name "-"
    assert recs[0].organization_name == "Test Vaccination Site A"


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
    recs = [parse_bundle(b) for b in _bundles()]
    groups = find_duplicate_groups(recs)
    by_file = {id(r): i + 1 for i, r in enumerate(recs)}
    found = sorted(tuple(sorted(by_file[id(r)] for r in g)) for g in groups)
    assert found == [(5, 7), (6, 8), (10, 12), (11, 13)]


def test_xdm_reader_picks_vacd_and_skips_others() -> None:
    xdm = read_xdm_zip(build_xdm_zip())
    assert len(xdm.bundles) == 16
    assert xdm.skipped == ["DOC00099.PDF"]


def test_parse_rejects_non_bundle() -> None:
    with pytest.raises(VacdParseError):
        parse_bundle({"resourceType": "Patient"})
