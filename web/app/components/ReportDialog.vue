<script setup lang="ts">
import type { Report } from '~/composables/useContractCop'

const { loadReport } = useContractCop()

const dlg = ref<HTMLDialogElement | null>(null)
const report = ref<Report | null>(null)
const loading = ref(false)
const failed = ref(false)

async function open() {
  report.value = null
  failed.value = false
  loading.value = true
  dlg.value?.showModal()
  const r = await loadReport()
  loading.value = false
  if (r) report.value = r
  else failed.value = true
}

function clock(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString()
}

defineExpose({ open })
</script>

<template>
  <dialog ref="dlg">
    <h3>End-of-call report</h3>
    <p v-if="loading" class="sub">Loading…</p>
    <p v-else-if="failed" class="sub">Could not load the report. Is the server up?</p>
    <template v-else-if="report">
      <p class="sub mono">
        session {{ report.session }} · {{ report.claims_total }} claims ·
        {{ report.contradictions }} contradictions
      </p>
      <table v-if="report.timeline.length">
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
      <p v-else class="sub">No claims in this session yet.</p>
    </template>
    <div class="drow">
      <button type="button" class="cancel" @click="dlg?.close()">Close</button>
    </div>
  </dialog>
</template>

<style scoped>
h3 { font-weight: 500; font-size: 17px; }
.sub { color: var(--ink-2); font-weight: 300; margin-top: 6px; }
table {
  margin-top: 14px;
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
.drow { margin-top: 18px; display: flex; justify-content: flex-end; }
.cancel {
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  font-size: 13.5px;
}
.cancel:hover { background: var(--surface); }
</style>
