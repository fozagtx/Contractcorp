<script setup lang="ts">
import type { Report } from '~/composables/useContractCop'

const cop = useContractCop()

const report = ref<Report | null>(null)
const loading = ref(false)
const failed = ref(false)

async function refresh() {
  loading.value = true
  failed.value = false
  const r = await cop.loadReport()
  loading.value = false
  if (r) report.value = r
  else failed.value = true
}

function newSession() {
  cop.newSession()
  report.value = null
  navigateTo('/')
}

function clock(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString()
}

const stats = computed(() => [
  { label: 'checked', value: cop.checked.value },
  { label: 'contradictions', value: cop.counts.value.contradiction },
  { label: 'consistent', value: cop.counts.value.consistent },
  { label: 'unclear', value: cop.counts.value.unclear },
])

onMounted(refresh)
</script>

<template>
  <div>
    <h1>End-of-call report.</h1>
    <p class="sub mono">session {{ cop.session.value || 'new' }}</p>

    <div class="stats mono">
      <div v-for="s in stats" :key="s.label" class="stat">
        <span class="n">{{ s.value }}</span>
        <span class="l">{{ s.label }}</span>
      </div>
    </div>

    <div class="drow">
      <button type="button" class="ghost" :disabled="loading" @click="refresh">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
      <button type="button" class="ghost" @click="newSession">New session</button>
    </div>

    <p v-if="failed" class="err">Could not load the report. Is the server up?</p>
    <table v-else-if="report?.timeline.length">
      <thead>
        <tr>
          <th>Time</th>
          <th>Verdict</th>
          <th>Claim</th>
          <th>Clause</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(h, i) in report.timeline" :key="i">
          <td class="mono">{{ clock(h.ts) }}</td>
          <td><VerdictChip :verdict="h.verdict" /></td>
          <td class="claim">"{{ h.claim }}"</td>
          <td class="mono">{{ h.clause_id || '-' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading" class="sub">No claims in this session yet.</p>
  </div>
</template>

<style scoped>
h1 {
  font-size: 56px;
  font-weight: 300;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 12px;
}
.sub { color: var(--ink-2); font-weight: 300; }
.stats {
  margin-top: 28px;
  display: flex;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}
.stat {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 14px 18px 14px 0;
  margin-right: 18px;
  border-right: 1px solid var(--line);
}
.stat:last-child { border-right: 0; }
.n { font-size: 22px; color: var(--ink); }
.l { font-size: 11px; color: var(--ink-2); text-transform: uppercase; letter-spacing: 0.04em; }
.drow { margin-top: 16px; display: flex; gap: 10px; }
.ghost {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  font-size: 13px;
}
.ghost:hover:not(:disabled) { background: var(--surface); }
.ghost:disabled { opacity: 0.5; }
.err { color: var(--red); font-size: 13px; margin-top: 16px; }
table {
  margin-top: 28px;
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--ink-2);
  padding: 6px 8px 6px 0;
  border-bottom: 1px solid var(--line);
}
td {
  padding: 8px 8px 8px 0;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
td.claim { font-weight: 300; }
@media (max-width: 900px) {
  h1 { font-size: 40px; }
  .stats { flex-wrap: wrap; }
  .stat { border-right: 0; }
}
</style>
