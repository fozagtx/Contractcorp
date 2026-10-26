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
  <div class="wrap">
    <h1>End-of-call <em>report</em>.</h1>
    <p><span class="session mono">session {{ cop.session.value || 'new' }}</span></p>

    <div class="stats">
      <div v-for="s in stats" :key="s.label" class="stat">
        <span class="n">{{ s.value }}</span>
        <span class="label">{{ s.label }}</span>
      </div>
    </div>

    <div class="drow">
      <button type="button" class="ghost" :disabled="loading" @click="refresh">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
      <button type="button" class="go" @click="newSession">New session</button>
    </div>

    <p v-if="failed" class="err">Could not load the report. Is the server up?</p>
    <div v-else-if="report?.timeline.length" class="tablewrap">
      <table>
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
    </div>
    <p v-else-if="!loading" class="sub">No claims in this session yet.</p>
  </div>
</template>

<style scoped>
.wrap { max-width: 900px; margin: 0 auto; }
h1 {
  font-family: var(--serif);
  font-size: 64px;
  font-weight: 400;
  letter-spacing: -0.015em;
  line-height: 0.98;
  margin-bottom: 18px;
}
h1 em { font-style: italic; }
.session {
  font-size: 12px;
  color: var(--ink-2);
  border: 1px solid var(--line);
  border-radius: var(--pill);
  padding: 5px 11px;
}
.stats {
  margin-top: 30px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.stat {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.n { font-family: var(--serif); font-size: 40px; line-height: 1; }
.drow { margin-top: 18px; display: flex; gap: 10px; }
.ghost {
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid var(--line);
  border-radius: var(--pill);
  font-size: 14px;
  font-weight: 500;
}
.ghost:hover:not(:disabled) { background: #efece6; }
.ghost:disabled { opacity: 0.5; }
.go {
  min-height: 40px;
  padding: 0 16px;
  background: var(--accent);
  color: var(--accent-ink);
  font-weight: 600;
  font-size: 14px;
  border-radius: var(--pill);
}
.err { color: var(--red); font-size: 13px; margin-top: 18px; }
.sub { color: var(--ink-2); margin-top: 24px; }
.tablewrap {
  margin-top: 24px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
}
th {
  text-align: left;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-3);
  padding: 12px 16px 10px;
  border-bottom: 1px solid var(--line);
}
td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
tr:last-child td { border-bottom: 0; }
@media (max-width: 900px) {
  h1 { font-size: 44px; }
  .stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
