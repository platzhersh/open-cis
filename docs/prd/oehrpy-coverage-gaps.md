# oehrpy: Uncovered openEHR Use Cases

- **Created**: 2026-01-31
- **oehrpy version analyzed**: 0.1.0

Reference document for planning future oehrpy SDK enhancements based on gaps identified against the [openEHR REST API specification](https://specifications.openehr.org/releases/ITS-REST/latest/).

## Current Coverage

oehrpy today covers:

- **EHR Management**: create, get, get by subject
- **Compositions**: create, get (raw + formatted), delete
- **AQL**: execute ad-hoc queries
- **Templates**: list, upload, get info (ADL 1.4)
- **Composition Building**: `VitalSignsBuilder` (FLAT format)
- **RM Models**: 134 Pydantic classes (available but unused in Open CIS)
- **OPT Parser / Template Generator**: available but unused

---

## High-Value Gaps

### 1. Composition Update / Amendment

**openEHR endpoint**: `PUT /ehr/{ehr_id}/composition/{uid}`

Currently compositions can only be created or deleted. There is no way to amend or correct an existing record. Real clinical workflows require modifications (corrections, addenda, status changes) that preserve the original and create a new version.

**SDK surface**: `update_composition(ehr_id, uid, template_id, composition, format)`

---

### 2. Composition Versioning

**openEHR endpoints**:
- `GET /ehr/{ehr_id}/composition/{uid}?version_at_time=...`
- `GET /ehr/{ehr_id}/versioned_composition/{uid}/version`
- `GET /ehr/{ehr_id}/versioned_composition/{uid}/version/{version_uid}`

No way to retrieve prior versions of a composition or list version history. Required for audit, clinical governance, and medico-legal record keeping.

**SDK surface**: `get_composition_at_version()`, `list_composition_versions()`, `get_versioned_composition()`

---

### 3. Contribution (Audit Trail)

**openEHR endpoints**:
- `GET /ehr/{ehr_id}/contribution/{uid}`
- `POST /ehr/{ehr_id}/contribution`

Contributions are atomic changesets grouping one or more composition changes with audit metadata (committer, time, change type, description). Essential for tracking who changed what and when.

**SDK surface**: `get_contribution()`, `create_contribution()`, plus a `Contribution` model class

---

### 4. EHR Directory

**openEHR endpoints**:
- `PUT /ehr/{ehr_id}/directory`
- `GET /ehr/{ehr_id}/directory`
- `DELETE /ehr/{ehr_id}/directory`

Folder structures for organizing compositions within an EHR (e.g., by episode, department, encounter type). Without this, all compositions exist as a flat list.

**SDK surface**: `create_directory()`, `get_directory()`, `update_directory()`, `delete_directory()`

---

### 5. Additional Composition Builders

Only `VitalSignsBuilder` exists. Common clinical document types that need builders:

- Medication orders
- Problem / diagnosis lists
- Lab results / pathology reports
- Encounter / progress notes
- Discharge summaries

oehrpy already has an OPT parser and template generator that could auto-generate builders from any OPT file. This capability is untapped.

**SDK surface**: `MedicationOrderBuilder`, `ProblemListBuilder`, or a generic `CompositionBuilder.from_template(opt_path)`

---

## Medium-Value Gaps

### 6. EHR Status Updates

**openEHR endpoint**: `PUT /ehr/{ehr_id}/ehr_status`

Update EHR metadata such as subject demographics link, modifiable flag, or marking an EHR as inactive.

**SDK surface**: `update_ehr_status(ehr_id, status)`

---

### 7. Stored / Registered Queries

**openEHR endpoints**:
- `PUT /definition/query/{qualified_query_name}`
- `GET /definition/query/{qualified_query_name}`
- `GET /query/{qualified_query_name}` (execute stored query)

Register reusable named AQL queries on the server and execute them by name with parameters. Avoids sending full query text on every request.

**SDK surface**: `register_query()`, `get_query()`, `execute_stored_query()`

---

### 8. Archetype / Definition Management

**openEHR endpoints**:
- `GET /definition/archetype`
- `GET /definition/archetype/{archetype_id}`
- `POST /definition/archetype`

Discover, retrieve, and upload archetypes. Currently only ADL 1.4 templates are managed.

**SDK surface**: `list_archetypes()`, `get_archetype()`, `upload_archetype()`

---

### 9. AQL Builder (complete the existing API)

oehrpy has a fluent AQL builder, but Open CIS uses raw query strings exclusively. The builder likely needs:

- Better documentation / examples
- Support for common query patterns (temporal, aggregation)
- Parameter binding helpers
- Integration with RM model field paths

---

## Priority Matrix

| Use Case | Clinical Importance | Estimated Effort | Priority |
|---|---|---|---|
| Composition Update | Critical | Low | P0 |
| Composition Versioning | Critical | Low | P0 |
| Contributions / Audit | High | Medium | P1 |
| Additional Builders | High | Medium | P1 |
| EHR Directory | Medium | Medium | P2 |
| Stored Queries | Medium | Low | P2 |
| EHR Status Updates | Medium | Low | P2 |
| Archetype Management | Low | Low | P3 |
| AQL Builder completion | Low | Medium | P3 |
