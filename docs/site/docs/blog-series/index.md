# Blog Series

Open CIS was built in public and documented through a six-part blog series on Medium. The series covers the journey from initial architecture decisions to building a Python SDK for openEHR.

---

## Part 1: Building Open CIS

**[Building Open CIS: A Minimal Clinical Information System on openEHR](https://medium.com/@platzh1rsch/building-open-cis-a-minimal-clinical-information-system-on-openehr-7d3c5d75bae8)**

The project motivation and introduction. Why build a CIS from scratch? What is openEHR and why does it matter? Setting up EHRBase with Docker Compose and making the first API calls.

**Key topics:** Project goals, openEHR introduction, EHRBase setup, Docker Compose infrastructure

---

## Part 2: The Clinical Modeling Stack

**[Part 2: The Clinical Modeling Stack](https://medium.com/@platzh1rsch/building-open-cis-part-2-the-clinical-modeling-stack-221c019e65ca)**

A deep dive into how openEHR models clinical data. Archetypes as reusable building blocks, templates as use-case-specific constraints, and the Clinical Knowledge Manager (CKM) as the community hub for clinical models.

**Key topics:** Archetypes, templates, CKM, clinical modeling workflow, two-level modeling

**Related docs:** [openEHR Concepts](../architecture/openehr.md), [ADR-0003: Template Management](../decisions/0003-template-management.md)

---

## Part 2b: Template Formats and the Flat Format Deep Dive

**[Part 2b: Template Formats and the Flat Format Deep Dive](https://medium.com/@platzh1rsch/building-open-cis-part-2b-template-formats-and-the-flat-format-deep-dive-0ed3ff0acfed)**

The practical side of working with templates. Compares OPT format, FLAT JSON, structured JSON, and canonical JSON. Deep dive into FLAT format path syntax, context fields, and the pitfalls of working with EHRBase's FLAT API.

**Key topics:** OPT format, FLAT vs structured vs canonical JSON, path syntax, EHRBase API quirks

**Related docs:** [openEHR Concepts](../architecture/openehr.md)

---

## Part 3: Going SDK-less

**[Part 3: Going SDK-less -- Our Architecture Decisions](https://medium.com/@platzh1rsch/building-open-cis-part-3-going-sdk-less-our-architecture-decisions-134786e090b5)**

Why we chose to use direct HTTP calls with httpx instead of an existing SDK. Evaluates the available options (Java SDK, pyEHR, nothing in Python), introduces the ADR process, and explains the lightweight client approach.

**Key topics:** SDK evaluation, ADR process, httpx integration, thin client pattern

**Related docs:** [ADR-0004: Direct httpx Integration](../decisions/0004-direct-httpx-integration.md)

---

## Part 4: The openEHR SDK Landscape

**[Part 4: The openEHR SDK Landscape](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279)**

A comprehensive survey of the openEHR SDK ecosystem. The Java SDK's 20+ modules, the dormant pyEHR project, and the gap in the Python ecosystem. This analysis directly led to the creation of oehrpy.

**Key topics:** EHRbase Java SDK, pyEHR, SDK gap analysis, Python ecosystem gap

**Related docs:** [oehrpy Overview](../oehrpy/index.md)

---

## Part 5: oehrpy -- A Python SDK for openEHR

**[Part 5: oehrpy -- A Python SDK for openEHR](https://medium.com/@platzh1rsch/building-open-cis-part-5-oehrpy-a-python-sdk-for-openehr-c9c90f46d075)**

The creation of oehrpy, a Python SDK that fills the gap identified in Part 4. Covers the design philosophy, 134 Pydantic RM classes, async EHRBase client, VitalSignsBuilder, FLAT serialization, and the OPT parser.

**Key topics:** oehrpy design, Reference Model in Pydantic, VitalSignsBuilder, FLAT serialization, async client

**Related docs:** [oehrpy Overview](../oehrpy/index.md), [oehrpy Integration](../oehrpy/integration.md), [oehrpy Coverage & Roadmap](../oehrpy/coverage.md)

---

## Reading Order

The series is designed to be read in order, but each part also stands on its own:

| If you want to... | Start with... |
|---|---|
| Understand the project and openEHR basics | Part 1 |
| Learn about clinical data modeling | Part 2 |
| Understand the technical data formats | Part 2b |
| See how architecture decisions are made | Part 3 |
| Survey the openEHR tooling ecosystem | Part 4 |
| Learn about building a Python openEHR SDK | Part 5 |
