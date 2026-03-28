# 6. Versioning and Release Management

Date: 2026-03-28

## Status

Proposed

## Context

Open CIS has no formal versioning or release management. Both `package.json` (web) and `pyproject.toml` (API) are pinned at `0.1.0` with no process to bump them. This makes it difficult to:

1. **Trace deployments** — which commits are running in staging vs. production?
2. **Communicate changes** — contributors and users have no changelog to review.
3. **Coordinate releases** — the API and frontend are versioned independently today but deployed together.

### Requirements

- A single source of truth for the current version.
- The version displayed in the frontend UI so users/testers can report issues against a specific release.
- An auto-generated changelog derived from commit history (no manual editing).
- Lightweight process — this is a learning/experimentation project, not enterprise software.

## Decision

### 1. Semantic Versioning (SemVer)

We adopt [Semantic Versioning 2.0.0](https://semver.org/) with a **single version** for the entire monorepo (API + web). Both `package.json` and `pyproject.toml` are bumped together.

- **MAJOR** — breaking API changes or incompatible data migrations
- **MINOR** — new features (new endpoints, UI pages, openEHR templates)
- **PATCH** — bug fixes, dependency updates, docs

We start at the current `0.x` series. While in `0.x`, minor bumps may include breaking changes per SemVer convention.

### 2. Conventional Commits

All commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `docs`, `ci`, `refactor`, `test`, `chore`, `perf`, `style`
**Scopes (optional):** `api`, `web`, `ehrbase`, `db`, `infra`

Examples:
```
feat(web): add patient timeline view
fix(api): correct AQL query for vital signs
docs: update EHRBase integration guide
```

Commits with `feat` trigger a minor bump; `fix` triggers a patch bump. A `BREAKING CHANGE:` footer (or `!` after the type) triggers a major bump.

### 3. Changelog Generation

Use [git-cliff](https://git-cliff.org/) to auto-generate `CHANGELOG.md` from conventional commit messages.

**Why git-cliff over alternatives:**
- **vs. conventional-changelog (JS)**: git-cliff is a standalone Rust binary — no Node.js dependency needed for the API side, works in CI without a JS runtime.
- **vs. release-please (Google)**: release-please is a full GitHub App/Action that creates release PRs automatically. It's powerful but heavyweight for our project. git-cliff is simpler: it just generates a changelog file, and we control when/how releases happen.
- **vs. manual changelog**: error-prone, always out of date.

git-cliff is configured via a `cliff.toml` at the repo root. It groups commits by type, links to GitHub PRs/issues, and outputs Markdown.

### 4. Release Workflow

Releases are triggered manually via a **GitHub Actions workflow dispatch** (`workflow_dispatch`):

1. Maintainer runs the "Release" workflow, specifying the bump level (`major`, `minor`, `patch`) or letting conventional commits determine it automatically.
2. The workflow:
   - Bumps version in `package.json` and `pyproject.toml`
   - Runs `git-cliff` to regenerate `CHANGELOG.md`
   - Commits the version bump + changelog
   - Creates a git tag `v{version}`
   - Pushes the tag
   - Creates a GitHub Release with the changelog excerpt as release notes
3. Railway deploys from the tag or main branch as configured.

### 5. Version Display in Frontend

The frontend displays the current version in the page footer/header. The version is injected at **build time** via Vite's `define` config, reading from `package.json`:

```ts
// vite.config.ts
define: {
  __APP_VERSION__: JSON.stringify(require('./package.json').version),
}
```

This is a zero-runtime-cost approach — the version string is baked into the bundle at build time. No API call needed.

### 6. API Version Endpoint

The API exposes a `GET /api/version` endpoint returning the current version. This is useful for health checks and debugging deployments:

```json
{ "version": "0.2.0" }
```

## Consequences

### Positive

- **Traceability**: every deployment is tied to a specific version and tag.
- **Automated changelog**: contributors never need to manually write release notes.
- **Low overhead**: no new services, no GitHub Apps — just a CLI tool and a CI workflow.
- **User-visible version**: testers can report "I see this bug on v0.3.1" instead of "I see this bug on the latest version".

### Negative

- **Commit discipline required**: contributors must write conventional commit messages. Malformed messages will be excluded from the changelog.
- **Single version for monorepo**: API and web are always released together even if only one changed. Acceptable for our project size.

### Risks

- If we forget to run the release workflow, the changelog drifts. Mitigated by keeping it simple and documenting the process.
- Conventional commit enforcement is best done via a commit-msg git hook (e.g., commitlint). We can add this later if discipline slips.

## Implementation Plan

1. **Add `cliff.toml`** configuration at repo root
2. **Add GitHub Actions release workflow** (`.github/workflows/release.yml`)
3. **Update `vite.config.ts`** to inject `__APP_VERSION__` at build time
4. **Add version display** in the frontend header (App.vue)
5. **Add `GET /api/version` endpoint** to the API
6. **Retroactively tag** the current state as `v0.1.0`
7. **Update CLAUDE.md** with release process documentation
