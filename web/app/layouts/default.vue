<script setup lang="ts">
const cop = useContractCop()

onMounted(() => {
  cop.loadHealth()
  cop.loadClauses()
})
</script>

<template>
  <div>
    <TopBar :session="cop.session.value" :health="cop.health.value" />
    <main class="content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.content {
  max-width: 1120px;
  margin: 0 auto;
  padding: 56px 40px 96px;
}
@media (max-width: 900px) {
  .content { padding: 40px 20px 80px; }
}
</style>
