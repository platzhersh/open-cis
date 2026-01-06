# 5. Synthetic Data Generation for Staging Environment

Date: 2026-01-05

## Status

Accepted

## Context

Open CIS needs realistic synthetic clinical data for the Railway staging environment to enable:
1. Demonstration and testing without real patient data
2. Frontend development with realistic datasets
3. API testing with varied clinical scenarios
4. Onboarding new contributors with working examples

### Problem

The current seed script (`scripts/seed.py`) only creates basic patient demographics (MRN, name, birth date). It lacks:
- Clinical observations (vital signs, lab results)
- Encounter histories
- Medications and diagnoses
- Longitudinal patient journeys
- Realistic value distributions

For a staging environment, we need synthetic data that:
- Matches our openEHR templates
- Generates clinically plausible values
- Can be easily recreated for each deployment
- Requires minimal external dependencies
- Works with our EHRbase + FastAPI stack

### Research: Available Solutions

#### 1. MapEHR
**Website**: https://mapehr.com/
**Type**: Commercial/Proprietary

**Features**:
- Purpose-built for openEHR synthetic data generation
- YAML-based rules with LOINC/SNOMED codes
- Faker library integration for demographics
- Statistical distributions for clinical values (e.g., `randomNormalDistribution()`)
- Supports complex calculations (BMI from height/weight)
- Works with OPT2 templates

**Limitations**:
- ❌ Not publicly available (no GitHub, npm, or PyPI package)
- ❌ Website blocks automated access (403 errors)
- ❌ No pricing information publicly available
- ❌ Requires vendor contact for access
- ❌ Proprietary product with potential licensing costs
- ⚠️ Template compatibility unclear (we use OPT 1.4, MapEHR uses OPT2)

**Status**: Unavailable for immediate use

#### 2. openFHIR
**Website**: https://open-fhir.com/
**Type**: Commercial (trial available)

**Features**:
- Docker-based FHIR ↔ openEHR mapping engine
- YAML mapping rules (nearly identical to MapEHR)
- Bidirectional conversion
- Sandbox available (sandbox.open-fhir.com)

**Limitations**:
- ❌ Requires trial license request
- ❌ Commercial product (pricing unknown)
- ❌ Focused on FHIR mapping, not synthetic data generation
- ⚠️ Would need separate data source (like Synthea)

**Status**: Could explore for future FHIR integration

#### 3. Synthea
**Repository**: https://github.com/synthetichealth/synthea
**Type**: Open Source (Apache 2.0)

**Features**:
- ✅ Industry-standard synthetic patient generator
- ✅ Generates realistic longitudinal patient histories
- ✅ Exports FHIR R4, STU3, C-CDA, CSV
- ✅ 1M+ free synthetic records available
- ✅ Actively maintained (3.5k+ commits)
- ✅ Docker images available
- ✅ Clinically validated scenarios

**Limitations**:
- ❌ No direct openEHR export (FHIR only)
- ⚠️ Requires FHIR → openEHR conversion layer
- ⚠️ Additional dependency (Java-based)

**Integration Path**:
```
Synthea (FHIR) → fhir-bridge → EHRbase (openEHR)
```

**Status**: Viable option but adds complexity

#### 4. ehrbase/fhir-bridge
**Repository**: https://github.com/ehrbase/fhir-bridge
**Type**: Open Source

**Features**:
- ✅ Official EHRbase component
- ✅ Converts FHIR → openEHR compositions
- ✅ Actively maintained

**Limitations**:
- ❌ Only handles conversion, not data generation
- ⚠️ Must be paired with Synthea or similar

**Status**: Complementary tool, not standalone solution

#### 5. Custom Python Script
**Implementation**: Enhanced `scripts/seed.py`

**Features**:
- ✅ Full control over data generation
- ✅ Uses Faker for realistic demographics
- ✅ Direct integration with existing `ehrbase_client`
- ✅ No external service dependencies
- ✅ Can be customized for specific test scenarios
- ✅ Railway-ready (no additional infrastructure)
- ✅ Works with existing templates (OPT 1.4)
- ✅ Simple to maintain and extend

**Limitations**:
- ⚠️ Manual work to create realistic clinical scenarios
- ⚠️ Need to define value ranges ourselves
- ⚠️ Less sophisticated than specialized tools
- ⚠️ No longitudinal patient journeys (initially)

**Status**: Immediately implementable

## Decision

We will implement **Option 5: Custom Python Seed Script** using Faker and manual composition building for synthetic data generation in the staging environment.

### Implementation Approach

```python
# scripts/seed.py (enhanced)
import asyncio
from datetime import datetime, timedelta
from faker import Faker
import httpx
from random import randint, uniform

fake = Faker()

async def create_synthetic_patient_with_vitals():
    # 1. Create patient with Faker demographics
    patient = {
        "mrn": fake.unique.bothify(text='MRN-####'),
        "given_name": fake.first_name(),
        "family_name": fake.last_name(),
        "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=90)
    }

    # 2. Create vital signs composition
    vital_signs = {
        "ctx/language": "en",
        "ctx/territory": "US",
        "vital_signs/blood_pressure/systolic": randint(90, 140),
        "vital_signs/blood_pressure/diastolic": randint(60, 90),
        "vital_signs/pulse_rate": randint(60, 100),
        "vital_signs/body_temperature": uniform(36.1, 37.5),
        "vital_signs/time": datetime.now().isoformat()
    }

    # 3. Post to API
    # ... (existing patient creation logic)
    # ... (new composition creation via ehrbase_client)
```

### Railway Deployment Integration

Railway provides several approaches for running seed scripts during deployment:

#### Option 1: Dockerfile CMD with Chained Commands (Current Approach)
We already use this pattern for migrations in `api/Dockerfile`:

```dockerfile
CMD sh -c "prisma migrate deploy && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

For seeding, we can extend this to:

```dockerfile
CMD sh -c "prisma migrate deploy && python scripts/seed_staging.py && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

**Pros:**
- ✅ Runs automatically on every deployment
- ✅ Consistent with existing migration pattern
- ✅ No Railway configuration changes needed
- ✅ Works for all Railway environments

**Cons:**
- ⚠️ Runs on every container start (including restarts)
- ⚠️ Requires idempotent seed script
- ⚠️ Can't easily disable for production

#### Option 2: railway.toml startCommand
Configure per-environment start commands in `api/railway.toml`:

```toml
[deploy]
startCommand = "prisma migrate deploy && python scripts/seed_staging.py && uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

**Pros:**
- ✅ Overrides Dockerfile CMD
- ✅ Can be environment-specific (different Railway projects for staging/prod)
- ✅ No Dockerfile changes needed

**Cons:**
- ⚠️ Configuration split between Dockerfile and railway.toml
- ⚠️ Must remember to set for staging environment only

#### Option 3: Conditional Seeding Based on Environment Variable
Add environment variable check in Dockerfile:

```dockerfile
CMD sh -c "prisma migrate deploy && \
  if [ \"$RAILWAY_ENVIRONMENT\" = \"staging\" ]; then python scripts/seed_staging.py; fi && \
  uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

**Pros:**
- ✅ Single Dockerfile works for all environments
- ✅ Automatic based on Railway environment
- ✅ No accidental production seeding

**Cons:**
- ⚠️ More complex shell script in CMD
- ⚠️ Requires setting `RAILWAY_ENVIRONMENT` variable

#### Recommended Approach: Option 3 (Conditional + Idempotent)

We'll use **conditional seeding based on environment variable** with an **idempotent seed script** that:

1. **Checks if data exists**: Only seed if patient count < threshold
2. **Uses unique identifiers**: MRNs that won't conflict with real data
3. **Handles existing records gracefully**: Skip or update, don't fail
4. **Runs quickly**: Complete in <10 seconds to avoid deployment timeout

```python
# scripts/seed_staging.py
async def should_seed() -> bool:
    """Only seed if staging environment and data doesn't exist."""
    if os.getenv("RAILWAY_ENVIRONMENT") != "staging":
        return False

    patient_count = await get_patient_count()
    return patient_count < 5  # Threshold for re-seeding

async def main():
    if not await should_seed():
        print("Skipping seed (not staging or data exists)")
        return

    print("Seeding staging data...")
    # ... seed logic
```

### Scope

**Initial implementation** (for staging deployment):
- Patient demographics (10-20 synthetic patients)
- Vital signs observations (2-5 per patient)
- Realistic value ranges based on clinical norms
- Timestamps spread over recent weeks
- Idempotent execution (safe to run multiple times)
- Environment-aware (staging only)

**Future enhancements** (as needed):
- Diagnoses and problem lists
- Medication orders
- Lab results
- Encounter histories
- Longitudinal data (multiple observations over time)

## Rationale

### Why Custom Python Script?

1. **Immediate Availability**: No vendor contact, licensing, or trial requests needed
2. **Zero Additional Dependencies**: Uses existing stack (Python, httpx, Faker)
3. **Railway Compatibility**: Simple script, no additional services/containers
4. **Full Control**: Customize data to match our specific templates and scenarios
5. **Maintainability**: ~200 lines of Python vs integrating external systems
6. **Educational Value**: For a learning project, understanding data structure is valuable
7. **Sufficient for Staging**: We don't need complex patient journeys yet
8. **Incremental Enhancement**: Can add complexity as needs grow

### Why Not MapEHR (Now)?

1. **Unavailable**: Not publicly accessible, no clear path to obtain
2. **Unknown Cost**: Could require commercial license
3. **Overkill**: We need 10-20 patients with basic vitals, not thousands with complex histories
4. **Template Compatibility**: Unclear if our OPT 1.4 templates work with OPT2-focused tool

**Note**: We will explore MapEHR/openFHIR for **plausibility research** once we need:
- More sophisticated clinical scenarios
- Standardized data generation patterns
- Complex multi-system patient histories
- FHIR integration capabilities

### Why Not Synthea + fhir-bridge?

1. **Complexity**: Adds Java dependency (Synthea) + conversion layer (fhir-bridge)
2. **Deployment Overhead**: Two additional services on Railway
3. **Learning Curve**: Need to understand FHIR → openEHR mapping
4. **Overkill for V1**: Synthea generates years of patient history; we need basic vitals

**Note**: Synthea remains a strong option if we need realistic longitudinal data later.

## Consequences

### Positive

- ✅ **Fast to implement**: Can be done in ~2 hours
- ✅ **No blockers**: No vendor contacts, licenses, or external approvals
- ✅ **Simple deployment**: Runs as Railway deployment hook or manual script
- ✅ **Transparent**: Full visibility into what data is generated
- ✅ **Customizable**: Easy to adjust for specific test scenarios
- ✅ **No ongoing costs**: No licensing fees or API usage charges
- ✅ **Git-friendly**: Seed script logic versioned in repository

### Negative

- ⚠️ **Manual value ranges**: Must research clinical norms ourselves
- ⚠️ **Limited sophistication**: No statistical distributions or complex calculations initially
- ⚠️ **Maintenance burden**: Must update script as templates evolve
- ⚠️ **No FHIR integration**: Can't easily test FHIR workflows

### Neutral

- 🔄 **Incremental approach**: Can migrate to specialized tools later
- 🔄 **Educational trade-off**: More hands-on work, more learning

## Mitigation Strategies

To address the negative consequences:

1. **Clinical Value Research**: Reference medical guidelines for realistic ranges
   ```python
   # Based on WHO guidelines
   VITAL_SIGNS_RANGES = {
       "systolic_bp": (90, 140),      # mmHg (normal: 90-120)
       "diastolic_bp": (60, 90),       # mmHg (normal: 60-80)
       "pulse_rate": (60, 100),        # bpm (normal resting)
       "body_temp_c": (36.1, 37.5),   # Celsius (normal)
   }
   ```

2. **Template Helpers**: Create reusable composition builders
   ```python
   def build_vital_signs_flat_composition(
       systolic: int, diastolic: int, pulse: int, temp: float,
       recorded_at: datetime
   ) -> dict[str, Any]:
       # Encapsulate FLAT path knowledge
   ```

3. **Seed Data Versioning**: Store generated datasets as JSON for reproducibility
   ```
   scripts/
   ├── seed.py              # Generation script
   └── fixtures/
       └── staging-v1.json  # Pre-generated data (optional)
   ```

4. **Railway Integration**: Use conditional environment-based seeding
   ```dockerfile
   # api/Dockerfile
   CMD sh -c "prisma migrate deploy && \
     if [ \"$RAILWAY_ENVIRONMENT\" = \"staging\" ]; then \
       python scripts/seed_staging.py; \
     fi && \
     uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
   ```

   Set `RAILWAY_ENVIRONMENT=staging` in Railway staging project environment variables.

## Alternatives Considered

### 1. Wait for MapEHR Access
**Rejected**: No timeline for when/if we could obtain access. Blocks staging deployment.

### 2. Manual Data Entry via UI
**Rejected**: Not reproducible, time-consuming, doesn't scale.

### 3. Commit Pre-generated JSON Compositions
**Rejected**: Less flexible than generation script, harder to customize.

### 4. Use Synthea Now
**Rejected**: Over-engineering for current needs. Can revisit when we need complex scenarios.

## Future Exploration: MapEHR/openFHIR

While we're implementing the custom script now, we will **explore MapEHR and openFHIR for plausibility research** to:

1. **Understand YAML mapping patterns**: Learn industry-standard approaches
2. **Evaluate OPT2 compatibility**: Assess if our templates need updates
3. **Compare data quality**: See how specialized tools generate distributions
4. **Assess FHIR integration**: Understand conversion patterns for future needs

**Action items**:
- [ ] Contact MapEHR vendor for trial access information
- [ ] Request openFHIR trial license
- [ ] Document findings in separate research document
- [ ] Evaluate migration path if tools prove valuable

This exploration is **non-blocking** and runs in parallel with the custom script implementation.

## Migration Path

If we adopt MapEHR/openFHIR or Synthea in the future:

1. **Script Remains Useful**: Custom script can generate quick test data during development
2. **Incremental Adoption**: Can use both approaches (script for quick tests, MapEHR for staging)
3. **Template Evolution**: Learning from YAML patterns can improve our manual builders
4. **FHIR Bridge**: If we add FHIR support, Synthea + fhir-bridge becomes attractive

The custom script is not wasted effort—it's a pragmatic V1 that unblocks progress.

## Related

- ADR-0001: Use openEHR for Clinical Data
- ADR-0003: openEHR Template Management
- ADR-0004: Direct httpx openEHR Integration
- Current seed script: `scripts/seed.py`
- Vital signs template: `api/templates/IDCR - Vital Signs Encounter.v1.opt`

## References

### Synthetic Data Tools
- MapEHR Documentation: https://mapehr.com/docs/synthetic-data/
- openFHIR: https://open-fhir.com/
- Synthea: https://github.com/synthetichealth/synthea
- ehrbase/fhir-bridge: https://github.com/ehrbase/fhir-bridge
- Faker (Python): https://faker.readthedocs.io/
- WHO Vital Signs Guidelines: https://www.who.int/data/gho/indicator-metadata-registry/imr-details/3155

### Railway Deployment
- [Set a Start Command - Railway Docs](https://docs.railway.com/guides/start-command)
- [How to run migrations and seeds - Railway Help](https://station.railway.com/questions/how-can-i-configure-the-migration-and-se-1b56c601)
- [Pre and post-deployment scripts - Railway Help](https://station.railway.com/questions/how-to-run-pre-and-post-deployment-scrip-914b6858)
- [Deployment Actions - Railway Docs](https://docs.railway.com/guides/deployment-actions)
