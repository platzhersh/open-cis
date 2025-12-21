# ADR 0001: Use openEHR for Clinical Data

## Status

Accepted

## Context

We need a data model and storage solution for clinical data (observations, diagnoses, medications, encounters). Options considered:

1. **Custom relational schema** - Design our own tables for each clinical concept
2. **HL7 FHIR** - Use FHIR resources and a FHIR server
3. **openEHR** - Use openEHR archetypes and EHRBase

## Decision

We will use **openEHR** with **EHRBase** as the clinical data repository.

## Rationale

- **Archetype-based modeling**: Clinical concepts are defined in reusable, version-controlled archetypes maintained by the openEHR community
- **Separation of concerns**: Data model (archetypes) is separate from software implementation
- **Query language**: AQL (Archetype Query Language) provides powerful querying across clinical structures
- **EHRBase maturity**: Open-source, actively maintained, good REST API
- **Learning opportunity**: Explore openEHR ecosystem for clinical data management

## Consequences

### Positive
- Rich clinical modeling with community-maintained archetypes
- Standardized data that could interoperate with other openEHR systems
- AQL for complex clinical queries

### Negative
- Learning curve for openEHR concepts (compositions, archetypes, templates)
- Need to manage two databases (EHRBase + app DB)
- Template creation/management adds complexity

### Mitigations
- Start with simple templates
- Keep app-specific data (users, audit) in separate PostgreSQL database
- Use PatientRegistry to link MRN to EHR ID
