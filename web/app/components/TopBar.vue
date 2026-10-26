<script setup lang="ts">
defineProps<{ session: string }>()

const links = [
  { to: '/', label: 'Check' },
  { to: '/transcript', label: 'Transcript' },
  { to: '/contract', label: 'Contract' },
  { to: '/report', label: 'Report' },
]
</script>

<template>
  <header class="topbar">
    <span class="wordmark">ContractCop</span>
    <nav class="links">
      <NuxtLink
        v-for="l in links"
        :key="l.to"
        :to="l.to"
        class="navlink"
      >{{ l.label }}</NuxtLink>
    </nav>
    <span class="session mono">{{ session || 'no session yet' }}</span>
  </header>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 18px;
  height: 52px;
  padding: 0 24px;
  background: var(--bg);
  border-bottom: 1px solid var(--line);
}
.wordmark { font-weight: 500; font-size: 15px; letter-spacing: -0.01em; }
.links { display: flex; gap: 16px; }
.navlink {
  display: inline-flex;
  align-items: center;
  height: 52px;
  font-size: 14px;
  color: var(--ink-2);
  text-decoration: none;
  border-bottom: 1px solid transparent;
}
.navlink:hover { color: var(--ink); }
.navlink.router-link-active {
  color: var(--ink);
  border-bottom-color: var(--ink);
}
.session { margin-left: auto; color: var(--ink-2); }
@media (max-width: 900px) {
  .links { gap: 12px; }
  .navlink { font-size: 13px; }
  .session { display: none; }
  .topbar { gap: 14px; padding: 0 16px; }
}
</style>
