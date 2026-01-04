<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { TabsRoot, TabsList, TabsTrigger, TabsContent } from 'radix-vue'
import { useVitalsStore } from '@/stores/vitals'
import type { VitalSignsReading, RawComposition, ArchetypeInfo } from '@/types'
import { Copy, ExternalLink, Check, X } from 'lucide-vue-next'

const props = defineProps<{
  open: boolean
  reading: VitalSignsReading | null
  patientId: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const store = useVitalsStore()

const rawComposition = ref<RawComposition | null>(null)
const archetypeInfos = ref<Map<string, ArchetypeInfo>>(new Map())
const loading = ref(false)
const activeFormat = ref('FLAT')
const copiedPath = ref<string | null>(null)
const error = ref<string | null>(null)

// Request tracking to prevent race conditions on rapid format switching
let requestId = 0

// Load data when panel opens
async function loadData() {
  if (!props.reading || !props.reading.id) return

  loading.value = true
  error.value = null
  const currentRequestId = ++requestId

  try {
    const composition = await store.fetchRawComposition(props.reading.id, props.patientId, activeFormat.value as 'FLAT' | 'STRUCTURED')

    // Only update if this is still the latest request
    if (currentRequestId === requestId) {
      rawComposition.value = composition
    }

    const archetypesToFetch = props.reading.openehr_metadata.archetype_ids.filter(
      archetypeId => !archetypeInfos.value.has(archetypeId)
    )

    if (archetypesToFetch.length > 0) {
      const archetypeResults = await Promise.all(
        archetypesToFetch.map(archetypeId => store.fetchArchetypeInfo(archetypeId))
      )

      // Only update if this is still the latest request
      if (currentRequestId === requestId) {
        archetypesToFetch.forEach((archetypeId, index) => {
          const info = archetypeResults[index]
          if (info) {
            archetypeInfos.value.set(archetypeId, info)
          }
        })
      }
    }
  } catch (e) {
    console.error('Failed to load openEHR data:', e)
    // Only set error if this is still the latest request
    if (currentRequestId === requestId) {
      error.value = e instanceof Error ? e.message : 'Failed to load openEHR data'
    }
  } finally {
    // Only clear loading if this is still the latest request
    if (currentRequestId === requestId) {
      loading.value = false
    }
  }
}

watch(
  () => [props.open, props.reading] as const,
  ([isOpen]) => {
    if (isOpen) {
      loadData()
    }
  },
  { immediate: true }
)

// Load composition when format changes
watch(activeFormat, () => {
  loadData()
})

async function copyToClipboard(text: string, identifier: string) {
  try {
    await navigator.clipboard.writeText(text)
    copiedPath.value = identifier
    window.setTimeout(() => {
      copiedPath.value = null
    }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
  }
}

const formattedComposition = computed(() => {
  if (!rawComposition.value?.composition) return ''
  return JSON.stringify(rawComposition.value.composition, null, 2)
})

function handleOpenChange(open: boolean) {
  emit('update:open', open)
}
</script>

<template>
  <DialogRoot :open="open" @update:open="handleOpenChange">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
      <DialogContent class="fixed right-0 top-0 h-full w-full sm:max-w-lg bg-background border-l shadow-lg overflow-y-auto data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <DialogTitle class="text-lg font-semibold">openEHR Data Structure</DialogTitle>
            <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
              <X class="h-4 w-4" />
              <span class="sr-only">Close</span>
            </DialogClose>
          </div>

          <DialogDescription class="text-sm text-muted-foreground mb-6">
            View how this vital signs data is stored in openEHR format.
          </DialogDescription>

          <!-- Error Banner -->
          <div v-if="error" class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 mb-6">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1">
                <p class="text-sm font-medium text-destructive">Failed to load openEHR data</p>
                <p class="text-sm text-destructive/80 mt-1">{{ error }}</p>
              </div>
              <button
                class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-destructive text-destructive-foreground h-9 px-3 hover:bg-destructive/90"
                @click="loadData"
              >
                Retry
              </button>
            </div>
          </div>

          <div v-if="reading" class="space-y-6">
            <!-- Composition Info -->
            <div class="space-y-2">
              <h3 class="font-medium">Composition</h3>
              <div class="rounded-lg border bg-muted/30 p-3 space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-muted-foreground">UID:</span>
                  <code class="text-xs break-all max-w-[200px] text-right">{{ reading.openehr_metadata.composition_uid }}</code>
                </div>
                <div class="flex justify-between">
                  <span class="text-muted-foreground">Template:</span>
                  <code class="text-xs">{{ reading.openehr_metadata.template_id }}</code>
                </div>
                <div class="flex justify-between">
                  <span class="text-muted-foreground">EHR ID:</span>
                  <code class="text-xs break-all max-w-[200px] text-right">{{ reading.openehr_metadata.ehr_id }}</code>
                </div>
              </div>
            </div>

            <!-- Archetypes Used -->
            <div class="space-y-2">
              <h3 class="font-medium">Archetypes Used</h3>
              <div class="space-y-2">
                <div
                  v-for="archetypeId in reading.openehr_metadata.archetype_ids"
                  :key="archetypeId"
                  class="rounded-lg border p-3"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0">
                      <code class="text-xs text-primary break-all">{{ archetypeId }}</code>
                      <p v-if="archetypeInfos.get(archetypeId)" class="text-sm text-muted-foreground mt-1">
                        {{ archetypeInfos.get(archetypeId)?.description }}
                      </p>
                    </div>
                    <a
                      v-if="archetypeInfos.get(archetypeId)?.ckm_url"
                      :href="archetypeInfos.get(archetypeId)?.ckm_url ?? undefined"
                      target="_blank"
                      class="inline-flex items-center justify-center rounded-md text-sm h-8 px-2 hover:bg-accent hover:text-accent-foreground shrink-0"
                    >
                      <ExternalLink class="h-4 w-4" />
                      <span class="ml-1 hidden sm:inline">CKM</span>
                    </a>
                  </div>
                </div>
              </div>
            </div>

            <!-- Data Path Mappings -->
            <div class="space-y-2">
              <h3 class="font-medium">Data Path Mappings</h3>
              <p class="text-sm text-muted-foreground">
                See how each UI field maps to openEHR archetype paths.
              </p>
              <div class="space-y-3">
                <div
                  v-for="mapping in reading.openehr_metadata.path_mappings"
                  :key="mapping.field"
                  class="rounded-lg border p-3 space-y-2"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-medium capitalize">{{ mapping.field.replace('_', ' ') }}</span>
                    <span class="text-sm">
                      {{ mapping.value }}
                      <span v-if="mapping.unit" class="text-muted-foreground">{{ mapping.unit }}</span>
                    </span>
                  </div>

                  <div class="space-y-1 text-xs">
                    <div class="flex items-start gap-2">
                      <span class="text-muted-foreground shrink-0">Archetype:</span>
                      <code class="break-all">{{ mapping.archetype_path }}</code>
                    </div>
                    <div class="flex items-start gap-2">
                      <span class="text-muted-foreground shrink-0">FLAT:</span>
                      <div class="flex items-center gap-1 min-w-0">
                        <code class="break-all">{{ mapping.flat_path }}</code>
                        <button
                          class="inline-flex items-center justify-center rounded-md h-5 w-5 shrink-0 hover:bg-accent"
                          @click="copyToClipboard(mapping.flat_path, mapping.flat_path)"
                        >
                          <Check v-if="copiedPath === mapping.flat_path" class="h-3 w-3 text-green-600" />
                          <Copy v-else class="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Raw Composition Data -->
            <div class="space-y-2">
              <h3 class="font-medium">Raw Composition Data</h3>
              <TabsRoot v-model="activeFormat" class="w-full">
                <TabsList class="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 w-full">
                  <TabsTrigger
                    value="FLAT"
                    class="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm flex-1"
                  >
                    FLAT
                  </TabsTrigger>
                  <TabsTrigger
                    value="STRUCTURED"
                    class="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm flex-1"
                  >
                    STRUCTURED
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="FLAT" class="mt-2">
                  <div class="relative">
                    <button
                      class="absolute right-2 top-2 inline-flex items-center justify-center rounded-md h-6 w-6 hover:bg-accent"
                      @click="copyToClipboard(formattedComposition, 'composition')"
                    >
                      <Check v-if="copiedPath === 'composition'" class="h-4 w-4 text-green-600" />
                      <Copy v-else class="h-4 w-4" />
                    </button>
                    <pre
                      v-if="rawComposition && !loading"
                      class="rounded-lg border bg-muted/30 p-3 text-xs overflow-x-auto max-h-64"
                    >{{ formattedComposition }}</pre>
                    <div v-else-if="loading" class="rounded-lg border bg-muted/30 p-8 text-center text-sm text-muted-foreground">
                      Loading...
                    </div>
                    <div v-else class="rounded-lg border bg-muted/30 p-8 text-center text-sm text-muted-foreground">
                      Composition data not available.
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="STRUCTURED" class="mt-2">
                  <div class="relative">
                    <button
                      class="absolute right-2 top-2 inline-flex items-center justify-center rounded-md h-6 w-6 hover:bg-accent"
                      @click="copyToClipboard(formattedComposition, 'composition')"
                    >
                      <Check v-if="copiedPath === 'composition'" class="h-4 w-4 text-green-600" />
                      <Copy v-else class="h-4 w-4" />
                    </button>
                    <pre
                      v-if="rawComposition && !loading"
                      class="rounded-lg border bg-muted/30 p-3 text-xs overflow-x-auto max-h-64"
                    >{{ formattedComposition }}</pre>
                    <div v-else-if="loading" class="rounded-lg border bg-muted/30 p-8 text-center text-sm text-muted-foreground">
                      Loading...
                    </div>
                  </div>
                </TabsContent>
              </TabsRoot>
            </div>
          </div>

          <div v-else class="text-center text-muted-foreground py-8">
            Select a vital signs reading to view its openEHR structure.
          </div>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
