# CH VACD ↔ openEHR mapping (vaccination records)

Template: `Open CIS - Vaccination Record.v1` — COMPOSITION (event) →
ACTION.medication (ism_transition *completed*) with vaccine product details.

| CH VACD (FHIR) | openEHR / FLAT item |
|---|---|
| `Immunization.vaccineCode` (Swissmedic CS) | `immunisation/vaccine` (DV_CODED_TEXT, terminology = CS URL) |
| `protocolApplied.targetDisease` (SNOMED CT) | `immunisation/target_disease:n` (DV_CODED_TEXT) |
| `protocolApplied.doseNumberPositiveInt` | `immunisation/dose_number` |
| `occurrenceDateTime` | `context/start_time`, `immunisation/time` |
| `lotNumber` (`"-"` → null) | `immunisation/batch_identifier` |
| `performer → PractitionerRole → Practitioner/Organization` | `performer_name`, `organisation_name` |
| `Composition.author` (Patient vs. provider) | `author_type` (`patient`/`practitioner`), composer name |
| `Bundle.identifier` / `Immunization.id` | `external_identifier` (idempotency) |
| `Immunization.status` | `status` |

## Status / open items

- **The `.opt` template is not yet authored or uploaded.** It needs CKM
  archetype selection (check IPS immunisation first) and validation against a
  running EHRBase; the FLAT ids in `api/src/vaccinations/flat.py` must then be
  verified against the web template (see ADR-0008/0009). The template is
  deliberately not in `REQUIRED_TEMPLATES` yet.
- Export is not yet validated against the CH VACD IG (HAPI/fhir.ch validator).
- No UI yet.
