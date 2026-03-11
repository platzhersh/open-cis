# PRD-0007: GitHub Pages Documentation Site

**Version:** 1.0
**Date:** 2026-03-11
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Create a public documentation site for Open CIS hosted on GitHub Pages. The site will serve as the central hub for project documentation, architecture decisions, developer guides, and links to the accompanying Medium blog series. It transforms scattered markdown files and tribal knowledge into a polished, navigable reference that lowers the barrier to entry for contributors and demonstrates the project's maturity to the openEHR community.

---

## Problem Statement

### Current Pain Points

**1. Documentation is scattered across the repository**

Project knowledge lives in multiple places: `README.md`, `CONTEXT.md`, `CLAUDE.md`, `docs/adr/`, `docs/prd/`, and inline code comments. A newcomer must hunt through the repo tree to piece together how the system works.

**2. No public-facing documentation**

The only entry point for someone discovering Open CIS is the GitHub README. There is no searchable, navigable documentation site that explains the architecture, setup process, or clinical domain concepts in a structured way.

**3. Blog series context is disconnected**

The six-part Medium blog series documents the journey of building Open CIS, including deep dives into openEHR modeling, SDK decisions, and the creation of oehrpy. But there is no single place that ties these articles to the actual codebase and its current state.

**4. oehrpy lacks a discovery path**

[oehrpy](https://github.com/platzhersh/oehrpy) is a standalone Python SDK for openEHR that was born out of the Open CIS project. The relationship between the two projects, and how oehrpy fits into the architecture, is not well documented outside of PRD-0005 and the blog series.

**5. No brand presence**

The project has a brand kit ("The Archetype Brick" concept) with colors, logo lockups, and typography defined, but these assets are not used in any public-facing material.

---

## Goals & Success Metrics

### Goals

| Priority | Goal | Rationale |
|----------|------|-----------|
| P0 | Deploy a GitHub Pages site with project overview and getting started guide | Provide a single entry point for newcomers |
| P0 | Include architecture documentation with diagrams | Make the dual-database design and openEHR integration understandable |
| P0 | Link and contextualize the Medium blog series | Connect the narrative journey to the current codebase |
| P1 | Document oehrpy and its relationship to Open CIS | Help developers understand the SDK story |
| P1 | Incorporate the brand kit (colors, logo, typography) | Give the site a cohesive visual identity |
| P1 | Publish ADRs in a browsable format | Make architecture decisions discoverable |
| P2 | Add API reference documentation | Provide endpoint reference for developers |
| P2 | Include developer contribution guide | Lower barrier for new contributors |

### Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Site is live on GitHub Pages | Deployed | URL resolves |
| All existing ADRs are published | 5/5 ADRs | Page count |
| Blog series is linked with summaries | 6/6 articles | Page content |
| Time for new contributor to set up locally | < 15 min following docs | Manual test |

---

## Scope

### In Scope (v1.0)

1. **Static site generator setup** (MkDocs with Material theme or similar)
2. **GitHub Actions workflow** for automatic deployment on push to `main`
3. **Site structure and content** (see Information Architecture below)
4. **Brand kit integration** (colors, logo, favicon from "The Archetype Brick")
5. **Existing content migration** (README, CONTEXT.md, ADRs reformatted for the site)

### Out of Scope (Future)

- Auto-generated API reference from OpenAPI spec (could be added later via `mkdocstrings` or similar)
- Interactive examples or embedded demos
- Versioned documentation (single version for now)
- i18n / multi-language support
- Search analytics

---

## Technical Design

### Static Site Generator: MkDocs + Material

**Why MkDocs Material:**
- Markdown-native (all existing docs are markdown)
- Beautiful default theme with dark mode support
- Built-in search
- GitHub Pages deployment is a single CLI command
- Widely used in Python ecosystems (aligns with our backend)
- Supports admonitions, tabs, code highlighting, diagrams (Mermaid)

**Alternative considered:** Docusaurus (React-based) was considered but adds Node.js build complexity for what is primarily a Python project. VitePress was also considered but is Vue-focused and better suited for Vue library docs.

### Repository Structure

```
docs/
├── brand/
│   └── brand-kit.html          # Brand kit reference page
├── adr/                        # Architecture Decision Records (existing)
├── prd/                        # Product Requirements Documents (existing)
├── domain/                     # Domain concepts (existing, to be populated)
├── site/                       # NEW: documentation site source
│   ├── docs/
│   │   ├── index.md            # Home / project overview
│   │   ├── getting-started.md  # Setup guide (from README)
│   │   ├── architecture/
│   │   │   ├── overview.md     # System architecture (from CONTEXT.md)
│   │   │   ├── data-model.md   # Dual-database design
│   │   │   └── openehr.md      # openEHR concepts for newcomers
│   │   ├── guides/
│   │   │   ├── development.md  # Dev workflow, commands, testing
│   │   │   ├── deployment.md   # Railway deployment guide
│   │   │   └── contributing.md # How to contribute
│   │   ├── decisions/
│   │   │   ├── index.md        # ADR index
│   │   │   ├── 0001-use-openehr.md
│   │   │   ├── 0002-fastapi-backend.md
│   │   │   ├── 0003-template-management.md
│   │   │   ├── 0004-direct-httpx-integration.md
│   │   │   └── 0005-synthetic-data.md
│   │   ├── blog-series/
│   │   │   └── index.md        # Blog series index with summaries
│   │   ├── oehrpy/
│   │   │   ├── index.md        # What is oehrpy, relationship to Open CIS
│   │   │   ├── integration.md  # How Open CIS uses oehrpy (from PRD-0005)
│   │   │   └── coverage.md     # SDK coverage gaps & roadmap
│   │   └── brand/
│   │       └── index.md        # Brand guidelines (references brand-kit.html)
│   └── mkdocs.yml              # Site configuration
├── ...
```

### MkDocs Configuration

```yaml
# docs/site/mkdocs.yml
site_name: Open CIS
site_description: A minimal Clinical Information System built on openEHR/EHRBase
site_url: https://platzhersh.github.io/open-cis/
repo_url: https://github.com/platzhersh/open-cis
repo_name: platzhersh/open-cis

theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  font:
    text: Inter
    code: JetBrains Mono
  logo: assets/logo.svg
  favicon: assets/favicon.svg
  features:
    - navigation.sections
    - navigation.expand
    - navigation.top
    - content.code.copy
    - search.highlight

extra_css:
  - stylesheets/brand.css  # Custom brand colors (#005EB8, #F39200)

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Architecture:
    - Overview: architecture/overview.md
    - Data Model: architecture/data-model.md
    - openEHR Concepts: architecture/openehr.md
  - Guides:
    - Development: guides/development.md
    - Deployment: guides/deployment.md
    - Contributing: guides/contributing.md
  - Decisions:
    - decisions/index.md
    - ADR-0001 Use openEHR: decisions/0001-use-openehr.md
    - ADR-0002 FastAPI Backend: decisions/0002-fastapi-backend.md
    - ADR-0003 Template Management: decisions/0003-template-management.md
    - ADR-0004 Direct httpx Integration: decisions/0004-direct-httpx-integration.md
    - ADR-0005 Synthetic Data: decisions/0005-synthetic-data.md
  - Blog Series: blog-series/index.md
  - oehrpy:
    - Overview: oehrpy/index.md
    - Integration: oehrpy/integration.md
    - Coverage & Roadmap: oehrpy/coverage.md
  - Brand: brand/index.md

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - tables
  - attr_list
  - md_in_html
```

### GitHub Actions Workflow

```yaml
# .github/workflows/docs.yml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/site/**'
      - '.github/workflows/docs.yml'
  workflow_dispatch:  # Allow manual trigger

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install mkdocs-material pymdown-extensions

      - name: Build and deploy
        working-directory: docs/site
        run: mkdocs gh-deploy --force
```

### Brand Integration

The brand kit ("The Archetype Brick") defines:

| Element | Value | Usage |
|---------|-------|-------|
| **Archetype Blue** | `#005EB8` | Primary color, top brick, headings, links |
| **Foundation Orange** | `#F39200` | Accent color, bottom brick, highlights, CTAs |
| **Clinical Neutrals** | Slate scale | Body text, backgrounds, borders |
| **Primary Font** | Inter | All text (Light for "open", Black for "cis") |
| **Code Font** | JetBrains Mono | Code blocks, terminal output |
| **Logo** | Isometric stacked bricks | Favicon, site logo, social preview |

Custom CSS override for MkDocs Material:

```css
/* docs/site/docs/stylesheets/brand.css */
:root {
  --md-primary-fg-color: #005EB8;
  --md-primary-fg-color--light: #3380C8;
  --md-primary-fg-color--dark: #004A93;
  --md-accent-fg-color: #F39200;
  --md-accent-fg-color--transparent: rgba(243, 146, 0, 0.1);
}

[data-md-color-scheme="slate"] {
  --md-primary-fg-color: #005EB8;
  --md-accent-fg-color: #F39200;
}
```

---

## Information Architecture

### Home Page (`index.md`)

- Project tagline and logo
- One-paragraph description
- Key features / what makes Open CIS interesting
- Quick links to Getting Started, Architecture, Blog Series
- Live demo link (Railway staging)
- Deploy your own button (Railway template)

### Getting Started (`getting-started.md`)

Consolidates setup instructions from README.md and CLAUDE.md:
- Prerequisites (Docker, Python 3.11+, pnpm)
- One-command setup (`./scripts/setup.sh`)
- Manual setup steps
- Health check verification
- Service URLs table

### Architecture Section

**Overview** (`architecture/overview.md`):
- High-level system diagram (Mermaid)
- Tech stack table
- Service layer pattern explanation
- Request flow walkthrough

**Data Model** (`architecture/data-model.md`):
- Dual-database design (EHRBase + PostgreSQL)
- PatientRegistry linking MRN to EHR ID
- When data goes where (clinical vs. app data)
- Prisma schema overview

**openEHR Concepts** (`architecture/openehr.md`):
- EHR, Composition, Archetype, Template, AQL explained for newcomers
- How Open CIS uses these concepts
- FLAT format explanation
- Links to openEHR.org learning resources

### Blog Series (`blog-series/index.md`)

Each article gets a summary card with:
- Title and link to Medium article
- 2-3 sentence summary of what it covers
- Key concepts introduced
- Relevant code/docs in the repo

| # | Article | Key Topics |
|---|---------|------------|
| 1 | [Building Open CIS: A Minimal Clinical Information System on openEHR](https://medium.com/@platzh1rsch/building-open-cis-a-minimal-clinical-information-system-on-openehr-7d3c5d75bae8) | Project motivation, openEHR introduction, EHRBase setup |
| 2 | [Part 2: The Clinical Modeling Stack](https://medium.com/@platzh1rsch/building-open-cis-part-2-the-clinical-modeling-stack-221c019e65ca) | Archetypes, templates, CKM, clinical modeling workflow |
| 3 | [Part 2b: Template Formats and the Flat Format Deep Dive](https://medium.com/@platzh1rsch/building-open-cis-part-2b-template-formats-and-the-flat-format-deep-dive-0ed3ff0acfed) | OPT format, FLAT vs structured vs canonical JSON, path syntax |
| 4 | [Part 3: Going SDK-less — Our Architecture Decisions](https://medium.com/@platzh1rsch/building-open-cis-part-3-going-sdk-less-our-architecture-decisions-134786e090b5) | Why direct HTTP, ADR process, httpx integration |
| 5 | [Part 4: The openEHR SDK Landscape](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279) | Java SDK, pyEHR, SDK gap analysis, community state |
| 6 | [Part 5: oehrpy — A Python SDK for openEHR](https://medium.com/@platzh1rsch/building-open-cis-part-5-oehrpy-a-python-sdk-for-openehr-c9c90f46d075) | oehrpy design, RM models, VitalSignsBuilder, FLAT serialization |

### oehrpy Section

**Overview** (`oehrpy/index.md`):
- What is oehrpy: a Python SDK for openEHR, born from the Open CIS project
- Link to [oehrpy GitHub repository](https://github.com/platzhersh/oehrpy)
- Link to [PyPI package](https://pypi.org/project/oehrpy/) (if published)
- Feature matrix (134 RM classes, async EHRBase client, VitalSignsBuilder, OPT parser, AQL builder)
- The story: started as ADR-0004 (direct httpx), evolved into a standalone SDK (blog Part 5)

**Integration** (`oehrpy/integration.md`):
- How Open CIS uses oehrpy (from PRD-0005)
- Before/after code comparison
- Migration path from raw HTTP to SDK
- Architecture diagram showing oehrpy's place in the stack

**Coverage & Roadmap** (`oehrpy/coverage.md`):
- Current SDK coverage (from `oehrpy-coverage-gaps.md`)
- High-value gaps: composition update, versioning, contributions
- Priority matrix
- How to contribute to oehrpy

### Decisions Section (`decisions/`)

All five ADRs published as-is with a navigable index page showing:
- ADR number, title, date, status
- One-line summary for each

### Brand Section (`brand/index.md`)

- Brand guidelines summary
- Color palette with hex codes
- Logo usage (light/dark modes)
- Typography (Inter + JetBrains Mono)
- Link to full interactive brand kit HTML

---

## Content Migration Plan

### Phase 1: Site Scaffolding (Day 1)

1. Install MkDocs Material locally
2. Create `docs/site/` directory structure
3. Configure `mkdocs.yml` with nav and theme
4. Set up GitHub Actions workflow
5. Create placeholder pages
6. Verify local `mkdocs serve` works

### Phase 2: Core Content (Day 2-3)

1. **Home page**: Write project overview from README + CONTEXT.md
2. **Getting Started**: Consolidate from README + CLAUDE.md
3. **Architecture pages**: Expand CONTEXT.md into three focused pages
4. **ADR migration**: Copy and format all 5 ADRs
5. **Blog series index**: Write summaries for all 6 articles

### Phase 3: oehrpy & Brand (Day 4)

1. **oehrpy overview**: Write from PRD-0005 + blog Part 5
2. **oehrpy integration**: Adapt PRD-0005 content
3. **oehrpy coverage**: Adapt coverage-gaps.md
4. **Brand page**: Create guidelines page, link to brand-kit.html
5. **Custom CSS**: Apply brand colors to MkDocs theme
6. **Logo/favicon**: Extract SVG from brand kit for site assets

### Phase 4: Polish & Deploy (Day 5)

1. Cross-link between pages
2. Add Mermaid diagrams for architecture
3. Test dark mode
4. Test mobile responsiveness
5. Deploy to GitHub Pages
6. Update README.md with docs site link

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Content becomes stale vs. codebase | High | Medium | Keep docs close to source (same repo), review in PRs |
| Over-engineering the site | Medium | Low | Start with MkDocs defaults, customize incrementally |
| Duplicate content (README vs. docs site) | Medium | Low | README becomes a brief intro pointing to docs site |
| GitHub Pages build failures | Low | Low | GitHub Actions with pinned versions, local testing |

---

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| mkdocs-material | >=9.0 | Static site generator + theme |
| pymdown-extensions | >=10.0 | Markdown extensions (admonitions, tabs, code blocks) |
| GitHub Pages | N/A | Hosting (free for public repos) |
| GitHub Actions | N/A | CI/CD for automatic deployment |

---

## Success Criteria

The documentation site is successful when:

- Site is live at `https://platzhersh.github.io/open-cis/`
- All 5 ADRs are browsable on the site
- All 6 blog articles are linked with summaries
- oehrpy section explains the SDK and its relationship to Open CIS
- Brand colors and logo are applied consistently
- A new developer can go from zero to running locally using only the docs site
- Site auto-deploys on push to main

---

## Related Documents

- [README.md](../../README.md) - Current project entry point
- [CONTEXT.md](../../CONTEXT.md) - Architecture and AI context
- [CLAUDE.md](../../CLAUDE.md) - Development commands and conventions
- [PRD-0005: oehrpy SDK Integration](./0005-oehrpy-sdk-integration.md) - oehrpy integration plan
- [oehrpy Coverage Gaps](./oehrpy-coverage-gaps.md) - SDK gap analysis
- [ADR Index](../adr/) - Architecture Decision Records
- [oehrpy Repository](https://github.com/platzhersh/oehrpy) - Python openEHR SDK
- [Brand Kit](../brand/brand-kit.html) - Interactive brand reference

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-11 | Open CIS Team | Initial PRD draft |
