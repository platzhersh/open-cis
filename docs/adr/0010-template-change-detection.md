# 10. Template Change Detection on Startup

Date: 2026-04-10

## Status

Accepted

## Context

ADR-0003 established that Open CIS automatically uploads required Operational
Templates (OPT) to EHRBase on API startup. The original implementation always
attempted to POST every template, relying on EHRBase's 409 Conflict response
to signal that the template already existed.

This caused two problems in practice:

1. **Noisy error logs.** Every startup produced 409 errors for every template
   that was already registered. While these were handled gracefully (treated as
   success), they cluttered logs and made it harder to spot real failures. On
   Railway staging, the log output looked like:

   ```
   ERROR: EHRBase error: Request failed: 409 - {"error":"Conflict",
          "message":"Operational template with this template ID already exists: ..."}
   ```

2. **Unpredictable 500 errors.** Some EHRBase versions (notably v2.x with
   certain PostgreSQL configurations) respond with 500 Internal Server Error
   instead of 409 when a duplicate template is uploaded. This caused startup
   warnings that suggested a real failure, even though the template was
   correctly registered.

3. **No update path.** If a template was modified locally (e.g., a new
   archetype constraint or a bugfix in the OPT), the only way to propagate
   the change was to manually delete the template from EHRBase and restart the
   API — or redeploy with a clean EHRBase database. There was no mechanism to
   detect that the local OPT differed from the registered one.

### Constraints

- EHRBase's `POST /rest/openehr/v1/definition/template/adl1.4` rejects
  duplicates (409 or 500 depending on version); it does not upsert.
- EHRBase v2 supports `PUT /rest/openehr/v1/definition/template/adl1.4/{id}`
  for updating an existing template, but the update may be rejected if existing
  compositions reference the template and the change is not backwards-compatible.
- EHRBase returns the stored OPT XML via
  `GET /rest/openehr/v1/definition/template/adl1.4/{id}` with
  `Accept: application/xml`, but it may reformat the XML (attribute order,
  namespace declarations, empty element syntax) compared to the original file.
- The oehrpy SDK (v0.7.0) does not provide `get_template_opt()`,
  `update_template()`, or `delete_template()` methods (documented as P0 gaps
  in PRD-0010).

## Decision

We implement a **compare-before-upload** strategy using canonical XML hashing.
On startup, for each required template:

1. **Fetch** the existing OPT XML from EHRBase via a direct HTTP GET
   (`GET /rest/openehr/v1/definition/template/adl1.4/{template_id}` with
   `Accept: application/xml`).
2. **Hash** both the local and remote OPT using XML Canonical Form (C14N) via
   Python's `xml.etree.ElementTree.canonicalize()`, then SHA-256. C14N
   normalises attribute order, namespace declarations, and empty element syntax
   so that semantically identical documents produce the same hash.
3. **Compare** hashes:
   - **Match** — template is up to date; skip upload entirely.
   - **Mismatch** — template has changed; attempt a `PUT` update.
   - **No remote OPT** (template not registered or fetch failed) — `POST` upload
     as before.

### New client methods

Two methods are added to `EHRBaseClient` in `api/src/ehrbase/client.py`, using
direct HTTP calls to the oehrpy SDK's underlying httpx client (same pattern as
the existing `get_web_template()` and `delete_composition()` methods):

- `get_template_opt(template_id) -> str | None` — fetches the raw OPT XML.
- `update_template_opt(template_id, content) -> bool` — PUTs an updated OPT.

### Sync logic

A new `_sync_template()` function in `api/src/ehrbase/templates.py` encapsulates
the compare-and-act logic. `ensure_templates_registered()` delegates to it
instead of unconditionally calling `upload_template_file()`.

### Fallback on C14N failure

If `ET.canonicalize()` raises `ParseError` (e.g., EHRBase returns non-XML
content), the hash function falls back to a SHA-256 of the stripped raw text.
This is a safe fallback: in the worst case it produces a false mismatch,
triggering an unnecessary PUT update — which is the safe direction.

## Alternatives Considered

### Keep the unconditional POST approach

Continue uploading every template on startup and suppress 409 errors.

**Rejected.** This is the status quo. It produces noisy logs, masks real 500
errors, and provides no update path when templates change.

### Compare raw XML strings

Hash the raw bytes of the local file and the EHRBase response without
canonicalisation.

**Rejected.** EHRBase may reformat XML on storage (e.g., reorder attributes,
expand self-closing tags). Raw comparison would produce false mismatches,
triggering unnecessary PUT updates on every startup.

### Store a local hash/checksum file

Maintain a `.template-checksums` file alongside the OPT files, recording the
hash of the last successfully uploaded version.

**Rejected.** This adds state that can drift from reality (e.g., after a manual
EHRBase database reset). Comparing directly with EHRBase is the single source
of truth.

### Delete and re-upload on mismatch

Instead of PUT, use `DELETE` then `POST` when a template has changed.

**Rejected.** EHRBase may refuse to delete a template that has existing
compositions. The PUT approach is safer because EHRBase can validate backwards
compatibility before accepting the update. DELETE+POST also creates a window
where the template is unregistered, which could cause failures if requests
arrive concurrently during startup.

## Consequences

### Positive

- **Clean logs.** Unchanged templates produce a single `INFO: Template X is up
  to date` line instead of error-level 409/500 messages.
- **Automatic updates.** When a developer modifies an OPT file and deploys, the
  change is detected and applied via PUT without manual intervention.
- **Correct error reporting.** Real failures (EHRBase down, template rejected)
  are clearly distinguishable from the "already exists" noise.
- **No extra state.** The comparison uses EHRBase as the source of truth, with
  no local checksum files to maintain.

### Negative

- **Extra HTTP call per template.** Each startup now makes a GET request per
  template to fetch the existing OPT. For the current 2 templates this adds
  negligible latency (<100ms total).
- **PUT may be rejected.** If EHRBase cannot update a template because existing
  compositions would become invalid, the update fails and a warning is logged.
  Manual intervention (database reset or compatible template change) is required
  in this case. This is an EHRBase constraint, not a limitation of this
  approach.
- **C14N is not perfect.** If EHRBase introduces changes to the OPT that C14N
  does not normalise (e.g., adding server-generated comments), false mismatches
  will occur. The consequence is an unnecessary PUT attempt, which is harmless.

### Neutral

- The existing `upload_template_file()` function is retained for the "new
  template" code path and is unchanged.
- The startup sequence in `main.py` is unchanged — `ensure_templates_registered()`
  is still called first, followed by `warm_web_template_cache()`.

## File Locations

```
api/src/ehrbase/
├── client.py          # + get_template_opt(), update_template_opt()
└── templates.py       # + _xml_hash(), _sync_template(); updated ensure_templates_registered()

api/tests/unit/
└── test_template_sync.py   # Unit tests for hash and sync logic
```

## Related

- [ADR-0003: openEHR Template Management](./0003-openehr-template-management.md) — original template upload decision
- [ADR-0009: oehrpy Web Template Integration](./0009-oehrpy-web-template-integration.md) — Web Template caching on startup
- `docs/prd/0010-oehrpy-coverage-gaps.md` — documents missing `delete_template` / `update_template` in oehrpy SDK
