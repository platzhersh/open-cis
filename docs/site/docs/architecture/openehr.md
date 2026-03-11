# openEHR Concepts

This page introduces the core openEHR concepts used in Open CIS. If you're new to openEHR, start here.

## What is openEHR?

[openEHR](https://www.openehr.org/) is an open standard for electronic health records. Its key innovation is **two-level modeling**: the software (Reference Model) is separated from the clinical knowledge (archetypes and templates). This means clinical data models can evolve without changing the software.

## Core Concepts

### EHR (Electronic Health Record)

An EHR is a container for all clinical data belonging to one patient. In Open CIS, each patient gets exactly one EHR in EHRBase.

```
Patient (MRN: P-001) ──── EHR (ehr_id: abc-123-...)
                            ├── Composition (Vital Signs, 2026-01-15)
                            ├── Composition (Vital Signs, 2026-01-20)
                            └── Composition (Encounter Note, 2026-02-01)
```

### Composition

A **composition** is a clinical document -- a single unit of clinical information committed to the EHR. Examples include a vital signs reading, a consultation note, or a prescription.

Each composition:

- Belongs to one EHR
- Is based on a template
- Is versioned (every update creates a new version)
- Has audit metadata (who, when, where)

### Archetype

An **archetype** is a reusable, maximal definition of a clinical concept. Archetypes are maintained by the international openEHR community in the [Clinical Knowledge Manager (CKM)](https://ckm.openehr.org/).

Examples:

- `openEHR-EHR-OBSERVATION.blood_pressure.v1` -- defines everything about a blood pressure measurement
- `openEHR-EHR-OBSERVATION.pulse.v1` -- defines pulse/heart rate measurement
- `openEHR-EHR-COMPOSITION.encounter.v1` -- defines an encounter document

Archetypes are **maximal** -- they contain every possible data point. A blood pressure archetype includes fields for body position, cuff size, device, exertion level, and more. Most applications only need a subset.

### Template

A **template** constrains one or more archetypes for a specific use case. Open CIS uses the **IDCR Vital Signs Encounter** template, which combines:

```
COMPOSITION (encounter)
└── SECTION (vital_signs)
    ├── OBSERVATION (blood_pressure)
    ├── OBSERVATION (pulse)
    ├── OBSERVATION (body_temperature)
    ├── OBSERVATION (respiration)
    ├── OBSERVATION (indirect_oximetry)
    └── ...
```

Templates are exported as **OPT** (Operational Template) files and uploaded to EHRBase before they can be used.

### AQL (Archetype Query Language)

**AQL** is a query language for retrieving clinical data from an openEHR repository. It looks like SQL but navigates the archetype structure:

```sql
SELECT
    c/context/start_time/value as time,
    o/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude as systolic,
    o/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude as diastolic
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.blood_pressure.v1]
WHERE e/ehr_id/value = :ehr_id
```

Key differences from SQL:

- `CONTAINS` replaces `JOIN` -- it navigates the archetype hierarchy
- Paths like `o/data[at0001]/events[at0006]/...` reference archetype node IDs
- Queries are portable across any openEHR system using the same archetypes

## FLAT Format

Open CIS uses the **FLAT format** to create compositions. FLAT format represents a composition as a flat dictionary of paths and values:

```json
{
    "ctx/language": "en",
    "ctx/territory": "US",
    "ctx/composer_name": "Dr. Smith",
    "vital_signs/blood_pressure/systolic|magnitude": 120,
    "vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
    "vital_signs/blood_pressure/diastolic|magnitude": 80,
    "vital_signs/blood_pressure/diastolic|unit": "mm[Hg]",
    "vital_signs/pulse_heart_beat/rate|magnitude": 72,
    "vital_signs/pulse_heart_beat/rate|unit": "/min"
}
```

This is simpler than the canonical JSON format (which mirrors the full RM hierarchy) but requires knowledge of the template-specific path structure. See [Part 2b of the blog series](../blog-series/index.md) for a deep dive into FLAT format.

## Learn More

- [openEHR Specifications](https://specifications.openehr.org/)
- [Clinical Knowledge Manager](https://ckm.openehr.org/)
- [EHRBase Documentation](https://ehrbase.readthedocs.io/)
- [openEHR REST API Specification](https://specifications.openehr.org/releases/ITS-REST/latest/)
- [Blog Series Part 2: The Clinical Modeling Stack](https://medium.com/@platzh1rsch/building-open-cis-part-2-the-clinical-modeling-stack-221c019e65ca)
