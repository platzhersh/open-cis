# 1. Use openEHR for Clinical Data

Date: 2026-01-02

## Status

Accepted

## Context

We need a data model and storage solution for clinical data including observations, diagnoses, medications, and encounters. Three approaches were considered: designing a custom relational schema with our own tables for each clinical concept, adopting HL7 FHIR resources with a FHIR server, or using openEHR archetypes with EHRBase as the clinical data repository.

A custom relational schema would give us complete control over the data model and allow rapid initial development, but we would need to design and maintain schemas for every clinical concept ourselves. HL7 FHIR offers a mature, widely-adopted standard with extensive tooling and community support, but FHIR servers can be complex to deploy and the resource-based model may not align perfectly with our learning goals. openEHR provides archetype-based modeling where clinical concepts are defined in reusable, version-controlled archetypes maintained by the international openEHR community, separating the clinical data model from the software implementation.

## Decision

We will use openEHR with EHRBase as the clinical data repository.

EHRBase is an open-source, actively maintained openEHR server that provides a well-documented REST API. Clinical data will be stored as compositions following openEHR templates, while application-specific data like user accounts and audit logs will remain in a separate PostgreSQL database. We will link patient medical record numbers to openEHR EHR IDs through a PatientRegistry table in our application database.

## Consequences

This decision means we gain access to rich clinical modeling capabilities with community-maintained archetypes, producing standardized data that could potentially interoperate with other openEHR systems. The Archetype Query Language (AQL) will enable us to perform complex queries across clinical structures in ways that would be difficult with traditional SQL.

However, we accept a steeper learning curve as the team must understand openEHR concepts including compositions, archetypes, and templates. We will need to manage two separate databases: EHRBase for clinical data and PostgreSQL for application data. Template creation and management adds operational complexity compared to a simple relational schema.

To mitigate these challenges, we will start with simple templates focusing on basic vital signs before expanding to more complex clinical scenarios. Keeping application-specific concerns in the PostgreSQL database allows us to use familiar tools and patterns where openEHR semantics are unnecessary.
