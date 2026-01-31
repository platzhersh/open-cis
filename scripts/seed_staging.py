#!/usr/bin/env python3
"""
Staging environment seed script for Open CIS.
Creates synthetic patients with realistic vital signs for demonstration and testing.

This script is designed to run automatically on Railway staging deployments.
It is idempotent and environment-aware (only runs in staging).
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime

from faker import Faker

# Add the api/src directory to the path so we can import from the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "src"))

from prisma import Prisma  # noqa: E402

# Configuration
RAILWAY_ENV = os.getenv("RAILWAY_ENVIRONMENT", "")
MIN_PATIENT_THRESHOLD = 3  # Re-seed if fewer than this many patients exist

# Faker for realistic demographics
fake = Faker()


async def should_seed(db: Prisma) -> bool:
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

    # Check patient count using Prisma directly
    try:
        patient_count = await db.patientregistry.count()
        if patient_count >= MIN_PATIENT_THRESHOLD:
            print(
                f"Skipping seed: sufficient patients exist ({patient_count} >= {MIN_PATIENT_THRESHOLD})"
            )
            return False
        print(f"Patient count: {patient_count} (threshold: {MIN_PATIENT_THRESHOLD})")
    except Exception as e:
        print(f"Warning: Could not check patient count ({e}), proceeding with seed...")

    return True


async def create_patient(db: Prisma, patient_data: dict) -> dict | None:
    """Create a patient in the PatientRegistry using Prisma."""
    try:
        # Convert birth_date string to datetime if needed
        birth_date = patient_data["birth_date"]
        if isinstance(birth_date, str):
            birth_date = datetime.fromisoformat(birth_date)

        # Generate a placeholder EHR ID for staging data
        # (real patients get this from EHRBase via the API)
        ehr_id = str(uuid.uuid4())

        patient = await db.patientregistry.create(
            data={
                "mrn": patient_data["mrn"],
                "ehrId": ehr_id,
                "givenName": patient_data["given_name"],
                "familyName": patient_data["family_name"],
                "birthDate": birth_date,
            }
        )
        return patient.model_dump()
    except Exception as e:
        print(f"  ❌ Error creating {patient_data['mrn']}: {e}")
        return None


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
    db: Prisma, patient_data: dict, num_readings: int = 3
) -> tuple[dict | None, int]:
    """
    Seed a single patient in the PatientRegistry.

    Note: Vital signs are stored in EHRBase (not the app DB), so this script
    only creates patient demographics. Vital signs can be added via the API
    once EHRBase is running.

    Returns: (patient, 0) - vital signs count is always 0 for DB-only seeding
    """
    # Create patient
    patient = await create_patient(db, patient_data)
    if not patient:
        return None, 0

    print(
        f"  ✅ Created: {patient['givenName']} {patient['familyName']} ({patient['mrn']})"
    )

    return patient, 0


async def main():
    """Main seeding function."""
    print("🌱 Open CIS Staging Seed Script")
    print("=" * 50)

    # Initialize Prisma
    db = Prisma()
    await db.connect()

    try:
        # Check if seeding should run
        if not await should_seed(db):
            return

        print(f"\n✅ Starting seed for environment: {RAILWAY_ENV or 'local'}")
        print()

        # Generate synthetic patient data
        synthetic_patients = generate_synthetic_patients(count=15)
        print(f"Generated {len(synthetic_patients)} synthetic patients")
        print()

        # Seed patients with vital signs
        created_patients = 0

        for patient_data in synthetic_patients:
            patient, _ = await seed_patient_with_vitals(db, patient_data)

            if patient:
                created_patients += 1

        # Summary
        print()
        print("=" * 50)
        print(f"✅ Seeding complete!")
        print(f"   Patients created: {created_patients}/{len(synthetic_patients)}")
        print()
        print("🎉 Staging data is ready for testing!")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
