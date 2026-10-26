<script setup lang="ts">
import type { PendingState } from '~/composables/useContractCop'

const props = defineProps<{ pending: PendingState }>()

const steps = ['routing', 'zetaris', 'judging'] as const
const activeIdx = computed(() => steps.indexOf(props.pending.stage))
</script>

<template>
  <article class="row pending">
    <div class="row-head">
      <span class="vdot" aria-hidden="true"></span>
      <span class="mid">
        <span class="claim" v-if="pending.progress">"{{ pending.progress.line }}"</span>
        <span class="claim" v-else>Checking the claim</span>
        <span class="desc steps mono" v-if="!pending.progress">
          <template v-for="(s, i) in steps" :key="s">
            <span :class="{ active: i === activeIdx, done: i < activeIdx }">{{ s }}</span>
            <span v-if="i < steps.length - 1" class="sep">→</span>
          </template>
        </span>
        <span class="desc" v-else>line {{ pending.progress.done }} of {{ pending.progress.total }}</span>
      </span>
      <span class="side">
        <span class="chip mono">Checking</span>
      </span>
    </div>
  </article>
</template>

<style scoped>
.row-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  padding: 14px 20px;
}
.vdot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
  flex: none;
  background: var(--accent);
  animation: pulse 1.1s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.8); }
}
.mid { flex: 1; min-width: 0; }
.claim { display: block; font-weight: 500; font-size: 15px; }
.desc { display: block; font-size: 13px; color: var(--ink-2); margin-top: 2px; }
.steps { display: flex; gap: 8px; align-items: center; font-size: 12px; }
.steps .active { color: var(--ink); font-weight: 500; }
.steps .done { color: var(--green); }
.sep { color: var(--ink-3); }
.side { flex: none; }
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
  color: var(--accent);
  background: #fde9df;
}
</style>
