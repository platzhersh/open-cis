"""Tests for the OPT template validator."""

import textwrap
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

# Import from the scripts directory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from validate_templates import (
    validate_template,
    validate_xml_wellformed,
    validate_template_structure,
    validate_language_codes,
    validate_terminology_codes,
)

MINIMAL_VALID_OPT = textwrap.dedent("""\
    <?xml version="1.0" encoding="utf-8"?>
    <template xmlns="http://schemas.openehr.org/v1">
      <language>
        <terminology_id><value>ISO_639-1</value></terminology_id>
        <code_string>en</code_string>
      </language>
      <description>
        <original_author id="author">Test</original_author>
        <lifecycle_state>Initial</lifecycle_state>
        <details>
          <language>
            <terminology_id><value>ISO_639-1</value></terminology_id>
            <code_string>en</code_string>
          </language>
        </details>
      </description>
      <concept>Test Template.v1</concept>
      <definition>
        <rm_type_name>COMPOSITION</rm_type_name>
        <node_id>at0000</node_id>
      </definition>
    </template>
""")


def _write_temp_opt(content: str) -> Path:
    """Write content to a temp .opt file and return its path."""
    f = NamedTemporaryFile(suffix=".opt", mode="w", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestXmlWellformed:
    def test_valid_xml(self) -> None:
        path = _write_temp_opt(MINIMAL_VALID_OPT)
        errors = validate_xml_wellformed(path)
        assert errors == []

    def test_malformed_xml(self) -> None:
        path = _write_temp_opt("<template><unclosed>")
        errors = validate_xml_wellformed(path)
        assert len(errors) == 1
        assert "Malformed XML" in errors[0].message


class TestTemplateStructure:
    def test_valid_structure(self) -> None:
        path = _write_temp_opt(MINIMAL_VALID_OPT)
        errors = validate_template_structure(path)
        assert errors == []

    def test_missing_concept(self) -> None:
        content = MINIMAL_VALID_OPT.replace(
            "<concept>Test Template.v1</concept>", ""
        )
        path = _write_temp_opt(content)
        errors = validate_template_structure(path)
        assert any("concept" in e.message.lower() for e in errors)

    def test_missing_definition(self) -> None:
        # Remove the entire definition block
        lines = MINIMAL_VALID_OPT.splitlines(keepends=True)
        content = "".join(
            line for line in lines
            if not any(tag in line for tag in ["<definition>", "</definition>", "rm_type_name", "node_id"])
        )
        path = _write_temp_opt(content)
        errors = validate_template_structure(path)
        assert any("definition" in e.message.lower() for e in errors)


class TestLanguageCodes:
    def test_valid_language(self) -> None:
        path = _write_temp_opt(MINIMAL_VALID_OPT)
        errors = validate_language_codes(path)
        assert errors == []

    def test_invalid_language(self) -> None:
        content = MINIMAL_VALID_OPT.replace(
            "<code_string>en</code_string>",
            "<code_string>xx</code_string>",
            1,  # Only replace first occurrence (top-level language)
        )
        path = _write_temp_opt(content)
        errors = validate_language_codes(path)
        assert len(errors) == 1
        assert "xx" in errors[0].message


class TestTerminologyCodes:
    def test_valid_category_code(self) -> None:
        content = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <template xmlns="http://schemas.openehr.org/v1">
              <language>
                <terminology_id><value>ISO_639-1</value></terminology_id>
                <code_string>en</code_string>
              </language>
              <description>
                <original_author id="author">Test</original_author>
                <lifecycle_state>Initial</lifecycle_state>
                <details>
                  <language>
                    <terminology_id><value>ISO_639-1</value></terminology_id>
                    <code_string>en</code_string>
                  </language>
                </details>
              </description>
              <concept>Test.v1</concept>
              <definition>
                <rm_type_name>COMPOSITION</rm_type_name>
                <node_id>at0000</node_id>
                <attributes>
                  <children>
                    <category>
                      <terminology_id><value>openehr</value></terminology_id>
                      <code_string>433</code_string>
                    </category>
                  </children>
                </attributes>
              </definition>
            </template>
        """)
        path = _write_temp_opt(content)
        errors, warnings = validate_terminology_codes(path)
        assert errors == []

    def test_invalid_category_code(self) -> None:
        """Category code 999 is not a valid openEHR category code."""
        content = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <template xmlns="http://schemas.openehr.org/v1">
              <language>
                <terminology_id><value>ISO_639-1</value></terminology_id>
                <code_string>en</code_string>
              </language>
              <description>
                <original_author id="author">Test</original_author>
                <lifecycle_state>Initial</lifecycle_state>
                <details>
                  <language>
                    <terminology_id><value>ISO_639-1</value></terminology_id>
                    <code_string>en</code_string>
                  </language>
                </details>
              </description>
              <concept>Test.v1</concept>
              <definition>
                <rm_type_name>COMPOSITION</rm_type_name>
                <node_id>at0000</node_id>
                <attributes>
                  <children>
                    <category>
                      <terminology_id><value>openehr</value></terminology_id>
                      <code_string>999</code_string>
                    </category>
                  </children>
                </attributes>
              </definition>
            </template>
        """)
        path = _write_temp_opt(content)
        errors, warnings = validate_terminology_codes(path)
        assert len(errors) == 1
        assert "999" in errors[0].message
        assert "category" in errors[0].message.lower()


class TestFullValidation:
    def test_valid_template(self) -> None:
        path = _write_temp_opt(MINIMAL_VALID_OPT)
        result = validate_template(path)
        assert result.is_valid

    def test_existing_templates(self) -> None:
        """Validate the actual templates in the repo."""
        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        if not templates_dir.exists():
            pytest.skip("Templates directory not found")
        for opt_file in templates_dir.glob("*.opt"):
            result = validate_template(opt_file)
            assert result.is_valid, (
                f"{opt_file.name} has validation errors: "
                + "; ".join(e.message for e in result.errors)
            )
