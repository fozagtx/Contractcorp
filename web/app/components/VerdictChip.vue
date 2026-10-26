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
  padding: 3px 10px;
  border-radius: var(--pill);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.contradiction { color: var(--red); background: #fdeceb; }
.consistent { color: var(--green); background: #e8f5ec; }
.unclear { color: var(--amber); background: #fbf1dc; }
.unrelated { color: var(--ink-3); background: #f1efe9; }
</style>
