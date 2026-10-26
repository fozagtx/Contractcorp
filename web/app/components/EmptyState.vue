<script setup lang="ts">
const emit = defineEmits<{ suggest: [text: string] }>()
const suggestion =
  'We will give you the 10 percent automatic discount, no approval needed.'
</script>

<template>
  <div class="empty">
    <p class="muted">No claims yet.</p>
    <button type="button" class="sugg" @click="emit('suggest', suggestion)">
      "{{ suggestion }}"
    </button>
  </div>
</template>

<style scoped>
.empty {
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  padding: 28px 18px;
  text-align: center;
}
.muted { color: var(--ink-2); font-weight: 400; }
.sugg {
  margin-top: 10px;
  color: var(--ink);
  font-weight: 400;
  min-height: 40px;
  padding: 4px 8px;
  border-radius: var(--radius);
}
.sugg:hover { background: var(--surface); text-decoration: underline; }
</style>
