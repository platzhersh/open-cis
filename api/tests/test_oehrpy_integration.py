"""Tests for oehrpy SDK integration."""

import pytest
from oehrpy.client import EHRBaseClient as OehrpyClient
from oehrpy.templates import VitalSignsBuilder

from src.ehrbase.client import EHRBaseClient
from src.openehr.compositions import VITAL_SIGNS_TEMPLATE_ID, build_vital_signs_flat


class TestVitalSignsBuilder:
    """Test VitalSignsBuilder produces valid FLAT output."""

    def test_builder_creates_required_context_fields(self):
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        flat = builder.build()

        # Should contain composition-level context
        flat_str = str(flat)
        assert "vital_signs" in flat_str

    def test_builder_blood_pressure(self):
        builder = VitalSignsBuilder(composer_name="Test")
        builder.add_blood_pressure(systolic=120, diastolic=80)
        flat = builder.build()

        # Look for systolic and diastolic values in the flat output
        bp_values = {k: v for k, v in flat.items() if "systolic" in k or "diastolic" in k}
        magnitudes = {k: v for k, v in bp_values.items() if "magnitude" in k}
        assert len(magnitudes) >= 2

    def test_builder_pulse(self):
        builder = VitalSignsBuilder(composer_name="Test")
        builder.add_pulse(rate=72)
        flat = builder.build()

        pulse_values = {
            k: v for k, v in flat.items() if "pulse" in k.lower() or "heart" in k.lower()
        }
        assert len(pulse_values) > 0

    def test_builder_combined_vitals(self):
        builder = VitalSignsBuilder(composer_name="Test")
        builder.add_blood_pressure(systolic=125, diastolic=82)
        builder.add_pulse(rate=68)
        flat = builder.build()

        assert isinstance(flat, dict)
        assert len(flat) > 0

    def test_builder_template_id(self):
        assert VitalSignsBuilder.template_id == "IDCR - Vital Signs Encounter.v1"

    def test_builder_fluent_api(self):
        """Builder methods return self for chaining."""
        builder = VitalSignsBuilder(composer_name="Test")
        result = builder.add_blood_pressure(systolic=120, diastolic=80)
        assert result is builder

    def test_add_all_vitals(self):
        builder = VitalSignsBuilder(composer_name="Test")
        builder.add_all_vitals(systolic=120, diastolic=80, pulse=72)
        flat = builder.build()
        assert isinstance(flat, dict)
        assert len(flat) > 0


class TestBuildVitalSigns:
    """Test the Open CIS composition helper."""

    def test_build_with_bp_and_pulse(self):
        flat = build_vital_signs_flat(
            systolic=120,
            diastolic=80,
            pulse_rate=72,
        )
        assert isinstance(flat, dict)
        assert len(flat) > 0

    def test_build_bp_only(self):
        flat = build_vital_signs_flat(systolic=130, diastolic=85)
        assert isinstance(flat, dict)

    def test_build_pulse_only(self):
        flat = build_vital_signs_flat(pulse_rate=68)
        assert isinstance(flat, dict)

    def test_template_id_matches(self):
        assert VITAL_SIGNS_TEMPLATE_ID == "IDCR - Vital Signs Encounter.v1"


class TestEHRBaseClientWrapper:
    """Test the EHRBase client wrapper."""

    @pytest.mark.asyncio
    async def test_client_creation(self):
        client = EHRBaseClient()
        assert client.base_url is not None
        assert client._client is None

    @pytest.mark.asyncio
    async def test_client_close_when_not_connected(self):
        client = EHRBaseClient()
        await client.close()
        assert client._client is None


class TestOehrpyClientDirect:
    """Test oehrpy client can be instantiated."""

    def test_client_creation(self):
        client = OehrpyClient(base_url="http://localhost:8080/ehrbase")
        assert client is not None

    def test_client_with_auth(self):
        client = OehrpyClient(
            base_url="http://localhost:8080/ehrbase",
            username="admin",
            password="admin",
        )
        assert client is not None
