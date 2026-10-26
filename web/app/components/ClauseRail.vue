<script setup lang="ts">
import type { RailClause } from '~/composables/useContractCop'

defineProps<{
  clauses: RailClause[]
  health: 'ok' | 'bad' | 'unknown'
  railError: boolean
}>()

const emit = defineEmits<{ retry: [] }>()
const open = ref<string | null>(null)
</script>

<template>
  <aside class="rail">
    <div class="rail-title mono">Signed contract</div>
    <div v-if="railError" class="rail-err">
      Clauses unavailable. Is Zetaris up?
      <button type="button" class="retry" @click="emit('retry')">Retry</button>
    </div>
    <template v-else>
      <button
        v-for="c in clauses"
        :key="c.clause_id"
        type="button"
        class="clause"
        :aria-expanded="open === c.clause_id"
        @click="open = open === c.clause_id ? null : c.clause_id"
      >
        <span class="cid mono">{{ c.clause_id }}</span>
        <span class="sec">{{ c.section }}</span>
        <span v-if="open === c.clause_id" class="ctext">{{ c.text }}</span>
        <span v-if="open === c.clause_id && c.policy_id" class="cpol mono">
          Policy {{ c.policy_id }}: {{ c.policy_rule }}
        </span>
      </button>
    </template>
    <div class="rail-foot mono">
      <span class="dot" :class="health" aria-hidden="true"></span>
      Zetaris {{ health === 'ok' ? 'ok' : health === 'bad' ? 'down' : '…' }} · Nemotron via Nightshift
    </div>
  </aside>
</template>

<style scoped>
.rail {
  width: 248px;
  flex: none;
  border-right: 1px solid var(--line);
  padding: 20px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: sticky;
  top: 52px;
  height: calc(100vh - 52px);
  overflow-y: auto;
}
.rail-title {
  color: var(--ink-2);
  padding: 0 10px;
  margin-bottom: 10px;
}
.clause {
  display: block;
  text-align: left;
  width: 100%;
  padding: 8px 10px;
  border-radius: var(--radius);
  min-height: 40px;
  transition: background 0.15s;
}
.clause:hover { background: var(--surface); }
.cid { color: var(--ink-2); }
.sec { font-size: 13.5px; margin-left: 8px; }
.ctext {
  display: block;
  font-size: 12.5px;
  font-weight: 400;
  color: var(--ink-2);
  line-height: 1.5;
  margin-top: 6px;
}
.cpol {
  display: block;
  color: var(--ink-2);
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed var(--line);
}
.rail-err { padding: 8px 10px; color: var(--red); font-size: 13px; }
.retry { text-decoration: underline; margin-left: 6px; }
.rail-foot {
  margin-top: auto;
  padding: 14px 10px 4px;
  color: var(--ink-2);
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--ink-2); flex: none; }
.dot.ok { background: var(--green); }
.dot.bad { background: var(--red); }
@media (max-width: 900px) {
  .rail { display: none; }
}
</style>
