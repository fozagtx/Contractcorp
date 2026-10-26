<script setup lang="ts">
const cop = useContractCop()
const route = useRoute()

const showRail = computed(() => route.path !== '/contract')

onMounted(() => {
  cop.loadHealth()
  cop.loadClauses()
})
</script>

<template>
  <div>
    <TopBar :session="cop.session.value" />
    <div class="frame">
      <ClauseRail
        v-if="showRail"
        :clauses="cop.clauses.value"
        :health="cop.health.value"
        :rail-error="cop.railError.value"
        @retry="cop.loadClauses"
      />
      <main class="content" :class="{ wide: !showRail }">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.frame { display: flex; min-height: calc(100vh - 52px); }
.content {
  flex: 1;
  min-width: 0;
  max-width: 760px;
  padding: 48px 40px 96px;
}
.content.wide { max-width: 860px; }
@media (max-width: 900px) {
  .content { padding: 40px 20px 80px; }
}
</style>
