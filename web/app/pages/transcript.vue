<script setup lang="ts">
const cop = useContractCop()

const text = ref('')
const info = ref('')
const fileError = ref('')
const parsing = ref(false)
const parsed = ref<string[] | null>(null)
const selected = ref<boolean[]>([])
const dragging = ref(false)
const running = ref(false)

const ACCEPT = ['.txt', '.md', '.vtt', '.srt', '.csv']
const MAX = 1024 * 1024

const chosen = computed(() =>
  (parsed.value ?? []).filter((_, i) => selected.value[i]),
)

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
    const lines = await cop.parseTranscript(text.value)
    if (!lines.length) {
      info.value = 'No rep lines found in that transcript.'
      parsed.value = null
      return
    }
    parsed.value = lines
    selected.value = lines.map(() => true)
  } catch (err) {
    fileError.value =
      'Parse failed: ' + (err instanceof Error ? err.message : String(err))
  } finally {
    parsing.value = false
  }
}

async function run() {
  const lines = chosen.value
  if (!lines.length) return
  running.value = true
  parsed.value = null
  text.value = ''
  info.value = ''
  await cop.runTranscript(lines)
  running.value = false
}
</script>

<template>
  <div>
    <h1>Check a whole call.</h1>
    <p class="sub">
      Drop a transcript file or paste it. Rep lines are checked against the
      contract one by one.
    </p>

    <div class="inputs">
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
        <span>Drop a .txt .md .vtt .srt or .csv file</span>
        <span class="mono dim">or click to browse · up to 1 MB</span>
      </label>
      <textarea
        v-model="text"
        rows="8"
        placeholder="Paste the transcript here"
        aria-label="Paste the transcript here"
      ></textarea>
    </div>
    <p v-if="fileError" class="err">{{ fileError }}</p>
    <p v-if="info" class="info mono">{{ info }}</p>

    <template v-if="parsed">
      <p class="info mono">
        {{ parsed.length }} rep lines found · {{ chosen.length }} selected
      </p>
      <ul class="preview">
        <li v-for="(l, i) in parsed" :key="i">
          <label>
            <input v-model="selected[i]" type="checkbox" />
            <span>{{ l }}</span>
          </label>
        </li>
      </ul>
    </template>

    <div class="drow">
      <button
        v-if="!parsed"
        type="button"
        class="go"
        :disabled="parsing || running"
        @click="parse"
      >
        {{ parsing ? 'Parsing…' : 'Parse' }}
      </button>
      <button
        v-else
        type="button"
        class="go"
        :disabled="!chosen.length || running"
        @click="run"
      >
        Check {{ chosen.length }} lines
      </button>
    </div>

    <section class="feed" aria-live="polite">
      <PendingRow v-if="cop.pending.value" :pending="cop.pending.value" />
      <ClaimRow v-for="(e, i) in cop.events.value" :key="i" :e="e" />
    </section>
  </div>
</template>

<style scoped>
h1 {
  font-size: 56px;
  font-weight: 300;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 16px;
}
.sub {
  color: var(--ink-2);
  font-weight: 300;
  margin-bottom: 32px;
  max-width: 560px;
}
.inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 140px;
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--ink-2);
  font-weight: 300;
  text-align: center;
  padding: 16px;
  transition: background 0.15s, border-color 0.15s;
}
.drop:hover, .drop.dragging { background: var(--surface); border-color: var(--ink-2); }
.drop .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.dim { color: var(--ink-2); }
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
.err { color: var(--red); font-size: 13px; margin-top: 10px; }
.info { color: var(--ink-2); margin-top: 12px; }
.preview {
  margin-top: 10px;
  list-style: none;
  padding: 0;
  color: var(--ink-2);
  font-weight: 300;
  font-size: 13.5px;
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fff;
}
.preview li { border-bottom: 1px solid var(--line); }
.preview li:last-child { border-bottom: 0; }
.preview label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  min-height: 40px;
}
.preview input[type='checkbox'] {
  width: 16px;
  height: 16px;
  margin-top: 3px;
  accent-color: var(--ink);
  flex: none;
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
.feed {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
@media (max-width: 900px) {
  h1 { font-size: 40px; }
  .inputs { grid-template-columns: 1fr; }
}
</style>
