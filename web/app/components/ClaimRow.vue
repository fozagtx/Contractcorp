<script setup lang="ts">
import type { ClaimEvent, MemoryItem } from '~/composables/useContractCop'

const props = defineProps<{ e: ClaimEvent }>()

const open = ref(props.e.open ?? props.e.verdict === 'contradiction')

const descriptor = computed(() => {
  const e = props.e
  switch (e.verdict) {
    case 'contradiction':
      return e.clause
        ? `contradicts Clause ${e.clause.clause_id}, ${e.clause.section}`
        : 'contradicts the signed contract'
    case 'consistent':
      return e.clause
        ? `allowed by Clause ${e.clause.clause_id}, ${e.clause.section}`
        : 'consistent with the contract'
    case 'unclear':
      return e.error ? `not enough to judge · ${e.error}` : 'not enough to judge'
    case 'unrelated':
      return 'nothing a contract could contradict'
  }
})

const seconds = computed(() =>
  props.e.ms != null ? (props.e.ms / 1000).toFixed(1) + 's' : '',
)

interface MemLine { when?: string; text: string }

const memoryLines = computed<MemLine[]>(() => {
  const out: MemLine[] = []
  const fmt = (m: MemoryItem, scope: string) =>
    `${scope}: "${m.claim}" -> ${m.verdict}${m.clause_id ? `, Clause ${m.clause_id}` : ''}`
  for (const m of props.e.memory?.same_session ?? [])
    out.push({ when: m.when, text: fmt(m, 'earlier this call') })
  for (const m of props.e.memory?.earlier_calls ?? [])
    out.push({ when: m.date, text: fmt(m, 'earlier call') })
  return out
})

const footer = computed(() => {
  const e = props.e
  const hops = (e.hops ?? []).filter((h) => h.ms != null)
  const parts: string[] = []
  if (e.model) parts.push(e.model)
  for (const h of hops) parts.push(`${h.hop} ${h.ms}ms`)
  if (e.sql_ms != null) parts.push(`zetaris ${e.sql_ms}ms`)
  if (e.ms != null) parts.push(`total ${e.ms}ms`)
  return parts.join(' · ')
})
</script>

<template>
  <article class="row" :class="{ open }">
    <button
      type="button"
      class="row-head"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span class="head-grid">
        <VerdictChip :verdict="e.verdict" />
        <span class="claim">"{{ e.claim }}"</span>
        <span class="secs mono">{{ seconds }}</span>
      </span>
      <span class="desc">
        {{ descriptor }}
        <span class="chev" aria-hidden="true">{{ open ? '▴' : '▾' }}</span>
      </span>
    </button>
    <div v-if="open" class="row-body">
      <blockquote v-if="e.clause" class="clausequote">
        <p>{{ e.clause.text }}</p>
        <figcaption class="mono">
          Clause {{ e.clause.clause_id }} · {{ e.clause.section }} · from Zetaris
        </figcaption>
      </blockquote>
      <p v-if="e.policy" class="policy">
        <span class="mono">Policy {{ e.policy.policy_id }}:</span> {{ e.policy.rule }}
      </p>
      <div v-if="e.reason" class="why">
        <span class="label mono">Why</span>
        <p>{{ e.reason }}</p>
      </div>
      <div v-if="memoryLines.length" class="memory">
        <span class="label mono">H-Mem recalled</span>
        <p v-for="(m, i) in memoryLines" :key="i" class="mem mono">
          <span v-if="m.when" class="when">{{ m.when }} · </span>{{ m.text }}
        </p>
      </div>
      <div v-if="e.sql" class="sqlwrap">
        <span class="label mono">SQL</span>
        <pre class="mono">{{ e.sql }}</pre>
      </div>
      <p v-if="footer" class="foot mono">{{ footer }}</p>
    </div>
  </article>
</template>

<style scoped>
.row {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fff;
  padding: 16px 18px;
  transition: background 0.15s;
}
.row:hover { background: var(--surface); }
.row-head {
  display: block;
  width: 100%;
  text-align: left;
  min-height: 40px;
}
.head-grid {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: baseline;
  gap: 12px;
}
.claim { font-weight: 400; }
.secs { color: var(--ink-2); text-align: right; }
.desc {
  display: block;
  font-weight: 300;
  color: var(--ink-2);
  margin-top: 4px;
  word-break: break-word;
}
.chev { margin-left: 8px; }
.row-body {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.clausequote {
  border-left: 2px solid var(--line);
  padding-left: 14px;
  font-weight: 300;
}
.clausequote figcaption { color: var(--ink-2); margin-top: 6px; }
.policy { font-weight: 300; }
.label {
  display: block;
  color: var(--ink-2);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 11px;
}
.why p { font-weight: 300; }
.mem { color: var(--ink-2); }
.when { color: var(--ink-2); }
pre {
  background: var(--surface-2);
  border-radius: var(--radius);
  padding: 12px 14px;
  overflow-x: auto;
  white-space: pre;
  color: var(--ink);
}
.foot { color: var(--ink-2); }
@media (prefers-reduced-motion: no-preference) {
  .row-body { animation: expand 160ms ease-out; }
  @keyframes expand {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: none; }
  }
}
</style>
