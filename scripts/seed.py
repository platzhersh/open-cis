#!/usr/bin/env python3
"""
Seed script for Open CIS.
Creates sample patients and data for development.
"""

import asyncio
import httpx

API_URL = "http://localhost:8000"

SAMPLE_PATIENTS = [
    {
        "mrn": "MRN-001",
        "given_name": "John",
        "family_name": "Smith",
        "birth_date": "1980-05-15",
    },
    {
        "mrn": "MRN-002",
        "given_name": "Jane",
        "family_name": "Doe",
        "birth_date": "1992-08-22",
    },
    {
        "mrn": "MRN-003",
        "given_name": "Robert",
        "family_name": "Johnson",
        "birth_date": "1975-12-01",
    },
    {
        "mrn": "MRN-004",
        "given_name": "Maria",
        "family_name": "Garcia",
        "birth_date": "1988-03-10",
    },
    {
        "mrn": "MRN-005",
        "given_name": "David",
        "family_name": "Wilson",
        "birth_date": "1965-07-28",
    },
]


async def check_api_health():
    """Check if the API is running."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/health")
            return response.status_code == 200
        except httpx.ConnectError:
            return False


async def create_patient(client: httpx.AsyncClient, patient_data: dict) -> dict | None:
    """Create a patient via the API."""
    try:
        response = await client.post(
            f"{API_URL}/api/patients",
            json=patient_data,
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f"  Failed to create {patient_data['mrn']}: {response.text}")
            return None
    except Exception as e:
        print(f"  Error creating {patient_data['mrn']}: {e}")
        return None


async def main():
    """Main seed function."""
    print("🌱 Seeding Open CIS database...")
    print()

    # Check API health
    if not await check_api_health():
        print("❌ API is not running. Start the API first:")
        print("   cd api && uvicorn src.main:app --reload --port 8000")
        return

    print("✅ API is running")
    print()

    # Create patients
    print("Creating sample patients...")
    async with httpx.AsyncClient() as client:
        created = 0
        for patient_data in SAMPLE_PATIENTS:
            result = await create_patient(client, patient_data)
            if result:
                print(f"  ✅ Created: {result['given_name']} {result['family_name']} ({result['mrn']})")
                created += 1

    print()
    print(f"✅ Created {created}/{len(SAMPLE_PATIENTS)} patients")
    print()
    print("You can view them at: http://localhost:5173/patients")


if __name__ == "__main__":
    asyncio.run(main())
