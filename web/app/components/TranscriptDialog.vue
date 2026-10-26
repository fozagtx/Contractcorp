<script setup lang="ts">
const emit = defineEmits<{ run: [lines: string[]] }>()

const { parseTranscript } = useContractCop()

const dlg = ref<HTMLDialogElement | null>(null)
const text = ref('')
const info = ref('')
const fileError = ref('')
const parsing = ref(false)
const parsed = ref<string[] | null>(null)
const dragging = ref(false)

const ACCEPT = ['.txt', '.md', '.vtt', '.srt', '.csv']
const MAX = 1024 * 1024

function open() {
  parsed.value = null
  info.value = ''
  fileError.value = ''
  dlg.value?.showModal()
}

function close() {
  dlg.value?.close()
}

async function loadFile(f: File | undefined) {
  fileError.value = ''
  if (!f) return
  const ext = '.' + (f.name.split('.').pop() ?? '').toLowerCase()
  if (!ACCEPT.includes(ext)) {
    fileError.value = `Unsupported file type ${ext}. Use ${ACCEPT.join(' ')}.`
    return
  }
  if (f.size > MAX) {
    fileError.value = `File too large (${Math.ceil(f.size / 1024)} KB, 1 MB max).`
    return
  }
  text.value = await f.text()
  parsed.value = null
  info.value = `Loaded ${f.name} (${Math.ceil(f.size / 1024)} KB)`
}

function onFileInput(e: Event) {
  loadFile((e.target as HTMLInputElement).files?.[0])
}

function onDrop(e: DragEvent) {
  dragging.value = false
  loadFile(e.dataTransfer?.files?.[0])
}

async function parse() {
  if (!text.value.trim()) {
    info.value = 'Nothing to parse yet. Drop a file or paste the transcript.'
    return
  }
  parsing.value = true
  info.value = ''
  fileError.value = ''
  try {
    const lines = await parseTranscript(text.value)
    if (!lines.length) {
      info.value = 'No rep lines found in that transcript.'
      parsed.value = null
      return
    }
    parsed.value = lines
  } catch (err) {
    fileError.value = 'Parse failed: ' + (err instanceof Error ? err.message : String(err))
  } finally {
    parsing.value = false
  }
}

function run() {
  if (!parsed.value?.length) return
  emit('run', parsed.value)
  close()
  text.value = ''
  parsed.value = null
  info.value = ''
}

defineExpose({ open })
</script>

<template>
  <dialog ref="dlg" @close="dragging = false">
    <h3>Check a call transcript</h3>
    <p class="sub">
      Drop a file or paste the transcript. Rep lines are checked against the
      contract one by one.
    </p>

    <label
      class="drop"
      :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
    >
      <input
        type="file"
        accept=".txt,.md,.vtt,.srt,.csv,text/plain"
        class="sr"
        @change="onFileInput"
      />
      <span>Drop a .txt .md .vtt .srt or .csv file, or click to browse</span>
      <span class="mono dim">up to 1 MB</span>
    </label>
    <p v-if="fileError" class="err">{{ fileError }}</p>

    <label class="flabel mono" for="trtext">Or paste it here</label>
    <textarea id="trtext" v-model="text" rows="7"></textarea>

    <p v-if="info" class="info mono">{{ info }}</p>

    <template v-if="parsed">
      <p class="info mono">{{ parsed.length }} rep lines found</p>
      <ul class="preview">
        <li v-for="(l, i) in parsed" :key="i">{{ l }}</li>
      </ul>
    </template>

    <div class="drow">
      <button
        v-if="!parsed"
        type="button"
        class="go"
        :disabled="parsing"
        @click="parse"
      >
        {{ parsing ? 'Parsing…' : 'Parse' }}
      </button>
      <button v-else type="button" class="go" @click="run">
        Check {{ parsed.length }} lines
      </button>
      <button type="button" class="cancel" @click="close">Cancel</button>
    </div>
  </dialog>
</template>

<style scoped>
h3 { font-weight: 500; font-size: 17px; }
.sub { color: var(--ink-2); font-weight: 300; margin-top: 4px; }
.drop {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 88px;
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--ink-2);
  font-weight: 300;
  transition: background 0.15s, border-color 0.15s;
}
.drop:hover, .drop.dragging { background: var(--surface); border-color: var(--ink-2); }
.drop .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.dim { color: var(--ink-2); }
.flabel { display: block; color: var(--ink-2); margin-top: 16px; margin-bottom: 6px; }
textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fff;
  padding: 10px 12px;
  font-weight: 300;
  resize: vertical;
}
textarea:focus { outline: none; border-color: var(--ink); }
.err { color: var(--red); font-size: 13px; margin-top: 8px; }
.info { color: var(--ink-2); margin-top: 10px; }
.preview {
  margin-top: 8px;
  padding-left: 18px;
  color: var(--ink-2);
  font-weight: 300;
  font-size: 13.5px;
  max-height: 160px;
  overflow-y: auto;
}
.drow { margin-top: 18px; display: flex; gap: 10px; align-items: center; }
.go {
  height: 36px;
  padding: 0 14px;
  background: var(--accent);
  color: #1b1b16;
  font-weight: 500;
  font-size: 13.5px;
  border-radius: var(--radius);
}
.go:disabled { opacity: 0.5; }
.cancel {
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  font-size: 13.5px;
}
.cancel:hover { background: var(--surface); }
</style>
