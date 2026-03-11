# ADR-0005: Synthetic Data Generation for Staging

**Date:** 2026-01-05 | **Status:** Accepted

## Context

Open CIS needs realistic synthetic clinical data for the Railway staging environment to enable demonstration and testing without real patient data, frontend development with realistic datasets, API testing with varied clinical scenarios, and onboarding new contributors with working examples.

### Options Evaluated

| Tool | Type | Verdict |
|------|------|---------|
| **MapEHR** | Commercial | Unavailable -- no public access, unknown pricing |
| **openFHIR** | Commercial | Requires trial license, focused on FHIR mapping |
| **Synthea + fhir-bridge** | Open Source | Viable but adds Java dependency + conversion layer |
| **Custom Python Script** | Custom | Immediately implementable, zero dependencies |

## Decision

We will implement a **custom Python seed script** using Faker and manual composition building for synthetic data generation in the staging environment.

### Implementation

- **Environment-aware**: Only runs when `RAILWAY_ENVIRONMENT=staging`
- **Idempotent**: Safe to run multiple times (checks patient count threshold)
- **Fast**: Completes in <10 seconds
- **Generates**:
    - 15 synthetic patients with realistic demographics (Faker)
    - 2-5 vital signs readings per patient
    - Clinically plausible values (BP: 90-140/60-90 mmHg, Pulse: 60-100 bpm)
    - Timestamps spread over past 1-4 weeks
    - MRN prefix: `STAGING-` to distinguish from production data

### Railway Integration

```dockerfile
CMD sh -c "prisma migrate deploy && \
  if [ \"$RAILWAY_ENVIRONMENT\" = \"staging\" ]; then \
    python scripts/seed_staging.py; \
  fi && \
  uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

## Consequences

### Positive

- Fast to implement, no external blockers
- No licensing fees or vendor dependencies
- Simple deployment as part of Railway start command
- Full control over generated data
- Git-friendly: seed script logic versioned in repository

### Negative

- Manual value ranges (must research clinical norms ourselves)
- Limited sophistication compared to specialized tools
- Must update script as templates evolve

### Future Path

Synthea + fhir-bridge remains a strong option if we need realistic longitudinal data in the future. MapEHR/openFHIR will be explored when complex clinical scenarios are needed.
