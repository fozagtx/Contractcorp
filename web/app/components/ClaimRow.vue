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

const showSaidSigned = computed(
  () =>
    props.e.verdict === 'contradiction' &&
    !!(props.e.spans?.claim || props.e.spans?.clause),
)

const saidHtml = computed(() =>
  markSpans(props.e.claim, [props.e.spans?.claim], 'm-said'),
)

const signedHtml = computed(() =>
  markSpans(props.e.clause?.text ?? '', [props.e.spans?.clause], 'm-signed'),
)
</script>

<template>
  <article class="row">
    <button
      type="button"
      class="row-head"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span class="vdot" :class="e.verdict" aria-hidden="true"></span>
      <span class="mid">
        <span class="claim">"{{ e.claim }}"</span>
        <span class="desc">{{ descriptor }}</span>
      </span>
      <span class="side">
        <VerdictChip :verdict="e.verdict" />
        <span class="secs mono">{{ seconds }}</span>
      </span>
    </button>
    <div v-if="open" class="row-body">
      <div v-if="showSaidSigned" class="svs">
        <div class="panel">
          <span class="plabel mono"><i class="pdot said" aria-hidden="true"></i>Rep said</span>
          <p class="ptext" v-html="saidHtml"></p>
        </div>
        <div class="panel">
          <span class="plabel mono"><i class="pdot signed" aria-hidden="true"></i>Contract says</span>
          <p class="ptext" v-html="signedHtml"></p>
        </div>
      </div>
      <blockquote v-if="e.clause" class="clausequote">
        <p v-html="signedHtml"></p>
        <figcaption class="mono">
          Clause {{ e.clause.clause_id }} · {{ e.clause.section }} · from Zetaris
        </figcaption>
      </blockquote>
      <p v-if="e.policy" class="policy">
        <span class="mono">Policy {{ e.policy.policy_id }}</span> {{ e.policy.rule }}
      </p>
      <div v-if="e.reason" class="why">
        <span class="label">Why</span>
        <p>{{ e.reason }}</p>
      </div>
      <div v-if="memoryLines.length" class="memory">
        <span class="label">H-Mem recalled</span>
        <p v-for="(m, i) in memoryLines" :key="i" class="mem mono">
          <span v-if="m.when">{{ m.when }} · </span>{{ m.text }}
        </p>
      </div>
      <div v-if="e.sql" class="sqlwrap">
        <span class="label">SQL</span>
        <pre class="mono">{{ e.sql }}</pre>
      </div>
      <p v-if="footer" class="foot mono">{{ footer }}</p>
    </div>
  </article>
</template>

<style scoped>
.row-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  text-align: left;
  padding: 14px 20px;
  min-height: 40px;
  transition: background 0.15s;
}
.row-head:hover { background: #fbfaf7; }
.vdot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
  flex: none;
}
.vdot.contradiction { background: var(--red); }
.vdot.consistent { background: var(--green); }
.vdot.unclear { background: var(--amber); }
.vdot.unrelated { background: var(--ink-3); }
.mid { flex: 1; min-width: 0; }
.claim { display: block; font-weight: 500; font-size: 15px; color: var(--ink); }
.desc {
  display: block;
  font-size: 13px;
  color: var(--ink-2);
  margin-top: 2px;
  word-break: break-word;
}
.side {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}
.secs { color: var(--ink-3); font-size: 11.5px; }
.row-body {
  padding: 14px 20px 18px;
  background: #fbfaf7;
  border-top: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.svs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.panel {
  background: #fbfaf7;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 14px;
}
.plabel {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-3);
  margin-bottom: 8px;
}
.pdot { width: 7px; height: 7px; border-radius: 50%; }
.pdot.said { background: var(--red); }
.pdot.signed { background: var(--green); }
.ptext { font-size: 14px; line-height: 22px; }
:deep(mark.m-said) {
  background: #fdeceb;
  color: var(--red);
  padding: 0 2px;
  border-radius: 3px;
}
:deep(mark.m-signed) {
  background: #e8f5ec;
  color: var(--green);
  padding: 0 2px;
  border-radius: 3px;
}
@media (max-width: 640px) {
  .svs { grid-template-columns: 1fr; }
}
.clausequote {
  border-left: 2px solid var(--accent);
  padding-left: 14px;
}
.clausequote p { font-size: 14.5px; }
.clausequote figcaption { color: var(--ink-3); margin-top: 6px; font-size: 11.5px; }
.policy { font-size: 14px; color: var(--ink-2); }
.policy .mono { color: var(--ink); font-size: 12px; margin-right: 6px; }
.label {
  display: block;
  margin-bottom: 6px;
}
.why p, .policy { font-weight: 400; }
.mem { color: var(--ink-2); font-size: 12px; }
pre {
  background: #f3f1ec;
  border-radius: 8px;
  padding: 12px 14px;
  overflow-x: auto;
  white-space: pre;
  color: var(--ink);
  font-size: 12px;
}
.foot { color: var(--ink-3); font-size: 11.5px; }
</style>
