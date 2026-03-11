# Coverage & Roadmap

This page tracks what oehrpy covers today and what gaps remain against the [openEHR REST API specification](https://specifications.openehr.org/releases/ITS-REST/latest/).

## Current Coverage

oehrpy v0.1.0 covers:

- **EHR Management**: create, get, get by subject
- **Compositions**: create, get (raw + formatted), delete
- **AQL**: execute ad-hoc queries
- **Templates**: list, upload, get info (ADL 1.4)
- **Composition Building**: `VitalSignsBuilder` (FLAT format)
- **RM Models**: 134 Pydantic classes
- **OPT Parser / Template Generator**: available but unused in Open CIS

## High-Value Gaps

### Composition Update / Amendment

**Endpoint**: `PUT /ehr/{ehr_id}/composition/{uid}`

Currently compositions can only be created or deleted. Real clinical workflows require modifications (corrections, addenda) that preserve the original and create a new version.

### Composition Versioning

**Endpoints**: `GET ...?version_at_time=...`, versioned composition history

No way to retrieve prior versions or list version history. Required for audit, clinical governance, and medico-legal record keeping.

### Contribution (Audit Trail)

**Endpoints**: `GET/POST /ehr/{ehr_id}/contribution/{uid}`

Contributions are atomic changesets grouping composition changes with audit metadata. Essential for tracking who changed what and when.

### EHR Directory

**Endpoints**: `GET/PUT/DELETE /ehr/{ehr_id}/directory`

Folder structures for organizing compositions within an EHR (e.g., by episode or department).

### Additional Composition Builders

Only `VitalSignsBuilder` exists. Common templates that need builders:

- Medication orders
- Problem / diagnosis lists
- Lab results
- Encounter / progress notes
- Discharge summaries

The OPT parser and template generator could auto-generate builders from any OPT file -- this capability is available but untapped.

## Medium-Value Gaps

| Gap | Description |
|-----|-------------|
| **EHR Status Updates** | Update EHR metadata (subject link, modifiable flag) |
| **Stored Queries** | Register and execute named AQL queries on the server |
| **Archetype Management** | Discover, retrieve, and upload archetypes |
| **AQL Builder completion** | Better docs, common query patterns, aggregation support |

## Priority Matrix

| Use Case | Clinical Importance | Estimated Effort | Priority |
|---|---|---|---|
| Composition Update | Critical | Low | **P0** |
| Composition Versioning | Critical | Low | **P0** |
| Contributions / Audit | High | Medium | **P1** |
| Additional Builders | High | Medium | **P1** |
| EHR Directory | Medium | Medium | P2 |
| Stored Queries | Medium | Low | P2 |
| EHR Status Updates | Medium | Low | P2 |
| Archetype Management | Low | Low | P3 |
| AQL Builder completion | Low | Medium | P3 |

## Contributing

oehrpy is open source. Contributions for any of the gaps above are welcome:

- [oehrpy GitHub Repository](https://github.com/platzhersh/oehrpy)
- [Open CIS GitHub Repository](https://github.com/platzhersh/open-cis)
