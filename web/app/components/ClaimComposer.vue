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
    <div class="ask">
      <textarea
        ref="ta"
        v-model="draft"
        rows="1"
        placeholder="What did the rep just say?"
        aria-label="What the rep just said"
        @keydown="onKeydown"
        @input="autosize"
      ></textarea>
      <button type="button" class="go" :disabled="busy || !draft.trim()" @click="submit">
        Check <span class="hint mono">[⏎]</span>
      </button>
    </div>
    <p class="meta mono">
      {{ checked }} checked · {{ contradictions }} contradictions · session {{ session || 'new' }}
    </p>
  </div>
</template>

<style scoped>
.ask {
  display: flex;
  align-items: flex-end;
  gap: 14px;
}
textarea {
  flex: 1;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  color: var(--ink);
  font-size: 17px;
  font-weight: 400;
  padding: 8px 0;
  resize: none;
  max-height: 160px;
  min-height: 40px;
}
textarea:focus { outline: none; border-bottom-color: var(--ink); }
textarea::placeholder { color: var(--ink-2); }
.go {
  flex: none;
  height: 40px;
  padding: 0 16px;
  background: var(--accent);
  color: #1b1b16;
  font-weight: 500;
  font-size: 14px;
  border-radius: var(--radius);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: filter 0.15s;
}
.go:hover:not(:disabled) { filter: brightness(0.95); }
.go:disabled { opacity: 0.45; cursor: default; }
.hint { font-size: 11px; opacity: 0.7; }
.meta { margin-top: 14px; color: var(--ink-2); }
</style>
