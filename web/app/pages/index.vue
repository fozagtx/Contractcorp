<script setup lang="ts">
const cop = useContractCop()

const composer = ref<InstanceType<typeof ClaimComposer> | null>(null)

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
  <div>
    <h1>Every claim, checked against the signed contract.</h1>
    <p class="sub">
      Paste what the rep said. The verdict cites the clause, the policy, the
      SQL and the model.
    </p>
    <ClaimComposer
      ref="composer"
      :checked="cop.checked.value"
      :contradictions="cop.contradictions.value"
      :session="cop.session.value"
      :busy="!!cop.pending.value && !cop.pending.value.progress"
      @submit="cop.checkClaim"
    />
    <section class="feed" aria-live="polite">
      <EmptyState
        v-if="!cop.events.value.length && !cop.pending.value"
        @suggest="composer?.fill($event)"
      />
      <ClaimRow v-for="(e, i) in cop.events.value" :key="i" :e="e" />
      <PendingRow v-if="cop.pending.value" :pending="cop.pending.value" />
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
.feed {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
@media (max-width: 900px) {
  h1 { font-size: 40px; }
}
</style>
