<script setup lang="ts">
const cop = useContractCop()
</script>

<template>
  <div class="wrap">
    <h1>The <em>signed</em> contract.</h1>
    <p class="sub">Five clauses, served live from Zetaris.</p>
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
        <div v-if="c.policy_id" class="cpol">
          <span class="label">Policy {{ c.policy_id }}</span>
          <p class="rule">{{ c.policy_rule }}</p>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
.wrap { max-width: 760px; margin: 0 auto; }
h1 {
  font-family: var(--serif);
  font-size: 64px;
  font-weight: 400;
  letter-spacing: -0.015em;
  line-height: 0.98;
  margin-bottom: 18px;
}
h1 em { font-style: italic; }
.sub {
  font-size: 18px;
  line-height: 26px;
  color: var(--ink-2);
  margin-bottom: 40px;
}
.err { color: var(--red); font-size: 13px; }
.retry { text-decoration: underline; margin-left: 6px; }
.clauses { display: flex; flex-direction: column; gap: 18px; }
.clause {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 22px 24px;
}
.clause header { display: flex; align-items: center; gap: 12px; }
.cid {
  font-size: 11.5px;
  color: var(--ink-2);
  border: 1px solid var(--line);
  border-radius: var(--pill);
  padding: 4px 10px;
  flex: none;
}
h2 { font-size: 18px; font-weight: 600; letter-spacing: -0.01em; }
.ctext { margin-top: 14px; font-size: 16px; line-height: 26px; }
.cpol {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}
.cpol .label { display: block; margin-bottom: 4px; }
.rule { color: var(--ink-2); font-size: 14px; }
@media (max-width: 900px) {
  h1 { font-size: 44px; }
}
</style>
