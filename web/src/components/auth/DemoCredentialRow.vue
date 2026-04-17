<script setup lang="ts">
import { useClipboard } from '@vueuse/core'

const props = defineProps<{
  label: string
  email: string
  password: string
}>()

const { copy: copyEmail, copied: emailCopied } = useClipboard()
const { copy: copyPassword, copied: passwordCopied } = useClipboard()
</script>

<template>
  <div class="flex items-center justify-between gap-2">
    <span class="text-muted-foreground w-20 shrink-0">{{ label }}</span>
    <code class="flex-1 text-xs truncate">{{ email }}</code>
    <button
      type="button"
      :aria-label="`Copy ${label} email`"
      class="inline-flex items-center justify-center rounded text-xs px-2 py-1 hover:bg-accent text-muted-foreground shrink-0"
      @click="copyEmail(props.email)"
    >
      {{ emailCopied ? 'Copied' : 'Copy' }}
    </button>
    <code class="w-20 text-xs shrink-0">{{ password }}</code>
    <button
      type="button"
      :aria-label="`Copy ${label} password`"
      class="inline-flex items-center justify-center rounded text-xs px-2 py-1 hover:bg-accent text-muted-foreground shrink-0"
      @click="copyPassword(props.password)"
    >
      {{ passwordCopied ? 'Copied' : 'Copy' }}
    </button>
  </div>
</template>
