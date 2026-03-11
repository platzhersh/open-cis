# PRD: Brand Kit Integration into App Design

**Status:** Draft
**Date:** 2026-03-11
**Author:** Claude

## Problem Statement

The Open CIS brand kit defines a distinct visual identity — "The Archetype Brick" — with specific colors (Archetype Blue `#005EB8`, Foundation Orange `#F39200`), typography (Inter, JetBrains Mono), and a logo mark. However, the web application currently uses the generic shadcn-vue default theme (dark navy primary, no accent color, system fonts, no logo). The brand kit exists only in documentation (`docs/brand/brand-kit.html`) and is completely disconnected from the actual product UI.

## Goal

Apply the brand kit to the web application so that the product visually matches its defined identity. Users should immediately recognize the app as "Open CIS" through consistent use of brand colors, typography, and the logo mark.

## Current State

| Element | Brand Kit | App (Current) |
|---------|-----------|---------------|
| **Primary color** | Archetype Blue `#005EB8` (HSL 209 100% 36%) | Dark navy `hsl(222.2 47.4% 11.2%)` |
| **Accent color** | Foundation Orange `#F39200` (HSL 36 100% 48%) | None (same as secondary) |
| **Heading font** | Inter Bold (700) | System default sans-serif |
| **Body font** | Inter Regular (400) | System default sans-serif |
| **Code font** | JetBrains Mono (400) | System default monospace |
| **Logo in header** | Isometric brick + "open**cis**" wordmark | Plain text "Open CIS" |
| **Favicon** | Simplified brick SVG | Default Vite icon (`/vite.svg`) |
| **Dark mode** | White top brick, blue studs | Generic inverted palette |

## Changes Required

### 1. CSS Variables — Map Brand Colors to Design Tokens

Update `web/src/assets/index.css` to replace the generic shadcn defaults with brand-derived values.

**Light mode:**
- `--primary` → Archetype Blue (`209 100% 36%`)
- `--primary-foreground` → White (`0 0% 100%`)
- `--accent` → Foundation Orange at 10% opacity for backgrounds (`36 100% 96%`)
- `--accent-foreground` → Foundation Orange dark (`36 100% 30%`)
- `--ring` → Archetype Blue (`209 100% 36%`)
- Keep slate neutrals for `--background`, `--foreground`, `--muted`, `--border`, `--card` (brand-consistent)

**Dark mode:**
- `--primary` → Lighter Archetype Blue for contrast (`209 90% 55%`)
- `--primary-foreground` → White
- `--accent` → Foundation Orange muted (`36 80% 15%`)
- `--accent-foreground` → Foundation Orange light (`36 100% 70%`)
- `--ring` → Lighter Archetype Blue

### 2. Typography — Load Brand Fonts

Add Inter (weights: 300, 400, 600, 700, 900) and JetBrains Mono (400) via Google Fonts in `web/index.html`. Set `font-family: 'Inter', system-ui, sans-serif` as the base and `'JetBrains Mono'` for `font-mono` in Tailwind config.

### 3. Logo & Header Wordmark

- Add inline SVG logo mark (simplified brick, ~24px) to the header in `App.vue`
- Replace plain "Open CIS" text with branded wordmark: `<span class="font-light">open</span><span class="font-black text-primary">cis</span>`
- Logo adapts to dark mode (white top brick variant)

### 4. Favicon

- Copy the brand favicon SVG to `web/public/favicon.svg`
- Update `web/index.html` to reference it instead of `/vite.svg`

### 5. Tailwind Config — Font Family Extension

Extend `web/tailwind.config.js` to set Inter as the default `fontFamily.sans` and JetBrains Mono as `fontFamily.mono`.

## Out of Scope

- Animated logo (hero/loading) — future enhancement
- Custom component variants (e.g., orange accent buttons) — can be added incrementally
- Marketing/landing pages — only the app shell
- Logo as a separate reusable Vue component — inline SVG is sufficient for now

## Success Criteria

1. Primary action buttons and links render in Archetype Blue
2. Focus rings use Archetype Blue
3. All text renders in Inter; monospace text renders in JetBrains Mono
4. Header shows the isometric brick logo + branded wordmark
5. Browser tab shows the brick favicon
6. Dark mode preserves brand identity with appropriate color adjustments
7. No regressions in lint (`pnpm lint`), typecheck (`pnpm typecheck`), or tests (`pnpm test`)

## Files Modified

| File | Change |
|------|--------|
| `web/src/assets/index.css` | Brand color CSS variables |
| `web/tailwind.config.js` | Font family extension |
| `web/index.html` | Google Fonts link, favicon reference |
| `web/src/App.vue` | Logo SVG + branded wordmark in header |
| `web/public/favicon.svg` | New file — brand favicon |
