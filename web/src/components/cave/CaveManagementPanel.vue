<script setup lang="ts">
import { ref, watch } from 'vue'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { X, Plus, ShieldCheck, Loader2 } from 'lucide-vue-next'
import { useCaveStore } from '@/stores/cave'
import type { CaveEntry, CaveStatus } from '@/types/cave'
import {
  CAVE_CATEGORY_LABELS,
  CAVE_CRITICALITY_LABELS,
  CAVE_STATUS_LABELS,
  REACTION_TYPE_LABELS,
  SEVERITY_LABELS,
  CERTAINTY_LABELS,
} from '@/types/cave'
import CaveEntryDialog from './CaveEntryDialog.vue'

const props = defineProps<{
  open: boolean
  patientId: string
  patientName?: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  updated: []
}>()

const store = useCaveStore()

const showEntryDialog = ref(false)
const editingEntry = ref<CaveEntry | null>(null)
const statusFilter = ref<string>('')
const categoryFilter = ref<string>('')

// Load entries when panel opens
watch(
  () => props.open,
  (isOpen: boolean) => {
    if (isOpen) {
      loadEntries()
    }
  }
)

async function loadEntries() {
  await store.fetchEntries(
    props.patientId,
    statusFilter.value || undefined,
    categoryFilter.value || undefined
  )
}

// Reload when filters change
watch([statusFilter, categoryFilter], () => {
  if (props.open) loadEntries()
})

function openAddDialog() {
  editingEntry.value = null
  showEntryDialog.value = true
}

function openEditDialog(entry: CaveEntry) {
  editingEntry.value = entry
  showEntryDialog.value = true
}

async function handleStatusChange(entry: CaveEntry, newStatus: CaveStatus) {
  try {
    const result = await store.updateEntry(entry.composition_uid, props.patientId, {
      status: newStatus,
    })
    if (!result) return
    await loadEntries()
    emit('updated')
  } catch (e) {
    console.error('Failed to update CAVE entry status:', e)
  }
}

async function handleDelete(entry: CaveEntry) {
  if (!window.confirm(`Delete CAVE entry for "${entry.substance}"?`)) return

  try {
    const success = await store.deleteEntry(entry.composition_uid, props.patientId)
    if (!success) return
    await loadEntries()
    emit('updated')
  } catch (e) {
    console.error('Failed to delete CAVE entry:', e)
  }
}

async function handleRecordNka() {
  if (store.entries.some((e: CaveEntry) => e.status === 'active')) {
    if (!window.confirm('There are active allergy entries. Recording NKA may be inconsistent. Continue?')) {
      return
    }
  }
  const success = await store.recordNka(props.patientId)
  if (success) {
    await loadEntries()
    emit('updated')
  }
}

async function handleEntrySaved() {
  await loadEntries()
  await store.fetchSummary(props.patientId)
  emit('updated')
}

function getCriticalityBadge(criticality: string) {
  switch (criticality) {
    case 'high':
      return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200'
    case 'low':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'active':
      return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200'
    case 'inactive':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    case 'resolved':
      return 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200'
    case 'refuted':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
  }
}

function handleOpenChange(open: boolean) {
  emit('update:open', open)
}
</script>

<template>
  <DialogRoot :open="open" @update:open="handleOpenChange">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
      <DialogContent class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg border shadow-lg w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
        <div class="flex items-center justify-between mb-4">
          <div>
            <DialogTitle class="text-lg font-semibold">
              CAVE - Allergies & Adverse Reactions
            </DialogTitle>
            <DialogDescription class="text-sm text-muted-foreground">
              {{ patientName || 'Patient' }}
            </DialogDescription>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-9 px-3 hover:bg-primary/90"
              @click="openAddDialog"
            >
              <Plus class="h-4 w-4 mr-1" />
              Add Entry
            </button>
            <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
              <X class="h-4 w-4" />
              <span class="sr-only">Close</span>
            </DialogClose>
          </div>
        </div>

        <!-- Filters -->
        <div class="flex gap-3 mb-4">
          <select
            v-model="statusFilter"
            class="flex h-9 rounded-md border border-input bg-background px-2 py-1 text-sm"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="resolved">Resolved</option>
            <option value="refuted">Refuted</option>
          </select>
          <select
            v-model="categoryFilter"
            class="flex h-9 rounded-md border border-input bg-background px-2 py-1 text-sm"
          >
            <option value="">All Categories</option>
            <option value="medication">Medication</option>
            <option value="food">Food</option>
            <option value="environment">Environment</option>
            <option value="other">Other</option>
          </select>
        </div>

        <!-- Loading -->
        <div v-if="store.loading && store.entries.length === 0" class="py-8 text-center text-muted-foreground">
          <Loader2 class="h-5 w-5 animate-spin mx-auto mb-2" />
          Loading CAVE entries...
        </div>

        <!-- Error -->
        <div v-else-if="store.error" class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
          {{ store.error }}
        </div>

        <!-- Entries list -->
        <div v-else-if="store.entries.length > 0" class="space-y-3">
          <div
            v-for="entry in store.entries"
            :key="entry.id"
            class="rounded-lg border p-4 space-y-2"
          >
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-semibold">{{ entry.substance }}</span>
                  <span
                    :class="['text-xs px-2 py-0.5 rounded-full', getCriticalityBadge(entry.criticality)]"
                  >
                    {{ CAVE_CRITICALITY_LABELS[entry.criticality] }}
                  </span>
                  <span
                    :class="['text-xs px-2 py-0.5 rounded-full', getStatusBadge(entry.status)]"
                  >
                    {{ CAVE_STATUS_LABELS[entry.status] }}
                  </span>
                </div>
                <div class="text-xs text-muted-foreground mt-1">
                  {{ CAVE_CATEGORY_LABELS[entry.category] }} &middot;
                  {{ REACTION_TYPE_LABELS[entry.reaction_type] }}
                </div>
              </div>
              <div class="flex items-center gap-1">
                <button
                  class="text-xs text-primary hover:underline px-2 py-1"
                  @click="openEditDialog(entry)"
                >
                  Edit
                </button>
                <template v-if="entry.status === 'active'">
                  <button
                    class="text-xs text-green-700 dark:text-green-400 hover:underline px-2 py-1"
                    @click="handleStatusChange(entry, 'resolved')"
                  >
                    Resolve
                  </button>
                </template>
                <template v-else-if="entry.status === 'resolved' || entry.status === 'inactive'">
                  <button
                    class="text-xs text-yellow-700 dark:text-yellow-400 hover:underline px-2 py-1"
                    @click="handleStatusChange(entry, 'active')"
                  >
                    Reactivate
                  </button>
                </template>
                <button
                  class="text-xs text-destructive hover:underline px-2 py-1"
                  @click="handleDelete(entry)"
                >
                  Delete
                </button>
              </div>
            </div>

            <!-- Reactions -->
            <div v-if="entry.reactions.length > 0" class="mt-2">
              <div class="text-xs font-medium text-muted-foreground mb-1">Reactions:</div>
              <div class="space-y-1">
                <div
                  v-for="(reaction, i) in entry.reactions"
                  :key="i"
                  class="text-xs text-muted-foreground flex items-center gap-1"
                >
                  <span>&bull;</span>
                  <span class="font-medium text-foreground">{{ reaction.manifestation }}</span>
                  <span>({{ SEVERITY_LABELS[reaction.severity] }}, {{ CERTAINTY_LABELS[reaction.certainty] }})</span>
                  <span v-if="reaction.description" class="italic">- {{ reaction.description }}</span>
                </div>
              </div>
            </div>

            <!-- Comment -->
            <div v-if="entry.comment" class="text-xs text-muted-foreground mt-1 italic">
              {{ entry.comment }}
            </div>

            <!-- Metadata -->
            <div class="text-xs text-muted-foreground mt-1">
              Recorded: {{ new Date(entry.recorded_date).toLocaleDateString() }}
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="py-8 text-center text-muted-foreground">
          <p class="mb-2">No CAVE entries recorded.</p>
          <p class="text-xs">Add an allergy/adverse reaction or record "No Known Allergies".</p>
        </div>

        <!-- Error (shown when entries exist but an action failed) -->
        <div v-if="store.error && store.entries.length > 0" class="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive mt-3">
          {{ store.error }}
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between mt-6 pt-4 border-t">
          <button
            class="inline-flex items-center gap-1.5 text-sm font-medium text-green-700 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
            @click="handleRecordNka"
          >
            <ShieldCheck class="h-4 w-4" />
            Record "No Known Allergies"
          </button>
          <button
            class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-9 px-4 hover:bg-accent hover:text-accent-foreground"
            @click="handleOpenChange(false)"
          >
            Close
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>

  <!-- Entry create/edit dialog -->
  <CaveEntryDialog
    v-model:open="showEntryDialog"
    :patient-id="patientId"
    :edit-entry="editingEntry"
    @saved="handleEntrySaved"
  />
</template>
