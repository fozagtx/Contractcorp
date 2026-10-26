<script setup lang="ts">
import type { Verdict } from '~/composables/useContractCop'

defineProps<{ verdict: Verdict }>()

const labels: Record<Verdict, string> = {
  contradiction: 'Contradiction',
  consistent: 'Consistent',
  unclear: 'Unclear',
  unrelated: 'Unrelated',
}
</script>

<template>
  <span class="chip mono" :class="verdict">{{ labels[verdict] }}</span>
</template>

<style scoped>
.chip {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.contradiction { color: var(--red); border: 1px solid color-mix(in srgb, var(--red) 40%, transparent); background: color-mix(in srgb, var(--red) 10%, transparent); }
.consistent { color: var(--green); border: 1px solid color-mix(in srgb, var(--green) 40%, transparent); background: color-mix(in srgb, var(--green) 10%, transparent); }
.unclear { color: var(--amber); border: 1px solid color-mix(in srgb, var(--amber) 40%, transparent); background: color-mix(in srgb, var(--amber) 10%, transparent); }
.unrelated { color: var(--ink-2); border: 1px solid color-mix(in srgb, var(--ink-2) 40%, transparent); background: color-mix(in srgb, var(--ink-2) 10%, transparent); }
</style>
