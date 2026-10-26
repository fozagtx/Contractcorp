<script setup lang="ts">
defineProps<{ session: string }>()
const emit = defineEmits<{ transcript: []; report: [] }>()
</script>

<template>
  <header class="topbar">
    <span class="wordmark">ContractCop</span>
    <span class="session mono">{{ session || 'no session yet' }}</span>
    <nav class="actions">
      <button type="button" class="ghost" @click="emit('transcript')">Transcript</button>
      <button type="button" class="ghost" @click="emit('report')">End-of-call report</button>
    </nav>
  </header>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 14px;
  height: 52px;
  padding: 0 24px;
  background: var(--bg);
  border-bottom: 1px solid var(--line);
}
.wordmark { font-weight: 500; font-size: 15px; letter-spacing: -0.01em; }
.session { color: var(--ink-2); }
.actions { margin-left: auto; display: flex; gap: 8px; }
.ghost {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--ink);
  background: transparent;
  transition: background 0.15s;
}
.ghost:hover { background: var(--surface); }
@media (max-width: 640px) {
  .session { display: none; }
}
</style>
