<script setup lang="ts">
const cop = useContractCop()
</script>

<template>
  <div class="feedcard-wrap">
    <section class="feedcard" aria-live="polite">
      <EmptyState v-if="!cop.events.value.length && !cop.pending.value" />
      <ClaimRow v-for="(e, i) in cop.events.value" :key="i" :e="e" />
      <PendingRow v-if="cop.pending.value" :pending="cop.pending.value" />
    </section>
  </div>
</template>

<style scoped>
.feedcard-wrap { position: relative; }
.feedcard-wrap::before {
  content: '';
  position: absolute;
  inset: -8% -12%;
  z-index: 0;
  background:
    radial-gradient(closest-side, rgba(240, 90, 40, 0.18), transparent 70%) 15% 20% / 60% 55%,
    radial-gradient(closest-side, rgba(245, 183, 0, 0.12), transparent 70%) 80% 25% / 55% 50%,
    radial-gradient(closest-side, rgba(110, 168, 255, 0.1), transparent 70%) 60% 85% / 60% 55%;
  background-repeat: no-repeat;
  filter: blur(40px);
  pointer-events: none;
}
.feedcard {
  position: relative;
  z-index: 1;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.feedcard > :deep(* + *) { border-top: 1px solid var(--line); }
</style>
