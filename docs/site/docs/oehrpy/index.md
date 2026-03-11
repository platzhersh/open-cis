# oehrpy: Python SDK for openEHR

**[oehrpy](https://github.com/platzhersh/oehrpy)** is a Python SDK for openEHR that was born out of the Open CIS project. It provides type-safe composition building, Pydantic-based Reference Model classes, and an async EHRBase REST client.

## The Story

When building Open CIS, we discovered there was no actively maintained Python SDK for openEHR ([Part 4: The openEHR SDK Landscape](../blog-series/index.md)). The Java SDK exists but doesn't help a Python project. pyEHR was last updated in 2018. So we started with direct httpx calls ([ADR-0004](../decisions/0004-direct-httpx-integration.md)).

As the project grew, the pain of manual FLAT path construction and raw JSON building became clear. Typos in path strings caused hours of debugging. No IDE autocomplete. No validation until EHRBase returned HTTP 422.

oehrpy was created to solve these problems -- first as an internal module, then extracted into a standalone, published SDK. The full story is told in [Part 5 of the blog series](https://medium.com/@platzh1rsch/building-open-cis-part-5-oehrpy-a-python-sdk-for-openehr-c9c90f46d075).

## Feature Overview

| Feature | Description |
|---------|-------------|
| **RM Classes** | 134 Pydantic v2 models covering the openEHR Reference Model |
| **FLAT Serialization** | Convert RM objects to/from EHRBase FLAT format |
| **Canonical JSON** | Full round-trip support for canonical JSON format |
| **EHRBase Client** | Async REST client for all EHRBase endpoints |
| **VitalSignsBuilder** | Type-safe builder for vital signs compositions |
| **OPT Parser** | Parse OPT 1.4 XML template files |
| **Template Generator** | Generate Python builders from OPT files |
| **AQL Builder** | Fluent API for building AQL queries |

## Quick Example

```python
from openehr_sdk.templates import VitalSignsBuilder
from openehr_sdk.client import EHRBaseClient

# Type-safe composition building with IDE autocomplete
builder = VitalSignsBuilder(composer_name="Dr. Smith")
builder.add_blood_pressure(systolic=120, diastolic=80)
builder.add_pulse(rate=72)
flat_data = builder.build()

# Async EHRBase client
async with EHRBaseClient(
    base_url="http://localhost:8080/ehrbase",
    username="admin",
    password="admin",
) as client:
    uid = await client.create_composition(
        ehr_id=ehr_id,
        template_id=VitalSignsBuilder.template_id,
        composition=flat_data,
        format="flat",
    )
```

## Links

- [GitHub Repository](https://github.com/platzhersh/oehrpy)
- [Integration with Open CIS](integration.md) -- how Open CIS uses oehrpy
- [Coverage & Roadmap](coverage.md) -- what's implemented and what's next
- [Blog Post: oehrpy -- A Python SDK for openEHR](https://medium.com/@platzh1rsch/building-open-cis-part-5-oehrpy-a-python-sdk-for-openehr-c9c90f46d075)
