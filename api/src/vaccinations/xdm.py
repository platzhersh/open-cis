"""Reader for IHE XDM packages (EPD exports) containing CH VACD documents."""

import io
import json
import logging
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

VACD_FORMAT_CODE = "urn:che:epr:ch-vacd:immunization-administration:2022"
_NS = {"rim": "urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0"}


@dataclass
class XdmContents:
    bundles: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _vacd_uris(metadata_xml: bytes) -> tuple[list[str], list[str]]:
    """Return (vacd document URIs, other document URIs) from METADATA.XML."""
    root = ET.fromstring(metadata_xml)  # noqa: S314 - trusted-size local archive
    vacd: list[str] = []
    other: list[str] = []
    for obj in root.iter(f"{{{_NS['rim']}}}ExtrinsicObject"):
        uri = None
        for slot in obj.findall("rim:Slot", _NS):
            if slot.get("name") == "URI":
                uri = slot.findtext("rim:ValueList/rim:Value", namespaces=_NS)
        fmt = None
        for cls in obj.findall("rim:Classification", _NS):
            if cls.get("classificationScheme", "").endswith(
                "a09d5840-386c-46f2-b5ad-9c3699a4309d"
            ):
                fmt = cls.get("nodeRepresentation")
        if not uri:
            continue
        (vacd if fmt == VACD_FORMAT_CODE else other).append(uri)
    return vacd, other


def read_xdm_zip(data: bytes) -> XdmContents:
    """Extract CH VACD Bundles from an XDM zip; log and skip everything else."""
    result = XdmContents()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = {n.upper(): n for n in zf.namelist()}
        meta_name = next((n for u, n in names.items() if u.endswith("METADATA.XML")), None)
        if meta_name is None:
            raise ValueError("XDM package has no METADATA.XML")
        base = meta_name.rsplit("/", 1)[0] + "/" if "/" in meta_name else ""
        vacd, other = _vacd_uris(zf.read(meta_name))
        for uri in vacd:
            member = names.get((base + uri).upper())
            if member is None:
                result.skipped.append(f"{uri} (listed in metadata but missing)")
                continue
            result.bundles.append(json.loads(zf.read(member)))
        for uri in other:
            logger.info("XDM: skipping non-CH-VACD document %s", uri)
            result.skipped.append(uri)
    return result
