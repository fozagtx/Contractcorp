<script setup lang="ts">
defineProps<{ session: string; health: 'ok' | 'bad' | 'unknown' }>()

const links = [
  { to: '/', label: 'Check' },
  { to: '/transcript', label: 'Transcript' },
  { to: '/contract', label: 'Contract' },
  { to: '/report', label: 'Report' },
]
</script>

<template>
  <header class="topbar">
    <NuxtLink to="/" class="brand">
      <span class="mark" aria-hidden="true"></span>
      <span class="wordmark">ContractCop</span>
    </NuxtLink>
    <nav class="links">
      <NuxtLink
        v-for="l in links"
        :key="l.to"
        :to="l.to"
        class="navlink"
      >{{ l.label }}</NuxtLink>
    </nav>
    <div class="right">
      <span class="health mono">
        <span class="dot" :class="health" aria-hidden="true"></span>
        Zetaris · Nemotron
      </span>
      <span class="session mono">{{ session || 'no session' }}</span>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 24px;
  height: 64px;
  padding: 0 28px;
  background: var(--bg);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  text-decoration: none;
  color: var(--ink);
}
.mark {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  flex: none;
}
.wordmark { font-weight: 600; font-size: 17px; letter-spacing: -0.01em; }
.links { display: flex; gap: 4px; }
.navlink {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 6px 12px;
  border-radius: var(--pill);
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-2);
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}
.navlink:hover { color: var(--ink); }
.navlink.router-link-active { color: var(--ink); background: #efece6; }
.right { margin-left: auto; display: flex; align-items: center; gap: 14px; }
.health {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: var(--ink-3);
}
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ink-3); }
.dot.ok { background: var(--green); }
.dot.bad { background: var(--red); }
.session {
  font-size: 12px;
  color: var(--ink-2);
  border: 1px solid var(--line);
  border-radius: var(--pill);
  padding: 5px 11px;
}
@media (max-width: 900px) {
  .topbar { gap: 14px; padding: 0 16px; }
  .links { gap: 0; }
  .navlink { font-size: 13px; padding: 6px 9px; }
  .health, .session { display: none; }
}
</style>
