"""Tests for the FHIR terminology client, enrichment, and system mapping."""

from typing import Any

import httpx
import pytest

from src.terminology.client import TerminologyClient
from src.terminology.enrichment import enrich_composition, enrich_flat_composition
from src.terminology.systems import INTERNAL_TERMINOLOGIES, to_fhir_system


class TestSystemMapping:
    """Test openEHR → FHIR system URI mapping."""

    def test_snomed_ct_mapping(self):
        assert to_fhir_system("SNOMED-CT") == "http://snomed.info/sct"

    def test_loinc_mapping(self):
        assert to_fhir_system("LOINC") == "http://loinc.org"

    def test_atc_mapping(self):
        assert to_fhir_system("ATC") == "http://www.whocc.no/atc"

    def test_icd10_mapping(self):
        assert to_fhir_system("ICD10") == "http://hl7.org/fhir/sid/icd-10"

    def test_internal_openehr_returns_none(self):
        assert to_fhir_system("openehr") is None

    def test_internal_local_returns_none(self):
        assert to_fhir_system("local") is None

    def test_http_uri_passthrough(self):
        uri = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
        assert to_fhir_system(uri) == uri

    def test_unknown_returns_none(self):
        assert to_fhir_system("UNKNOWN-SYSTEM") is None

    def test_internal_terminologies_set(self):
        assert "openehr" in INTERNAL_TERMINOLOGIES
        assert "local" in INTERNAL_TERMINOLOGIES


class TestTerminologyClientLookup:
    """Test TerminologyClient.lookup with mocked transport."""

    @pytest.mark.asyncio
    async def test_lookup_returns_display(self):
        """Test that lookup extracts display from FHIR Parameters response."""
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "resourceType": "Parameters",
                    "parameter": [
                        {"name": "display", "valueString": "Observable entity"},
                        {"name": "name", "valueString": "Observable entity"},
                    ],
                },
            )

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        result = await client.lookup("http://snomed.info/sct", "363787002")
        assert result == "Observable entity"
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_caches_result(self):
        """Test that repeated lookups use the cache."""
        import httpx

        call_count = 0

        def mock_handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                200,
                json={
                    "resourceType": "Parameters",
                    "parameter": [
                        {"name": "display", "valueString": "Test display"},
                    ],
                },
            )

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        r1 = await client.lookup("http://snomed.info/sct", "12345")
        r2 = await client.lookup("http://snomed.info/sct", "12345")

        assert r1 == "Test display"
        assert r2 == "Test display"
        assert call_count == 1  # Only one HTTP call — second was cached
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_returns_none_on_404(self):
        """Test that lookup returns None for unknown codes."""
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"resourceType": "OperationOutcome"})

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        result = await client.lookup("http://snomed.info/sct", "999999999")
        assert result is None
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_returns_none_on_network_error(self):
        """Test that lookup fails silently on network errors."""
        def mock_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        result = await client.lookup("http://snomed.info/sct", "12345")
        assert result is None
        await client.close()


class TestTerminologyClientValidateCode:
    """Test TerminologyClient.validate_code."""

    @pytest.mark.asyncio
    async def test_validate_code_returns_true(self):
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "resourceType": "Parameters",
                    "parameter": [{"name": "result", "valueBoolean": True}],
                },
            )

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        result = await client.validate_code(
            "http://example.com/ValueSet/test",
            "http://snomed.info/sct",
            "12345",
        )
        assert result is True
        await client.close()

    @pytest.mark.asyncio
    async def test_validate_code_returns_false(self):
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "resourceType": "Parameters",
                    "parameter": [{"name": "result", "valueBoolean": False}],
                },
            )

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        result = await client.validate_code(
            "http://example.com/ValueSet/test",
            "http://snomed.info/sct",
            "99999",
        )
        assert result is False
        await client.close()


class TestTerminologyClientExpand:
    """Test TerminologyClient.expand."""

    @pytest.mark.asyncio
    async def test_expand_returns_valueset(self):
        import httpx

        from src.terminology.client import TerminologyClient

        valueset_response = {
            "resourceType": "ValueSet",
            "expansion": {
                "contains": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "840539006",
                        "display": "COVID-19 vaccine",
                    }
                ]
            },
        }

        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=valueset_response)

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        result = await client.expand("http://example.com/ValueSet/vaccines")
        assert result["resourceType"] == "ValueSet"
        assert len(result["expansion"]["contains"]) == 1
        await client.close()


class TestTerminologyHealthCheck:
    """Test TerminologyClient.health_check."""

    @pytest.mark.asyncio
    async def test_health_check_online(self):
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"resourceType": "CapabilityStatement"})

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        status, ms = await client.health_check()
        assert status == "online"
        assert ms is not None
        assert ms >= 0
        await client.close()

    @pytest.mark.asyncio
    async def test_health_check_offline_on_error(self):
        def mock_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        status, ms = await client.health_check()
        assert status == "offline"
        assert ms is None
        await client.close()


class TestEnrichment:
    """Test composition enrichment."""

    @pytest.mark.asyncio
    async def test_enrich_composition_structured(self):
        """Test enrichment of STRUCTURED format DV_CODED_TEXT nodes."""
        import httpx

        def mock_handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "363787002" in url:
                return httpx.Response(
                    200,
                    json={
                        "resourceType": "Parameters",
                        "parameter": [
                            {"name": "display", "valueString": "Observable entity"},
                        ],
                    },
                )
            return httpx.Response(404, json={})

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        composition: dict[str, Any] = {
            "_type": "COMPOSITION",
            "content": [
                {
                    "_type": "DV_CODED_TEXT",
                    "value": "363787002",
                    "defining_code": {
                        "_type": "CODE_PHRASE",
                        "terminology_id": {"value": "SNOMED-CT"},
                        "code_string": "363787002",
                    },
                }
            ],
        }

        result = await enrich_composition(composition, client)

        # Original should be unchanged
        assert composition["content"][0]["value"] == "363787002"
        # Enriched copy should have display term
        assert result["content"][0]["value"] == "Observable entity"
        await client.close()

    @pytest.mark.asyncio
    async def test_enrich_skips_local_terminology(self):
        """Test that internal terminologies (local, openehr) are skipped."""
        import httpx

        from src.terminology.client import TerminologyClient
        from src.terminology.enrichment import enrich_composition

        call_count = 0

        def mock_handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json={})

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        composition = {
            "_type": "DV_CODED_TEXT",
            "value": "",
            "defining_code": {
                "_type": "CODE_PHRASE",
                "terminology_id": {"value": "local"},
                "code_string": "at0001",
            },
        }

        result = await enrich_composition(composition, client)
        assert call_count == 0  # No HTTP calls for local terminology
        assert result["value"] == ""
        await client.close()

    @pytest.mark.asyncio
    async def test_enrich_flat_composition(self):
        """Test enrichment of FLAT format compositions."""
        import httpx

        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "resourceType": "Parameters",
                    "parameter": [
                        {"name": "display", "valueString": "High"},
                    ],
                },
            )

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        flat = {
            "some_path/interpretation|code": "H",
            "some_path/interpretation|value": "H",
            "some_path/interpretation|terminology": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
            "some_path/magnitude|magnitude": 150,
        }

        result = await enrich_flat_composition(flat, client)
        assert result["some_path/interpretation|value"] == "High"
        await client.close()

    @pytest.mark.asyncio
    async def test_enrich_preserves_existing_display(self):
        """Test that nodes with proper display terms are not overwritten."""
        import httpx

        from src.terminology.client import TerminologyClient
        from src.terminology.enrichment import enrich_composition

        call_count = 0

        def mock_handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json={})

        client = TerminologyClient()
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_handler),
            base_url="http://test-tx",
        )

        composition = {
            "_type": "DV_CODED_TEXT",
            "value": "Already has a proper display term",
            "defining_code": {
                "_type": "CODE_PHRASE",
                "terminology_id": {"value": "SNOMED-CT"},
                "code_string": "12345",
            },
        }

        result = await enrich_composition(composition, client)
        assert call_count == 0  # No lookup needed
        assert result["value"] == "Already has a proper display term"
        await client.close()
