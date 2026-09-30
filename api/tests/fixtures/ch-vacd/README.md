# CH VACD test fixtures (anonymised)

16 FHIR document Bundles (profile `ch-vacd-document-immunization-administration`), each with one
Composition + Patient + Practitioner + PractitionerRole + Organization + Immunization.

Derived from a real Swiss EPD export (IHE XDM, Post Sanela), anonymised:
- Patient replaced by synthetic "Hans Muster", DOB 1985-01-01, dummy EPR-SPID
- Organisation names replaced with "Test Vaccination Site A–F"
- All UUIDs regenerated; narrative text removed
- All dates shifted by a fixed offset (intervals between doses preserved)

Known data-quality cases (keep them, they are useful test cases):
- Composition author is the Patient (self-entered records, not provider-sourced)
- lotNumber is "-" in all records; Practitioner names are "?"
- Same vaccine + same date with conflicting dose numbers (likely duplicates):
  05+07 (FSME), 06+08 (FSME), 10+12 (Spikevax), 11+13 (Spikevax)
- 16 has Organization name "-"
