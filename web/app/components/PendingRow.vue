<script setup lang="ts">
import type { PendingState } from '~/composables/useContractCop'

const props = defineProps<{ pending: PendingState }>()

const steps = ['routing', 'zetaris', 'judging'] as const

const activeIdx = computed(() => steps.indexOf(props.pending.stage))
</script>

<template>
  <article class="row pending">
    <template v-if="pending.progress">
      <p class="pline mono">
        Checking transcript: {{ pending.progress.done }} of {{ pending.progress.total }}
      </p>
      <p class="cur">"{{ pending.progress.line }}"</p>
    </template>
    <p v-else class="steps mono">
      <template v-for="(s, i) in steps" :key="s">
        <span :class="{ active: i === activeIdx, done: i < activeIdx }">{{ s }}</span>
        <span v-if="i < steps.length - 1" class="sep">→</span>
      </template>
    </p>
  </article>
</template>

<style scoped>
.row {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fff;
  padding: 16px 18px;
}
.steps { display: flex; gap: 10px; align-items: center; color: var(--ink-2); }
.steps .active { color: var(--ink); }
.steps .done { color: var(--green); }
.sep { color: var(--ink-2); }
.pline { color: var(--ink); }
.cur { font-weight: 300; color: var(--ink-2); margin-top: 4px; }
</style>
