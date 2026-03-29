# 7. Responsive Tables and Loading Indicators

Date: 2026-03-29

## Status

Accepted

## Context

Open CIS is used on both desktop and mobile devices. Two recurring UI patterns needed standardization:

1. **Data tables** (patients, encounters, vitals) render as full `<table>` elements that overflow horizontally on small screens, creating a poor mobile experience with horizontal scrolling and cramped columns.
2. **Loading indicators** were inconsistent across the app — some views showed plain text ("Loading..."), others used a spinner icon with text, and styling varied between components.

Both issues compound on mobile where screen real estate is limited and loading states are more noticeable on slower connections.

## Decision

### Responsive Tables: Card/Table Dual Layout

For list pages with wide tables (5+ columns), we use a **dual layout pattern**:

- **Mobile** (`md:hidden`): A **card-based layout** where each record is a tappable card showing the most important fields in a compact arrangement.
- **Desktop** (`hidden md:block`): The full **HTML table** with all columns, wrapped in `overflow-x-auto` as a safety net.

```vue
<template v-if="hasData">
  <!-- Mobile: Card layout -->
  <div class="space-y-3 md:hidden">
    <div
      v-for="item in items"
      :key="item.id"
      class="rounded-lg border p-4 hover:bg-muted/50 transition-colors"
    >
      <!-- Compact card content: primary info + badges -->
    </div>
  </div>

  <!-- Desktop: Table layout -->
  <div class="hidden md:block rounded-lg border">
    <div class="overflow-x-auto">
      <table class="w-full">
        <!-- Full table with all columns -->
      </table>
    </div>
  </div>
</template>
```

**When to use this pattern:**
- List pages with 5+ table columns (e.g., encounters with patient, type, status, time, provider, location)
- Tables where secondary columns (provider, location, actions) add little value on mobile

**When NOT to use this pattern:**
- Simple tables with 3-4 narrow columns (e.g., vitals: date, BP, pulse, actions) — `overflow-x-auto` alone is sufficient
- Tables inside dialogs or panels where width is already constrained
- Data-dense views where all columns are equally important (prefer horizontal scroll)

### Loading Indicators: Spinner + Text

All loading states use a consistent **Loader2 spinner icon + descriptive text** pattern:

```vue
<div class="py-8 text-center text-muted-foreground">
  <Loader2 class="h-5 w-5 animate-spin mx-auto mb-2" />
  <p class="text-sm">Loading patients...</p>
</div>
```

For smaller/inline loading states (e.g., inside cards or panels), use a smaller spinner:

```vue
<div class="py-4 text-center text-muted-foreground">
  <Loader2 class="h-4 w-4 animate-spin mx-auto mb-1" />
  <p class="text-sm">Loading...</p>
</div>
```

**Rules:**
- Always use `Loader2` from `lucide-vue-next` with `animate-spin` — never plain text alone
- Center the spinner above the text
- Use `text-muted-foreground` for both spinner and text color
- Include a descriptive message (e.g., "Loading encounters..." not just "Loading...")
- Use `h-5 w-5` for full-page/section loading, `h-4 w-4` for inline/compact loading

### Dark Mode for Badges

All colored badges (status, type, category) must include `dark:` Tailwind variants:

```typescript
// Correct
'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200'

// Incorrect — missing dark mode
'bg-blue-100 text-blue-800'
```

## Consequences

### Positive

- Consistent UX across all loading states
- Mobile users see a usable card layout instead of a cramped, overflowing table
- Dark mode works correctly for all badge colors
- Clear pattern for contributors to follow when adding new list pages

### Negative

- Dual layout means maintaining two representations of the same data per list page
- Slightly more template code per page (~30 extra lines)

### Neutral

- The `md` breakpoint (768px) is the threshold — this can be adjusted if needed
- Card layouts show fewer fields than tables; this is an intentional trade-off for readability

## Related

- ADR-0000: Record Architecture Decisions
- Tailwind CSS dark mode: `dark:` variant classes
- shadcn-vue component conventions: semantic color tokens
