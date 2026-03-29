<script setup lang="ts">
import type { TemplateInfo } from '@/types'

defineProps<{
  templates: TemplateInfo[] | null
}>()
</script>

<template>
  <div class="rounded-lg border">
    <div class="p-4 border-b">
      <h2 class="text-lg font-semibold">Registered openEHR Templates</h2>
    </div>

    <div v-if="templates === null" class="p-6 text-center">
      <p class="text-sm text-muted-foreground">
        Could not fetch templates. EHRBase may be unavailable.
      </p>
    </div>

    <div v-else-if="templates.length === 0" class="p-6 text-center">
      <p class="text-sm text-muted-foreground">
        No templates registered. Upload templates to EHRBase to see them here.
      </p>
    </div>

    <template v-else>
      <!-- Mobile: card layout -->
      <div class="space-y-3 p-4 md:hidden">
        <div
          v-for="t in templates"
          :key="t.template_id"
          class="rounded-md border p-3 space-y-1"
        >
          <p class="text-sm font-medium">{{ t.concept }}</p>
          <p class="text-xs text-muted-foreground font-mono">{{ t.template_id }}</p>
          <p class="text-xs text-muted-foreground font-mono">{{ t.archetype_id }}</p>
        </div>
      </div>

      <!-- Desktop: table -->
      <div class="hidden md:block overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="h-12 px-4 text-left align-middle font-medium text-sm">Template ID</th>
              <th class="h-12 px-4 text-left align-middle font-medium text-sm">Concept</th>
              <th class="h-12 px-4 text-left align-middle font-medium text-sm">Archetype ID</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in templates"
              :key="t.template_id"
              class="border-b"
            >
              <td class="p-4 align-middle font-mono text-sm">{{ t.template_id }}</td>
              <td class="p-4 align-middle text-sm">{{ t.concept }}</td>
              <td class="p-4 align-middle font-mono text-sm text-muted-foreground">{{ t.archetype_id }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
