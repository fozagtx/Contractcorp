<script setup lang="ts">
const cop = useContractCop()
</script>

<template>
  <div>
    <h1>The signed contract.</h1>
    <p class="sub">
      Every clause and its sales policy, straight from Zetaris.
    </p>
    <p v-if="cop.railError.value" class="err">
      Clauses unavailable. Is Zetaris up?
      <button type="button" class="retry" @click="cop.loadClauses">Retry</button>
    </p>
    <section class="clauses" aria-live="polite">
      <article v-for="c in cop.clauses.value" :key="c.clause_id" class="clause">
        <header>
          <span class="cid mono">Clause {{ c.clause_id }}</span>
          <h2>{{ c.section }}</h2>
        </header>
        <p class="ctext">{{ c.text }}</p>
        <p v-if="c.policy_id" class="cpol">
          <span class="mono">Policy {{ c.policy_id }}</span>
          <span class="rule">{{ c.policy_rule }}</span>
        </p>
      </article>
    </section>
  </div>
</template>

<style scoped>
h1 {
  font-size: 56px;
  font-weight: 500;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 16px;
}
.sub {
  color: var(--ink-2);
  font-weight: 400;
  margin-bottom: 36px;
  max-width: 560px;
}
.err { color: var(--red); font-size: 13px; }
.retry { text-decoration: underline; margin-left: 6px; }
.clauses { display: flex; flex-direction: column; }
.clause {
  padding: 22px 0;
  border-top: 1px solid var(--line);
}
.clause header { display: flex; align-items: baseline; gap: 12px; }
.cid { color: var(--ink-2); flex: none; }
h2 { font-size: 19px; font-weight: 400; letter-spacing: -0.01em; }
.ctext { margin-top: 10px; font-weight: 400; }
.cpol { margin-top: 14px; display: flex; gap: 8px; align-items: baseline; }
.cpol .mono { color: var(--ink); flex: none; }
.rule { color: var(--ink-2); font-weight: 400; }
@media (max-width: 900px) {
  h1 { font-size: 40px; }
}
</style>
