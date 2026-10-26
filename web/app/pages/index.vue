<script setup lang="ts">
const cop = useContractCop()

const composer = ref<InstanceType<typeof ClaimComposer> | null>(null)

const tries = [
  'We will give you the 10 percent automatic discount, no approval needed.',
  'On the Standard Plan, support runs 9 to 5, Monday through Friday.',
]

function onKey(e: KeyboardEvent) {
  const target = e.target as HTMLElement
  if (e.key === '/' && !['TEXTAREA', 'INPUT'].includes(target.tagName)) {
    e.preventDefault()
    composer.value?.focus()
  }
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="grid">
    <section class="hero">
      <h1>Every claim, <em>checked</em> against the signed contract.</h1>
      <p class="sub">
        Type one sentence a salesperson said to a customer. ContractCop checks it
        against the signed contract and shows the exact clause, the policy rule,
        the database query and the model behind the answer.
      </p>
      <NuxtLink
        v-if="!cop.contracts.value.length"
        to="/contract"
        class="needcard"
      >Upload a contract first</NuxtLink>
      <ClaimComposer
        v-else
        ref="composer"
        :checked="cop.checked.value"
        :contradictions="cop.contradictions.value"
        :session="cop.session.value"
        :busy="!!cop.pending.value && !cop.pending.value.progress"
        @submit="cop.checkClaim"
      />
      <p class="try">
        <span class="label">Try:</span>
        <button
          v-for="t in tries"
          :key="t"
          type="button"
          class="chip"
          @click="composer?.fill(t)"
        >{{ t }}</button>
      </p>
    </section>
    <FeedCard />
  </div>
</template>

<style scoped>
.needcard {
  display: block;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 16px 18px;
  color: var(--ink-2);
  font-size: 14px;
  text-decoration: none;
}
.needcard:hover { color: var(--ink); }
.grid {
  display: grid;
  grid-template-columns: minmax(0, 440px) minmax(0, 1fr);
  gap: 56px;
  align-items: start;
}
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
  margin-bottom: 30px;
}
.try { margin-top: 18px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.try .label { margin-right: 2px; }
.chip {
  border: 1px solid var(--line);
  border-radius: var(--pill);
  padding: 6px 12px;
  font-size: 12.5px;
  color: var(--ink-2);
  background: transparent;
  max-width: 100%;
  text-align: left;
  transition: background 0.15s, color 0.15s;
}
.chip:hover { background: #efece6; color: var(--ink); }
@media (max-width: 1024px) {
  .grid { grid-template-columns: 1fr; gap: 40px; }
}
@media (max-width: 900px) {
  h1 { font-size: 44px; }
}
</style>
