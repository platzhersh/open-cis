# ADR-0006: FHIR Terminology Server Selection

## Status

Accepted

## Context

Open CIS stores clinical data in EHRBase using openEHR's data model, including `DV_CODED_TEXT` elements that reference external terminologies like SNOMED CT, ICD-10, and LOINC. However, the system currently lacks the ability to:

1. **Validate codes** — Users can enter invalid or deprecated terminology codes
2. **Search terminologies** — No autocomplete or browsing for clinicians entering coded data
3. **Expand value sets** — Template constraints reference value sets we cannot resolve
4. **Navigate hierarchies** — Cannot leverage SNOMED CT's is-a relationships for queries
5. **Translate codes** — Cannot map between terminologies (e.g., SNOMED → ICD-10)

Ian McNicoll (openEHR Industry Partner) provided feedback on the Open CIS article series suggesting integration of a FHIR terminology server as a natural next step for any clinical system.

### Options Considered

We evaluated four terminology server options:

| Server | Type | License | Primary Focus |
|--------|------|---------|---------------|
| **Snowstorm Lite** | Dedicated terminology server | Apache 2.0 | SNOMED CT specialist |
| **Snowstorm (Full)** | Dedicated terminology server | Apache 2.0 | SNOMED CT specialist |
| **HAPI FHIR JPA** | General FHIR server with terminology | Apache 2.0 | Multi-purpose |
| **Ontoserver** | Dedicated terminology server | Commercial | Enterprise terminology |

## Decision

We will use **Snowstorm Lite** as the FHIR terminology server for Open CIS.

## Rationale

### Why Snowstorm Lite over HAPI FHIR?

| Factor | Snowstorm Lite | HAPI FHIR | Winner |
|--------|---------------|-----------|--------|
| **Memory footprint** | ~500MB running | 2-4GB minimum | Snowstorm Lite |
| **SNOMED CT support** | Native, official (SNOMED International) | Import-based, basic | Snowstorm Lite |
| **ECL support** | Full Expression Constraint Language | Partial/basic | Snowstorm Lite |
| **Setup complexity** | Single container, no external DB | Requires PostgreSQL | Snowstorm Lite |
| **SNOMED implicit maps** | Native (ICD-10 maps, refsets) | Not supported | Snowstorm Lite |
| **Multi-terminology** | Limited (one SNOMED edition) | Full (SNOMED + LOINC + RxNorm + custom) | HAPI FHIR |
| **Custom CodeSystems** | Limited format | Full FHIR API support | HAPI FHIR |
| **Subsumption inference** | Excellent | Limited | Snowstorm Lite |
| **Community/docs** | SNOMED International maintained | Large community, extensive docs | Tie |

**Key deciding factors:**

1. **SNOMED CT is primary** — For a CIS, SNOMED CT is the core clinical terminology. Snowstorm Lite provides first-class support as the official SNOMED International server.

2. **ECL is essential** — Expression Constraint Language enables powerful value set definitions like "all descendants of diabetes" (`<< 73211009`). HAPI FHIR's ECL support is limited.

3. **Resource constraints** — Open CIS follows a minimal-footprint philosophy. Snowstorm Lite's 500MB requirement fits alongside EHRBase, while HAPI FHIR would double our memory needs.

4. **Focused scope** — We don't currently need RxNorm (medications) or extensive custom terminologies. SNOMED CT + ICD-10 + LOINC covers our clinical data needs, and Snowstorm Lite supports all three.

5. **Implicit ConceptMaps** — Snowstorm Lite provides SNOMED-to-ICD-10 mappings out of the box via SNOMED reference sets. HAPI FHIR requires manual ConceptMap creation.

### Why not Full Snowstorm?

Full Snowstorm requires Elasticsearch and 8GB+ RAM. For a learning project, Snowstorm Lite provides the same FHIR API with minimal infrastructure. We can migrate to full Snowstorm if we need:
- Multiple SNOMED editions simultaneously
- Authoring/editing capabilities
- High-availability clustering

### Why not Ontoserver?

Ontoserver is excellent (used by NHS England, Australian NCTS) but requires a commercial license outside Australia. For an open-source learning project, Apache-licensed options are preferred.

## Detailed Comparison

### SNOMED CT Features

| Feature | Snowstorm Lite | HAPI FHIR |
|---------|---------------|-----------|
| RF2 import | ✅ Native | ✅ Via CLI |
| ECL queries | ✅ Full | ⚠️ Basic |
| Post-coordination | ✅ Supported | ❌ No |
| Implicit ValueSets | ✅ Native | ⚠️ Partial |
| Implicit ConceptMaps | ✅ Native | ❌ No |
| Reference set support | ✅ Full | ⚠️ Limited |
| Edition/version URIs | ✅ Full support | ✅ Supported |
| Hierarchy navigation | ✅ Optimized | ⚠️ Basic |

### FHIR Operations Support

| Operation | Snowstorm Lite | HAPI FHIR |
|-----------|---------------|-----------|
| `CodeSystem/$lookup` | ✅ | ✅ |
| `CodeSystem/$validate-code` | ✅ | ✅ |
| `CodeSystem/$subsumes` | ✅ Excellent | ⚠️ Limited inference |
| `ValueSet/$expand` | ✅ | ✅ |
| `ValueSet/$validate-code` | ✅ | ✅ |
| `ConceptMap/$translate` | ✅ SNOMED maps | ⚠️ Explicit only |
| `CodeSystem/$find-matches` | ❌ | ❌ |
| `ConceptMap/$closure` | ❌ | ✅ |

### Additional Terminology Support

| Terminology | Snowstorm Lite | HAPI FHIR |
|-------------|---------------|-----------|
| SNOMED CT | ✅ Native | ✅ Import |
| LOINC | ✅ Supported | ✅ Supported |
| ICD-10 | ✅ ClaML format | ✅ Supported |
| ICD-10-CM | ✅ Supported | ✅ Supported |
| RxNorm | ❌ | ✅ Supported |
| Custom CodeSystems | ⚠️ Specific format | ✅ Full API |
| HL7 FHIR ValueSets | ⚠️ Manual load | ✅ Built-in |

### Operational Characteristics

| Aspect | Snowstorm Lite | HAPI FHIR |
|--------|---------------|-----------|
| Docker image | ~200MB | ~400MB |
| External dependencies | None (Lucene embedded) | PostgreSQL or H2 |
| Startup time | ~30 seconds | ~60 seconds |
| SNOMED import time | ~5 minutes | ~30-60 minutes |
| Content syndication | ✅ From MLDS | ❌ Manual |
| Hot reload | ❌ | ✅ |
| Clustering | ❌ | ✅ |

## Consequences

### Positive

- **Minimal resource overhead** — 500MB RAM fits our infrastructure constraints
- **First-class SNOMED support** — Official server with complete ECL, implicit value sets, and concept maps
- **Simple deployment** — Single Docker container, no database dependency
- **Easy SNOMED updates** — Can auto-syndicate from SNOMED International MLDS
- **Fast queries** — Optimized Lucene index for terminology operations

### Negative

- **Single SNOMED edition** — Cannot host Swiss and International editions simultaneously
- **No RxNorm** — If medication terminology needed, requires second server or migration
- **Limited custom terminologies** — Must transform to specific format for import
- **No POST CodeSystem** — Cannot dynamically add terminologies via FHIR API
- **Single instance** — No built-in clustering for high availability

### Neutral

- **LOINC and ICD-10 supported** — Covers our lab and diagnosis coding needs
- **Migration path exists** — Can move to full Snowstorm or HAPI FHIR if requirements change

## Migration Path

If future requirements exceed Snowstorm Lite capabilities:

1. **Need multiple SNOMED editions** → Migrate to full Snowstorm (same API, more capacity)
2. **Need RxNorm** → Add HAPI FHIR alongside Snowstorm Lite, or migrate fully to HAPI FHIR
3. **Need custom terminologies** → Evaluate HAPI FHIR or transform to Snowstorm format
4. **Need enterprise features** → Evaluate Ontoserver commercial license

The FHIR terminology API is standardized, so our application code (TerminologyClient) will work with any compliant server with minimal changes.

## Implementation

### Docker Compose Addition

```yaml
terminology-server:
  image: snomedinternational/snowstorm-lite:latest
  container_name: open-cis-terminology
  ports:
    - "8081:8080"
  volumes:
    - terminology-data:/app/lucene-index
  environment:
    - INDEX_PATH=lucene-index/data
    - ADMIN_PASSWORD=${TERMINOLOGY_ADMIN_PASSWORD:-admin}
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/fhir/metadata"]
    interval: 30s
    timeout: 10s
    retries: 5
  restart: unless-stopped

volumes:
  terminology-data:
```

### SNOMED CT Loading

```bash
# Load SNOMED CT International Edition
curl -u admin:${TERMINOLOGY_ADMIN_PASSWORD} \
  --form file=@SnomedCT_InternationalRF2_PRODUCTION_20240101T120000Z.zip \
  --form version-uri="http://snomed.info/sct/900000000000207008/version/20240101" \
  http://localhost:8081/fhir-admin/load-package
```

### Environment Variables

```bash
# .env additions
TERMINOLOGY_SERVER_URL=http://localhost:8081/fhir
TERMINOLOGY_ADMIN_PASSWORD=secure-password-here
TERMINOLOGY_CACHE_TTL=300
```

## References

- [PRD-0006: FHIR Terminology Server Integration](../prd/0006-terminology-server.md)
- [Snowstorm Lite GitHub](https://github.com/IHTSDO/snowstorm-lite)
- [Snowstorm (Full) GitHub](https://github.com/IHTSDO/snowstorm)
- [HAPI FHIR Documentation](https://hapifhir.io/)
- [FHIR Terminology Services Specification](https://www.hl7.org/fhir/terminology-service.html)
- [Comparing FHIR Terminology Services (Rath Panyowat)](https://en.rath.asia/blog/2025/04/27/comparing-3-fhir-terminology-services/)
- [HL7 Australia Terminology Server Comparison](https://confluence.hl7.org/display/HAFWG/Terminology+Server+Comparison)
- [openEHR Discourse: Ian McNicoll's feedback](https://discourse.openehr.org/t/building-an-open-cis-article-series-on-implementing-a-minimal-cis-with-ehrbase/11690)
- [openEHR Discourse: Terminology service in CKM](https://discourse.openehr.org/t/use-of-a-terminology-service-in-ckm/3899)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-31 | Chregi | Initial decision |
