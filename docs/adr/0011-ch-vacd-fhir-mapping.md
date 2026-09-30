# ADR-0011: Hand-written Python mapping for CH VACD ↔ openEHR

**Date:** 2026-09-30

## Status

Accepted (OEH-93)

## Context

Vaccination records are imported from CH VACD FHIR Bundles (single documents or
IHE XDM exports from an EPD), stored as openEHR compositions in EHRBase, and
exported back as CH VACD Bundles. A mapping layer is needed in both directions.

## Decision

Write the mapping by hand in Python (`api/src/vaccinations/`): a parser
(FHIR → `VaccinationRecord`), a FLAT builder/parser, and a Bundle exporter.
The FLAT layout is kept in one module (`flat.py`); reading is suffix-based.

## Alternatives considered (rejected for now)

- **FHIRConnect / openFHIR mapping definitions** — declarative and reusable,
  but adds a Java mapping engine (openFHIR) as a new service and a mapping
  DSL to learn, for a single resource type. Worth revisiting if more CH
  documents (CH LAB, recommendations) are added.
- **`fhir.resources` / full FHIR models** — heavier than needed; only a small,
  fixed subset of the Bundle is read.

## Consequences

- Placeholders (`"-"`, `"?"`) are normalised to null on import and omitted on
  export; they are never re-invented.
- Idempotency key: `Bundle.identifier`, else `Immunization.id`.
- Composition author = Patient is preserved as `author_type` on the ACTION.
- Probable duplicates (same vaccine code + same date) are reported, never
  merged or dropped.
