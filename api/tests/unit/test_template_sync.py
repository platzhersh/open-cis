"""Tests for template change detection and sync logic."""

from unittest.mock import AsyncMock, patch

import pytest

from src.ehrbase.templates import _sync_template, _xml_hash

# ---------------------------------------------------------------------------
# _xml_hash — canonical XML hashing
# ---------------------------------------------------------------------------


class TestXmlHash:
    """Test the _xml_hash helper that normalises XML before hashing."""

    def test_identical_xml_produces_same_hash(self):
        xml = "<root><child attr='1'>text</child></root>"
        assert _xml_hash(xml) == _xml_hash(xml)

    def test_different_xml_produces_different_hash(self):
        xml_a = "<root><a>1</a></root>"
        xml_b = "<root><a>2</a></root>"
        assert _xml_hash(xml_a) != _xml_hash(xml_b)

    def test_empty_element_syntax_is_normalised(self):
        """C14N normalises <br/> vs <br></br> — both produce the same hash."""
        self_closing = "<root><child/></root>"
        expanded = "<root><child></child></root>"
        assert _xml_hash(self_closing) == _xml_hash(expanded)

    def test_attribute_order_is_normalised(self):
        xml_a = '<root a="1" b="2"/>'
        xml_b = '<root b="2" a="1"/>'
        assert _xml_hash(xml_a) == _xml_hash(xml_b)

    def test_invalid_xml_falls_back_to_raw_hash(self):
        bad = "not xml at all <<<"
        # Should not raise, and should return a deterministic hash
        h = _xml_hash(bad)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest length
        assert _xml_hash(bad) == h

    def test_empty_string_does_not_raise(self):
        h = _xml_hash("")
        assert isinstance(h, str)


# ---------------------------------------------------------------------------
# _sync_template — skip / upload / update logic
# ---------------------------------------------------------------------------


SAMPLE_OPT = "<template><id>Test.v1</id></template>"
MODIFIED_OPT = "<template><id>Test.v1</id><extra/></template>"


class TestSyncTemplateSkipsUnchanged:
    """When the remote OPT matches the local file, no upload should happen."""

    @pytest.mark.asyncio
    async def test_unchanged_template_returns_true(self):
        with patch("src.ehrbase.templates.ehrbase_client") as mock_client:
            mock_client.get_template_opt = AsyncMock(return_value=SAMPLE_OPT)
            mock_client.update_template_opt = AsyncMock()
            mock_client.upload_template = AsyncMock()

            result = await _sync_template("Test.v1", SAMPLE_OPT)

            assert result is True
            mock_client.update_template_opt.assert_not_called()
            mock_client.upload_template.assert_not_called()


class TestSyncTemplateUploadsNew:
    """When the template is not in EHRBase, it should be uploaded."""

    @pytest.mark.asyncio
    async def test_new_template_is_uploaded(self):
        with patch("src.ehrbase.templates.ehrbase_client") as mock_client:
            mock_client.get_template_opt = AsyncMock(return_value=None)
            mock_client.upload_template = AsyncMock(
                return_value={"template_id": "Test.v1", "status": "uploaded"}
            )

            result = await _sync_template("Test.v1", SAMPLE_OPT)

            assert result is True
            mock_client.upload_template.assert_called_once()


class TestSyncTemplateUpdatesChanged:
    """When the remote OPT differs, a PUT update should be attempted."""

    @pytest.mark.asyncio
    async def test_changed_template_triggers_put_update(self):
        with patch("src.ehrbase.templates.ehrbase_client") as mock_client:
            mock_client.get_template_opt = AsyncMock(return_value=MODIFIED_OPT)
            mock_client.update_template_opt = AsyncMock(return_value=True)

            result = await _sync_template("Test.v1", SAMPLE_OPT)

            assert result is True
            mock_client.update_template_opt.assert_called_once_with("Test.v1", SAMPLE_OPT)

    @pytest.mark.asyncio
    async def test_put_update_rejected_returns_false(self):
        with patch("src.ehrbase.templates.ehrbase_client") as mock_client:
            mock_client.get_template_opt = AsyncMock(return_value=MODIFIED_OPT)
            mock_client.update_template_opt = AsyncMock(return_value=False)

            result = await _sync_template("Test.v1", SAMPLE_OPT)

            assert result is False

    @pytest.mark.asyncio
    async def test_put_update_exception_returns_false(self):
        with patch("src.ehrbase.templates.ehrbase_client") as mock_client:
            mock_client.get_template_opt = AsyncMock(return_value=MODIFIED_OPT)
            mock_client.update_template_opt = AsyncMock(
                side_effect=Exception("EHRBase unavailable")
            )

            result = await _sync_template("Test.v1", SAMPLE_OPT)

            assert result is False


class TestSyncTemplateFetchFailure:
    """When fetching the remote OPT fails, fall back to upload."""

    @pytest.mark.asyncio
    async def test_fetch_failure_falls_back_to_upload(self):
        with patch("src.ehrbase.templates.ehrbase_client") as mock_client:
            mock_client.get_template_opt = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            mock_client.upload_template = AsyncMock(
                return_value={"template_id": "Test.v1", "status": "uploaded"}
            )

            result = await _sync_template("Test.v1", SAMPLE_OPT)

            assert result is True
            mock_client.upload_template.assert_called_once()
