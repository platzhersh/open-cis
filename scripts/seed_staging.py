#!/usr/bin/env python3
"""
Staging environment seed script for Open CIS.
Creates synthetic patients with realistic vital signs for demonstration and testing.

This script is designed to run automatically on Railway staging deployments.
It is idempotent and environment-aware (only runs in staging).
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from random import randint, uniform

import httpx
from faker import Faker

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
RAILWAY_ENV = os.getenv("RAILWAY_ENVIRONMENT", "")
MIN_PATIENT_THRESHOLD = 3  # Re-seed if fewer than this many patients exist

# Faker for realistic demographics
fake = Faker()

# Clinically realistic value ranges (based on WHO guidelines)
VITAL_SIGNS_RANGES = {
    "systolic_bp": (90, 140),  # mmHg (normal: 90-120, pre-hypertension: 120-140)
    "diastolic_bp": (60, 90),  # mmHg (normal: 60-80, pre-hypertension: 80-90)
    "pulse_rate": (60, 100),  # bpm (normal resting adult)
}


async def should_seed() -> bool:
    """
    Determine if seeding should run.

    Only seed if:
    1. RAILWAY_ENVIRONMENT is 'staging' (or empty for local dev)
    2. Patient count is below threshold
    """
    # Check environment
    if RAILWAY_ENV and RAILWAY_ENV != "staging":
        print(f"Skipping seed: not staging environment (current: {RAILWAY_ENV})")
        return False

    # Check if API is available
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/health")
            if response.status_code != 200:
                print("Skipping seed: API not healthy")
                return False
    except Exception as e:
        print(f"Skipping seed: API not accessible ({e})")
        return False

    # Check patient count
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/api/patients")
            if response.status_code == 200:
                patients = response.json()
                patient_count = len(patients)
                if patient_count >= MIN_PATIENT_THRESHOLD:
                    print(
                        f"Skipping seed: sufficient patients exist ({patient_count} >= {MIN_PATIENT_THRESHOLD})"
                    )
                    return False
                print(f"Patient count: {patient_count} (threshold: {MIN_PATIENT_THRESHOLD})")
    except Exception as e:
        print(f"Warning: Could not check patient count ({e}), proceeding with seed...")

    return True


async def create_patient(
    client: httpx.AsyncClient, patient_data: dict
) -> dict | None:
    """Create a patient via the API."""
    try:
        response = await client.post(
            f"{API_URL}/api/patients",
            json=patient_data,
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f"  ⚠️  Failed to create {patient_data['mrn']}: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Error creating {patient_data['mrn']}: {e}")
        return None


async def create_vital_signs(
    client: httpx.AsyncClient, vital_signs_data: dict
) -> dict | None:
    """Create vital signs observation via the API."""
    try:
        response = await client.post(
            f"{API_URL}/api/vital-signs",
            json=vital_signs_data,
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f"  ⚠️  Failed to create vital signs: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Error creating vital signs: {e}")
        return None


def generate_realistic_vital_signs(base_date: datetime, offset_hours: int) -> dict:
    """
    Generate clinically realistic vital signs.

    Uses normal distribution around healthy ranges with some variability.
    """
    recorded_at = base_date - timedelta(hours=offset_hours)

    # Generate correlated values (e.g., high systolic -> higher diastolic)
    systolic = randint(*VITAL_SIGNS_RANGES["systolic_bp"])

    # Diastolic tends to be proportional to systolic
    if systolic > 130:
        diastolic = randint(80, 90)  # Higher diastolic with high systolic
    elif systolic < 100:
        diastolic = randint(60, 70)  # Lower diastolic with low systolic
    else:
        diastolic = randint(65, 80)  # Normal range

    pulse_rate = randint(*VITAL_SIGNS_RANGES["pulse_rate"])

    return {
        "recorded_at": recorded_at.isoformat(),
        "systolic": systolic,
        "diastolic": diastolic,
        "pulse_rate": pulse_rate,
    }


def generate_synthetic_patients(count: int = 15) -> list[dict]:
    """Generate synthetic patient demographics with realistic data."""
    patients = []

    for i in range(count):
        # Use STAGING- prefix to distinguish from real data
        mrn = f"STAGING-{fake.unique.bothify(text='####')}"

        # Generate realistic demographics
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=85)

        patient = {
            "mrn": mrn,
            "given_name": fake.first_name(),
            "family_name": fake.last_name(),
            "birth_date": birth_date.isoformat(),
        }
        patients.append(patient)

    return patients


async def seed_patient_with_vitals(
    client: httpx.AsyncClient, patient_data: dict, num_readings: int = 3
) -> tuple[dict | None, list[dict]]:
    """
    Seed a single patient with multiple vital signs readings.

    Returns: (patient, list of vital signs)
    """
    # Create patient
    patient = await create_patient(client, patient_data)
    if not patient:
        return None, []

    patient_id = patient["id"]
    print(
        f"  ✅ Created: {patient['given_name']} {patient['family_name']} ({patient['mrn']})"
    )

    # Create vital signs readings spread over recent weeks
    vital_signs_list = []
    base_date = datetime.now(UTC)

    for i in range(num_readings):
        # Spread readings over past 2-4 weeks
        hours_offset = randint(24 * 7, 24 * 28)  # 1-4 weeks ago

        vital_signs_data = generate_realistic_vital_signs(base_date, hours_offset)
        vital_signs_data["patient_id"] = patient_id
        vital_signs_data["encounter_id"] = None

        vital_signs = await create_vital_signs(client, vital_signs_data)
        if vital_signs:
            vital_signs_list.append(vital_signs)
            print(
                f"    📊 Vital signs: {vital_signs_data['systolic']}/{vital_signs_data['diastolic']} mmHg, "
                f"{vital_signs_data['pulse_rate']} bpm"
            )

    return patient, vital_signs_list


async def main():
    """Main seeding function."""
    print("🌱 Open CIS Staging Seed Script")
    print("=" * 50)

    # Check if seeding should run
    if not await should_seed():
        return

    print(f"\n✅ Starting seed for environment: {RAILWAY_ENV or 'local'}")
    print(f"   API URL: {API_URL}")
    print()

    # Generate synthetic patient data
    synthetic_patients = generate_synthetic_patients(count=15)
    print(f"Generated {len(synthetic_patients)} synthetic patients")
    print()

    # Seed patients with vital signs
    async with httpx.AsyncClient(timeout=30.0) as client:
        created_patients = 0
        total_vital_signs = 0

        for patient_data in synthetic_patients:
            patient, vital_signs = await seed_patient_with_vitals(
                client, patient_data, num_readings=randint(2, 5)
            )

            if patient:
                created_patients += 1
                total_vital_signs += len(vital_signs)

    # Summary
    print()
    print("=" * 50)
    print(f"✅ Seeding complete!")
    print(f"   Patients created: {created_patients}/{len(synthetic_patients)}")
    print(f"   Vital signs created: {total_vital_signs}")
    print()
    print("🎉 Staging data is ready for testing!")


if __name__ == "__main__":
    asyncio.run(main())
