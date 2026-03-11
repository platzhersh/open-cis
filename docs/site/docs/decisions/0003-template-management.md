# ADR-0003: openEHR Template Management

**Date:** 2026-01-03 | **Status:** Accepted

## Context

Open CIS uses EHRBase as its openEHR Clinical Data Repository. EHRBase requires Operational Templates (OPT) to be registered before compositions can be created against them. Without the template, composition creation fails with a 400 error.

Templates define the structure of clinical data by constraining openEHR archetypes. For example, a "Vital Signs" template combines observation archetypes for blood pressure and pulse within an encounter composition archetype.

Templates must be uploaded to EHRBase before the application can store clinical data, but developers may forget this step when setting up a new environment. Different environments like development, staging, and production need consistent template configurations to ensure the same clinical data structures work everywhere. Creating proper OPT files from scratch requires specialized tooling and expertise that would slow down development and introduce a barrier to entry for new contributors.

## Decision

We will implement automatic template registration on API startup, using pre-built templates from the openEHR community.

1. **Template Storage**: OPT files are stored in `api/templates/` directory, named `{template_id}.opt`
2. **Startup Registration**: On API startup, the application checks which templates are already registered in EHRBase and uploads any missing required templates
3. **Required Templates**: The list of required templates is maintained in `src/ehrbase/templates.py`
4. **Graceful Degradation**: If EHRBase is unavailable or template upload fails, the API continues to start with a warning logged

### Template Source

We use the **IDCR - Vital Signs Encounter.v1** template from the [RippleOSI/Ripple-openEHR](https://github.com/RippleOSI/Ripple-openEHR) repository, a production-ready template created by clinical informaticists.

### Template Structure

```
COMPOSITION (openEHR-EHR-COMPOSITION.encounter.v1)
└── SECTION (openEHR-EHR-SECTION.vital_signs.v1)
    ├── OBSERVATION (blood_pressure.v1)
    ├── OBSERVATION (pulse.v1)
    ├── OBSERVATION (body_temperature.v1)
    ├── OBSERVATION (respiration.v1)
    ├── OBSERVATION (indirect_oximetry.v1)
    ├── OBSERVATION (avpu.v1)
    ├── OBSERVATION (news_uk_rcp.v1)
    └── EVALUATION (clinical_synopsis.v1)
```

## Consequences

### Positive

- New environments automatically get required templates
- Developers don't need to manually upload templates
- Template configuration is version-controlled
- Consistent behavior across environments
- Using community templates saves development time

### Negative

- OPT files are large and complex XML (~256KB for vital signs)
- Using older archetype versions (v1 vs v2)
- Dependent on external template sources for updates
- Template upload adds startup time (minimal)
