# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [0.3.4] - 2026-03-29

### Bug Fixes

- **api**: Improve NKA declaration detection with dedicated AQL query (#80) ([#80](https://github.com/platzhersh/open-cis/pull/80)) by @platzhersh
## [0.3.3] - 2026-03-29

### Bug Fixes

- **api**: Resolve exclusion path dynamically from web template tree (#79) ([#79](https://github.com/platzhersh/open-cis/pull/79)) by @platzhersh
## [0.3.2] - 2026-03-29

### Bug Fixes

- **api**: Add language and encoding metadata to NKA flat composition (#78) ([#78](https://github.com/platzhersh/open-cis/pull/78)) by @platzhersh
## [0.3.1] - 2026-03-29

### Bug Fixes

- **api**: Dynamic FLAT path resolution from EHRBase web templates (#77) ([#77](https://github.com/platzhersh/open-cis/pull/77)) by @platzhersh

### Documentation

- Add PRD-0009 System Info View and update PRD index (#76) ([#76](https://github.com/platzhersh/open-cis/pull/76)) by @platzhersh
## [0.3.0] - 2026-03-29

### Features

- **web**: Improve loading indicators and mobile responsiveness (#74) ([#74](https://github.com/platzhersh/open-cis/pull/74)) by @platzhersh

### Miscellaneous

- **web**: Hide 'Open Source' text on mobile, show only GitHub icon (#73) ([#73](https://github.com/platzhersh/open-cis/pull/73)) by @platzhersh
## [0.2.2] - 2026-03-28

### Bug Fixes

- **ci**: Add dependabot.yml to restrict updates to direct dependencies (#62) ([#62](https://github.com/platzhersh/open-cis/pull/62)) by @platzhersh
## [0.2.1] - 2026-03-28

### Bug Fixes

- **api**: EHRBase v2 compatibility issues with adverse reactions and compositions (#61) ([#61](https://github.com/platzhersh/open-cis/pull/61)) by @platzhersh
## [0.2.0] - 2026-03-28

### Bug Fixes

- Update healthcheck path to /ehrbase/rest/status by @platzhersh
- Switch from pnpm to npm for global serve installation in Dockerfile. by @platzhersh
- Change Dockerfiles to not run as root (#21) ([#21](https://github.com/platzhersh/open-cis/pull/21)) by @platzhersh
- Update EHRBase URL configuration to remove /rest path (#29) ([#29](https://github.com/platzhersh/open-cis/pull/29)) by @platzhersh
- Refactor seed script to use PatientRegistry model only (#30) ([#30](https://github.com/platzhersh/open-cis/pull/30)) by @platzhersh
- Add localStorage and sessionStorage to ESLint globals (#36) ([#36](https://github.com/platzhersh/open-cis/pull/36)) by @platzhersh
- Add Open CIS Adverse Reaction List template (#42) ([#42](https://github.com/platzhersh/open-cis/pull/42)) by @platzhersh
- Adverse reaction openEHR mappings and archetype paths (#46) ([#46](https://github.com/platzhersh/open-cis/pull/46)) by @platzhersh
- Update adverse reaction field name from substance to causative_agent (#49) ([#49](https://github.com/platzhersh/open-cis/pull/49)) by @platzhersh
- Reformat Open CIS Adverse Reaction List template XML (#51) ([#51](https://github.com/platzhersh/open-cis/pull/51)) by @platzhersh
- Update composition category from persistent to event (#55) ([#55](https://github.com/platzhersh/open-cis/pull/55)) by @platzhersh
- **api**: Exclusion_global field path in NKA composition builder (#58) ([#58](https://github.com/platzhersh/open-cis/pull/58)) by @platzhersh
- **api**: Add web template endpoint and fix FLAT path indexing (#60) ([#60](https://github.com/platzhersh/open-cis/pull/60)) by @platzhersh

### CI/CD

- Add scripts directory to Railway watch patterns (#31) ([#31](https://github.com/platzhersh/open-cis/pull/31)) by @platzhersh
- Add watch patterns to ehrbase-db Railway build config (#32) ([#32](https://github.com/platzhersh/open-cis/pull/32)) by @platzhersh
- Update docs workflow to use GitHub Actions Pages deployment (#43) ([#43](https://github.com/platzhersh/open-cis/pull/43)) by @platzhersh
- Add OPT template validation script and tests (#50) ([#50](https://github.com/platzhersh/open-cis/pull/50)) by @platzhersh
- Add semantic versioning and automated release management (#59) ([#59](https://github.com/platzhersh/open-cis/pull/59)) by @platzhersh

### Documentation

- Update Python setup instructions for Python 3.11+, correct EHRBase PostgreSQL port, and add a health check section. by @platzhersh
- Add PRDs for an admin interface and patient CRUD operations, and update the PRD index. by @platzhersh
- Add ADR-0003 detailing the decision to use direct httpx integration for the openEHR API. by @platzhersh
- Add Railway referral link to README (#25) ([#25](https://github.com/platzhersh/open-cis/pull/25)) by @platzhersh
- Add openEHR API coverage gaps analysis document (#38) ([#38](https://github.com/platzhersh/open-cis/pull/38)) by @platzhersh
- Add GitHub Pages documentation site with MkDocs (#41) ([#41](https://github.com/platzhersh/open-cis/pull/41)) by @platzhersh
- Include brand kit in documentation site build (#44) ([#44](https://github.com/platzhersh/open-cis/pull/44)) by @platzhersh
- Add PRD-0008 for improved error handling across the stack (#52) ([#52](https://github.com/platzhersh/open-cis/pull/52)) by @platzhersh

### Features

- Initialize core database schema, update database port, and add development guidance for Claude. by @platzhersh
- Initialize database schema with User, AuditLog, and PatientRegistry tables, roles enum, and a migration lock. by @platzhersh
- Add Redoc and OpenAPI schema links to README and enhance patient Pydantic schemas with field descriptions. by @platzhersh
- Standardize patient birth date to ISO 8601 string format with validation and updated service layer conversions. by @platzhersh
- Configure uvicorn to use the $PORT environment variable with a default of 8000. by @platzhersh
- Add Dockerfile for web service and update Railway configuration to use it, replacing Nixpacks builder. by @platzhersh
- Configure and document staging environment for web and API. by @platzhersh
- Implement patient & encounter CRUD operations (#18) ([#18](https://github.com/platzhersh/open-cis/pull/18)) by @platzhersh
- Add GitHub link to header and adjust layout. by @platzhersh
- Add basic chart for vital signs observations (#19) ([#19](https://github.com/platzhersh/open-cis/pull/19)) by @platzhersh
- Establish architecture decision record process and enhance existing openEHR and FastAPI ADRs. by @platzhersh
- Add synthetic data for staging deployment (#24) ([#24](https://github.com/platzhersh/open-cis/pull/24)) by @platzhersh
- Integrate oehrpy SDK for type-safe EHRBase composition building (#27) ([#27](https://github.com/platzhersh/open-cis/pull/27)) by @platzhersh
- Add dark mode toggle to application header (#34) ([#34](https://github.com/platzhersh/open-cis/pull/34)) by @platzhersh
- Implement CAVE form for allergies and adverse reactions (#40) ([#40](https://github.com/platzhersh/open-cis/pull/40)) by @platzhersh
- Apply Open CIS brand kit to web application UI (#45) ([#45](https://github.com/platzhersh/open-cis/pull/45)) by @platzhersh
- Add global exception handler for unhandled errors (#54) ([#54](https://github.com/platzhersh/open-cis/pull/54)) by @platzhersh

### Miscellaneous

- Fix docker setup (#17) ([#17](https://github.com/platzhersh/open-cis/pull/17)) by @platzhersh
- Add bind-tools to Dockerfile and enhance wait-for-db script with DNS resolution checks and logging. by @platzhersh
- Remove custom database wait script and tools as base image now handles database readiness. by @platzhersh
- Migrate build and package management from npm to pnpm. by @platzhersh
- Simplify railway.toml watch patterns to cover the entire web directory. by @platzhersh
- Add templates directory to Dockerfile build context. by @platzhersh
- Upgrade lodash from 4.17.21 to 4.17.23 (#28) ([#28](https://github.com/platzhersh/open-cis/pull/28)) by @platzhersh

### Refactoring

- Update Dockerfile CMD to shell form for environment variable substitution and remove railway.toml startCommand. by @platzhersh
- Enhance EHRBase composition creation error handling by logging detailed HTTP errors and failed composition data. by @platzhersh

### Styling

- Reformat MRN description strings for better readability in patient schemas. by @platzhersh

### Build

- Switch wait script from ENTRYPOINT to CMD to preserve base image entrypoint. by @platzhersh
- Adjust Dockerfile copy paths to be relative to the repository root by @platzhersh

