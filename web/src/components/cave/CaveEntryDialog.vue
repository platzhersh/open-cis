<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { X, Loader2, Plus, Trash2 } from 'lucide-vue-next'
import { useCaveStore } from '@/stores/cave'
import type { CaveEntry, ReactionEvent, CaveCategory, CaveReactionType, CaveCriticality } from '@/types/cave'

const props = defineProps<{
  open: boolean
  patientId: string
  editEntry?: CaveEntry | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const store = useCaveStore()

// Form state
const substance = ref('')
const category = ref<CaveCategory>('medication')
const reactionType = ref<CaveReactionType>('allergy')
const criticality = ref<CaveCriticality>('indeterminate')
const onsetDate = ref('')
const comment = ref('')
const reactions = ref<ReactionEvent[]>([])

const submitting = ref(false)
const formError = ref<string | null>(null)

const isEditing = computed(() => !!props.editEntry)

// Initialize form when dialog opens
watch(
  () => props.open,
  (isOpen: boolean) => {
    if (isOpen) {
      formError.value = null
      if (props.editEntry) {
        substance.value = props.editEntry.substance
        category.value = props.editEntry.category
        reactionType.value = props.editEntry.reaction_type
        criticality.value = props.editEntry.criticality
        onsetDate.value = props.editEntry.onset_date?.split('T')[0] || ''
        comment.value = props.editEntry.comment || ''
        reactions.value = props.editEntry.reactions.map((r: ReactionEvent) => ({ ...r }))
      } else {
        substance.value = ''
        category.value = 'medication'
        reactionType.value = 'allergy'
        criticality.value = 'indeterminate'
        onsetDate.value = ''
        comment.value = ''
        reactions.value = []
      }
    }
  }
)

function addReaction() {
  reactions.value.push({
    manifestation: '',
    severity: 'moderate',
    certainty: 'suspected',
    onset_date: null,
    description: null,
  })
}

function removeReaction(index: number) {
  reactions.value.splice(index, 1)
}

const canSubmit = computed(() => {
  if (!substance.value.trim()) return false
  // Validate all reactions have manifestation
  for (const r of reactions.value) {
    if (!r.manifestation.trim()) return false
  }
  return !submitting.value
})

async function handleSubmit() {
  if (!canSubmit.value) return

  formError.value = null
  submitting.value = true

  try {
    if (isEditing.value && props.editEntry) {
      // Update existing entry
      const result = await store.updateEntry(
        props.editEntry.composition_uid,
        props.patientId,
        {
          criticality: criticality.value,
          status: props.editEntry.status,
          comment: comment.value || null,
          reactions: reactions.value,
        }
      )
      if (!result) {
        formError.value = store.error || 'Failed to update CAVE entry'
        return
      }
    } else {
      // Create new entry
      const result = await store.createEntry({
        patient_id: props.patientId,
        substance: substance.value.trim(),
        category: category.value,
        reaction_type: reactionType.value,
        criticality: criticality.value,
        onset_date: onsetDate.value || null,
        comment: comment.value || null,
        reactions: reactions.value,
      })
      if (!result) {
        formError.value = store.error || 'Failed to create CAVE entry'
        return
      }
    }

    emit('saved')
    emit('update:open', false)
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'An error occurred'
  } finally {
    submitting.value = false
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
      <DialogContent class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg border shadow-lg w-full max-w-lg max-h-[85vh] overflow-y-auto p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
        <div class="flex items-center justify-between mb-4">
          <DialogTitle class="text-lg font-semibold">
            {{ isEditing ? 'Edit CAVE Entry' : 'Add Allergy / Adverse Reaction' }}
          </DialogTitle>
          <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
            <X class="h-4 w-4" />
            <span class="sr-only">Close</span>
          </DialogClose>
        </div>

        <DialogDescription class="text-sm text-muted-foreground mb-4">
          Record an allergy, intolerance, or adverse reaction.
        </DialogDescription>

        <form class="space-y-4" @submit.prevent="handleSubmit">
          <!-- Substance -->
          <div class="space-y-2">
            <label for="substance" class="text-sm font-medium">
              Substance <span class="text-destructive">*</span>
            </label>
            <input
              id="substance"
              v-model="substance"
              type="text"
              required
              maxlength="200"
              placeholder="e.g., Penicillin, Peanuts, Latex"
              :disabled="isEditing"
              :class="[
                'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                isEditing ? 'opacity-60' : ''
              ]"
            />
          </div>

          <!-- Category -->
          <div class="space-y-2">
            <label class="text-sm font-medium">
              Category <span class="text-destructive">*</span>
            </label>
            <div class="flex flex-wrap gap-3">
              <label
                v-for="opt in (['medication', 'food', 'environment', 'other'] as const)"
                :key="opt"
                class="flex items-center gap-1.5 text-sm"
              >
                <input
                  v-model="category"
                  type="radio"
                  :value="opt"
                  :disabled="isEditing"
                  class="accent-primary"
                />
                {{ opt.charAt(0).toUpperCase() + opt.slice(1) }}
              </label>
            </div>
          </div>

          <!-- Reaction Type -->
          <div class="space-y-2">
            <label class="text-sm font-medium">
              Reaction Type <span class="text-destructive">*</span>
            </label>
            <div class="flex flex-wrap gap-3">
              <label
                v-for="opt in (['allergy', 'intolerance', 'unknown'] as const)"
                :key="opt"
                class="flex items-center gap-1.5 text-sm"
              >
                <input
                  v-model="reactionType"
                  type="radio"
                  :value="opt"
                  :disabled="isEditing"
                  class="accent-primary"
                />
                {{ opt === 'allergy' ? 'Allergy (immune-mediated)' : opt === 'intolerance' ? 'Intolerance (non-immune)' : 'Unknown' }}
              </label>
            </div>
          </div>

          <!-- Criticality -->
          <div class="space-y-2">
            <label class="text-sm font-medium">
              Criticality <span class="text-destructive">*</span>
            </label>
            <div class="flex flex-wrap gap-3">
              <label
                v-for="opt in (['low', 'high', 'indeterminate'] as const)"
                :key="opt"
                class="flex items-center gap-1.5 text-sm"
              >
                <input
                  v-model="criticality"
                  type="radio"
                  :value="opt"
                  class="accent-primary"
                />
                {{ opt.charAt(0).toUpperCase() + opt.slice(1) }}
              </label>
            </div>
          </div>

          <!-- Onset Date -->
          <div class="space-y-2">
            <label for="onset-date" class="text-sm font-medium">
              Onset Date
            </label>
            <input
              id="onset-date"
              v-model="onsetDate"
              type="date"
              :max="new Date().toISOString().split('T')[0]"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>

          <!-- Reaction Events -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium">Reaction Events</label>
              <button
                type="button"
                class="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                @click="addReaction"
              >
                <Plus class="h-3 w-3" />
                Add Reaction
              </button>
            </div>

            <div
              v-for="(reaction, index) in reactions"
              :key="index"
              class="rounded-md border p-3 space-y-3"
            >
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium text-muted-foreground">Reaction #{{ Number(index) + 1 }}</span>
                <button
                  type="button"
                  class="text-destructive hover:text-destructive/80"
                  @click="removeReaction(index)"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                </button>
              </div>

              <div class="space-y-2">
                <label :for="`manifestation-${index}`" class="text-xs font-medium">
                  Manifestation <span class="text-destructive">*</span>
                </label>
                <input
                  :id="`manifestation-${index}`"
                  v-model="reaction.manifestation"
                  type="text"
                  required
                  maxlength="200"
                  placeholder="e.g., Anaphylaxis, Urticaria, Nausea"
                  class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="text-xs font-medium">Severity</label>
                  <select
                    v-model="reaction.severity"
                    class="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
                  >
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                  </select>
                </div>
                <div class="space-y-1">
                  <label class="text-xs font-medium">Certainty</label>
                  <select
                    v-model="reaction.certainty"
                    class="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
                  >
                    <option value="suspected">Suspected</option>
                    <option value="likely">Likely</option>
                    <option value="confirmed">Confirmed</option>
                  </select>
                </div>
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium">Description</label>
                <input
                  v-model="reaction.description"
                  type="text"
                  maxlength="500"
                  placeholder="Optional details about the reaction"
                  class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
            </div>
          </div>

          <!-- Comment -->
          <div class="space-y-2">
            <label for="comment" class="text-sm font-medium">Clinical Notes</label>
            <textarea
              id="comment"
              v-model="comment"
              maxlength="1000"
              rows="2"
              placeholder="Optional clinical notes"
              class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>

          <!-- Error -->
          <div v-if="formError" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {{ formError }}
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-10 px-4 py-2 hover:bg-accent hover:text-accent-foreground"
              @click="handleOpenChange(false)"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
              :disabled="!canSubmit"
            >
              <Loader2 v-if="submitting" class="h-4 w-4 mr-2 animate-spin" />
              {{ isEditing ? 'Save Changes' : 'Save Entry' }}
            </button>
          </div>
        </form>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
