#!/usr/bin/env python3
"""Validate openEHR Operational Template (OPT) files.

Performs static validation of .opt XML files without requiring a running
EHRBase instance. Catches structural issues, invalid terminology codes,
and missing required elements before deployment.

Usage:
    python scripts/validate_templates.py [template_dir]

Exit codes:
    0 - All templates valid
    1 - One or more validation errors found
"""

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

# openEHR XML namespace
NS = "http://schemas.openehr.org/v1"
NS_MAP = {"oe": NS}

# Valid openEHR category codes (from openehr terminology, group "composition category")
# See: https://specifications.openehr.org/releases/TERM/latest/SupportTerminology.html
VALID_CATEGORY_CODES = {
    "431": "persistent",
    "433": "event",
    "451": "episodic",
}

# Valid openEHR setting codes (from openehr terminology, group "setting")
VALID_SETTING_CODES = {
    "225": "home",
    "227": "emergency care",
    "228": "primary medical care",
    "229": "primary nursing care",
    "230": "primary allied health care",
    "231": "midwifery care",
    "232": "secondary medical care",
    "233": "secondary nursing care",
    "234": "secondary allied health care",
    "235": "complementary health care",
    "236": "dental care",
    "237": "nursing home care",
    "238": "other care",
}

# Valid ISO 639-1 language codes (common subset)
VALID_LANGUAGE_CODES = {
    "en", "de", "es", "fr", "it", "pt", "nl", "sv", "no", "da", "fi",
    "zh", "ja", "ko", "ar", "ru", "pl", "cs", "tr", "el", "he", "nb",
    "nn", "sl", "hr", "sr", "bg", "ro", "hu", "sk", "uk", "ca", "eu",
    "gl", "fa", "hi", "th", "vi", "id", "ms",
}


@dataclass
class ValidationError:
    """A single validation error."""
    template_file: str
    message: str
    element_path: str = ""


@dataclass
class ValidationResult:
    """Result of validating one or more templates."""
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    templates_checked: int = 0

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def _find_text(element: ET.Element, path: str) -> str | None:
    """Find text content of a child element using namespace-aware path."""
    parts = path.split("/")
    current = element
    for part in parts:
        child = current.find(f"{{{NS}}}{part}")
        if child is None:
            return None
        current = child
    return current.text


def _find_all(element: ET.Element, tag: str) -> list[ET.Element]:
    """Find all descendants with a given tag (namespace-aware)."""
    return element.findall(f".//{{{NS}}}{tag}")


def validate_xml_wellformed(filepath: Path) -> list[ValidationError]:
    """Check that the file is well-formed XML."""
    errors: list[ValidationError] = []
    try:
        ET.parse(filepath)
    except ET.ParseError as e:
        errors.append(ValidationError(
            template_file=filepath.name,
            message=f"Malformed XML: {e}",
        ))
    return errors


def validate_template_structure(filepath: Path) -> list[ValidationError]:
    """Validate required top-level template structure."""
    errors: list[ValidationError] = []
    fname = filepath.name

    try:
        tree = ET.parse(filepath)
    except ET.ParseError:
        return []  # Already caught by wellformed check

    root = tree.getroot()

    # Must be a <template> root element
    expected_tag = f"{{{NS}}}template"
    if root.tag != expected_tag:
        errors.append(ValidationError(
            template_file=fname,
            message=f"Root element must be <template>, found <{root.tag}>",
        ))
        return errors

    # Required children: language, description, definition
    for required in ["language", "description", "definition"]:
        if root.find(f"{{{NS}}}{required}") is None:
            errors.append(ValidationError(
                template_file=fname,
                message=f"Missing required element: <{required}>",
                element_path=f"/template/{required}",
            ))

    # Template must have a concept (acts as template_id in many contexts)
    concept = root.find(f"{{{NS}}}concept")
    if concept is None or not (concept.text and concept.text.strip()):
        errors.append(ValidationError(
            template_file=fname,
            message="Missing or empty <concept> element (template identifier)",
            element_path="/template/concept",
        ))

    return errors


def validate_language_codes(filepath: Path) -> list[ValidationError]:
    """Validate that language codes are valid ISO 639-1."""
    errors: list[ValidationError] = []
    fname = filepath.name

    tree = ET.parse(filepath)
    root = tree.getroot()

    # Check top-level language
    lang_code = _find_text(root, "language/code_string")
    if lang_code and lang_code not in VALID_LANGUAGE_CODES:
        errors.append(ValidationError(
            template_file=fname,
            message=f"Invalid language code: '{lang_code}'",
            element_path="/template/language/code_string",
        ))

    return errors


def validate_terminology_codes(filepath: Path) -> tuple[list[ValidationError], list[ValidationError]]:
    """Validate openEHR terminology codes (category, setting, etc.)."""
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []
    fname = filepath.name

    tree = ET.parse(filepath)
    root = tree.getroot()
    definition = root.find(f"{{{NS}}}definition")
    if definition is None:
        return errors, warnings

    # Find all code_phrase-like structures and check known terminologies
    # Walk the tree looking for terminology_id + code_string pairs
    _check_code_phrases(definition, fname, errors, warnings)

    return errors, warnings


def _check_code_phrases(
    element: ET.Element,
    fname: str,
    errors: list[ValidationError],
    warnings: list[ValidationError],
    path: str = "",
) -> None:
    """Recursively check CodePhrase elements for valid terminology codes."""
    tag = element.tag.replace(f"{{{NS}}}", "")
    current_path = f"{path}/{tag}" if path else tag

    # Look for patterns like:
    #   <terminology_id><value>openehr</value></terminology_id>
    #   <code_string>431</code_string>
    terminology_id_el = element.find(f"{{{NS}}}terminology_id")
    code_string_el = element.find(f"{{{NS}}}code_string")

    if terminology_id_el is not None and code_string_el is not None:
        terminology_value = _find_text(element, "terminology_id/value")
        code_value = code_string_el.text

        if terminology_value == "openehr" and code_value:
            # Check if this is in a category context
            parent_tag = tag.lower()
            if parent_tag == "category" or "category" in current_path.lower():
                if code_value not in VALID_CATEGORY_CODES:
                    errors.append(ValidationError(
                        template_file=fname,
                        message=(
                            f"Invalid category code '{code_value}' "
                            f"(valid: {', '.join(f'{k}={v}' for k, v in VALID_CATEGORY_CODES.items())})"
                        ),
                        element_path=current_path,
                    ))
            elif parent_tag == "setting" or "setting" in current_path.lower():
                if code_value not in VALID_SETTING_CODES:
                    warnings.append(ValidationError(
                        template_file=fname,
                        message=(
                            f"Unrecognized setting code '{code_value}' in openehr terminology"
                        ),
                        element_path=current_path,
                    ))

    # Recurse into children
    for child in element:
        _check_code_phrases(child, fname, errors, warnings, current_path)


def validate_definition_rm_types(filepath: Path) -> list[ValidationError]:
    """Validate that rm_type_name values in the definition are recognized openEHR RM types."""
    errors: list[ValidationError] = []
    fname = filepath.name

    # Common openEHR Reference Model types found in OPTs
    known_rm_types = {
        # Composition / structure types
        "COMPOSITION", "SECTION", "OBSERVATION", "EVALUATION", "INSTRUCTION",
        "ACTION", "ADMIN_ENTRY", "CLUSTER", "ELEMENT", "HISTORY", "EVENT",
        "POINT_EVENT", "INTERVAL_EVENT", "ITEM_TREE", "ITEM_LIST", "ITEM_SINGLE",
        "ITEM_TABLE", "ITEM_STRUCTURE",
        # Data value types
        "DV_TEXT", "DV_CODED_TEXT", "DV_QUANTITY", "DV_COUNT", "DV_BOOLEAN",
        "DV_DATE_TIME", "DV_DATE", "DV_TIME", "DV_DURATION", "DV_ORDINAL",
        "DV_PROPORTION", "DV_MULTIMEDIA", "DV_PARSABLE", "DV_URI", "DV_EHR_URI",
        "DV_IDENTIFIER", "DV_STATE", "DV_INTERVAL",
        # Other RM types
        "CODE_PHRASE", "PARTY_PROXY", "PARTY_IDENTIFIED", "PARTY_RELATED",
        "PARTY_SELF", "PARTICIPATION", "ISM_TRANSITION", "ACTIVITY",
        "INSTRUCTION_DETAILS", "EVENT_CONTEXT",
        # Primitive types (used in constraint definitions within OPTs)
        "STRING", "INTEGER", "REAL", "BOOLEAN", "CHARACTER", "DATE", "TIME",
        "DATE_TIME", "DURATION", "DOUBLE", "FLOAT",
    }

    tree = ET.parse(filepath)
    root = tree.getroot()

    for rm_type_el in _find_all(root, "rm_type_name"):
        rm_type = rm_type_el.text
        if rm_type and rm_type not in known_rm_types:
            errors.append(ValidationError(
                template_file=fname,
                message=f"Unknown RM type: '{rm_type}'",
            ))

    return errors


def validate_template(filepath: Path) -> ValidationResult:
    """Run all validations on a single OPT file."""
    result = ValidationResult(templates_checked=1)

    # 1. Well-formed XML
    xml_errors = validate_xml_wellformed(filepath)
    if xml_errors:
        result.errors.extend(xml_errors)
        return result  # Can't continue if XML is broken

    # 2. Template structure
    result.errors.extend(validate_template_structure(filepath))

    # 3. Language codes
    result.errors.extend(validate_language_codes(filepath))

    # 4. Terminology codes (category, setting)
    term_errors, term_warnings = validate_terminology_codes(filepath)
    result.errors.extend(term_errors)
    result.warnings.extend(term_warnings)

    # 5. RM type names
    result.errors.extend(validate_definition_rm_types(filepath))

    return result


def validate_templates_dir(templates_dir: Path) -> ValidationResult:
    """Validate all .opt files in a directory."""
    combined = ValidationResult()

    opt_files = sorted(templates_dir.glob("*.opt"))
    if not opt_files:
        print(f"No .opt files found in {templates_dir}")
        return combined

    for opt_file in opt_files:
        result = validate_template(opt_file)
        combined.templates_checked += result.templates_checked
        combined.errors.extend(result.errors)
        combined.warnings.extend(result.warnings)

    return combined


def main() -> int:
    """CLI entry point."""
    # Determine templates directory
    if len(sys.argv) > 1:
        templates_dir = Path(sys.argv[1])
    else:
        # Default: api/templates relative to repo root
        script_dir = Path(__file__).resolve().parent
        templates_dir = script_dir.parent / "api" / "templates"

    if not templates_dir.is_dir():
        print(f"Error: Templates directory not found: {templates_dir}")
        return 1

    print(f"Validating OPT templates in: {templates_dir}")
    print()

    result = validate_templates_dir(templates_dir)

    # Print warnings
    for w in result.warnings:
        path_info = f" ({w.element_path})" if w.element_path else ""
        print(f"  WARN  {w.template_file}{path_info}: {w.message}")

    # Print errors
    for e in result.errors:
        path_info = f" ({e.element_path})" if e.element_path else ""
        print(f"  ERROR {e.template_file}{path_info}: {e.message}")

    # Summary
    print()
    print(
        f"Checked {result.templates_checked} template(s): "
        f"{len(result.errors)} error(s), {len(result.warnings)} warning(s)"
    )

    if result.is_valid:
        print("All templates valid.")
        return 0
    else:
        print("Template validation FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
