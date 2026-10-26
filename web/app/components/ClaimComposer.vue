<script setup lang="ts">
const props = defineProps<{
  checked: number
  contradictions: number
  session: string
  busy: boolean
}>()

const emit = defineEmits<{ submit: [text: string] }>()

const draft = ref('')
const ta = ref<HTMLTextAreaElement | null>(null)

function submit() {
  const text = draft.value.trim()
  if (!text || props.busy) return
  emit('submit', text)
  draft.value = ''
  nextTick(() => {
    autosize()
    ta.value?.focus()
  })
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}

function autosize() {
  const el = ta.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

defineExpose({
  focus() {
    ta.value?.focus()
  },
  fill(text: string) {
    draft.value = text
    nextTick(() => {
      autosize()
      ta.value?.focus()
    })
  },
})
</script>

<template>
  <div class="composer">
    <div class="group">
      <textarea
        ref="ta"
        v-model="draft"
        rows="1"
        placeholder="What did the salesperson say?"
        aria-label="What the salesperson said"
        @keydown="onKeydown"
        @input="autosize"
      ></textarea>
      <button type="button" class="go" :disabled="busy || !draft.trim()" @click="submit">
        Check
      </button>
    </div>
    <p class="meta mono">
      {{ checked }} checked · {{ contradictions }} contradictions · session {{ session || 'new' }}
    </p>
  </div>
</template>

<style scoped>
.group {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 52px;
  padding: 6px 6px 6px 20px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--pill);
  box-shadow: var(--shadow);
}
.group:focus-within { border-color: var(--line-strong); }
textarea {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  font-size: 16px;
  padding: 8px 0;
  resize: none;
  max-height: 140px;
  min-height: 38px;
}
textarea:focus { outline: none; }
textarea::placeholder { color: var(--ink-3); }
.go {
  flex: none;
  min-height: 40px;
  padding: 0 20px;
  background: var(--accent);
  color: var(--accent-ink);
  font-weight: 600;
  font-size: 15px;
  border-radius: var(--pill);
  transition: filter 0.15s;
}
.go:hover:not(:disabled) { filter: brightness(0.94); }
.go:disabled { opacity: 0.45; cursor: default; }
.meta { margin-top: 14px; color: var(--ink-3); font-size: 12px; }
</style>
