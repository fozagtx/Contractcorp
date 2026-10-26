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
      info.value = 'No salesperson lines found in that transcript.'
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
  <div class="grid">
    <section class="side">
      <h1>Check a <em>whole</em> call.</h1>
      <p class="sub">
        Upload or paste the call transcript. Every sentence the salesperson said
        is checked against the contract, one by one.
      </p>

      <NuxtLink
        v-if="!cop.contracts.value.length"
        to="/contract"
        class="needcard"
      >Upload a contract first</NuxtLink>
      <template v-else>
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
        class="paste"
        rows="8"
        placeholder="Paste the transcript here"
        aria-label="Paste the transcript here"
      ></textarea>
      <p v-if="fileError" class="err">{{ fileError }}</p>
      <p v-if="info" class="info mono">{{ info }}</p>

      <button
        v-if="!parsed"
        type="button"
        class="go"
        :disabled="parsing || running"
        @click="parse"
      >
        {{ parsing ? 'Parsing…' : 'Parse' }}
      </button>

      <div v-if="parsed" class="lines">
        <p class="info mono">
          {{ parsed.length }} salesperson lines found · {{ chosen.length }} selected
        </p>
        <ul class="preview">
          <li v-for="(l, i) in parsed" :key="i">
            <label>
              <input v-model="selected[i]" type="checkbox" />
              <span>{{ l }}</span>
            </label>
          </li>
        </ul>
        <button
          type="button"
          class="go"
          :disabled="!chosen.length || running"
          @click="run"
        >
          Check {{ chosen.length }} lines
        </button>
      </div>
      </template>
    </section>
    <FeedCard />
  </div>
</template>

<style scoped>
.needcard {
  display: block;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 16px 18px;
  color: var(--ink-2);
  font-size: 14px;
  text-decoration: none;
}
.grid {
  display: grid;
  grid-template-columns: minmax(0, 440px) minmax(0, 1fr);
  gap: 56px;
  align-items: start;
}
h1 {
  font-family: var(--serif);
  font-size: 64px;
  font-weight: 400;
  letter-spacing: -0.015em;
  line-height: 0.98;
  margin-bottom: 18px;
}
h1 em { font-style: italic; }
.sub {
  font-size: 18px;
  line-height: 26px;
  color: var(--ink-2);
  margin-bottom: 30px;
}
.drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 120px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  background: var(--card);
  cursor: pointer;
  color: var(--ink-2);
  text-align: center;
  padding: 16px;
  transition: background 0.15s, border-color 0.15s;
}
.drop:hover, .drop.dragging { background: #fbfaf7; border-color: var(--ink-3); }
.drop .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.dim { color: var(--ink-3); font-size: 12px; }
.paste {
  margin-top: 14px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 14px 16px;
  font-size: 14px;
  resize: vertical;
}
.paste:focus { outline: none; border-color: var(--line-strong); }
.err { color: var(--red); font-size: 13px; margin-top: 10px; }
.info { color: var(--ink-3); margin-top: 12px; font-size: 12px; }
.go {
  margin-top: 16px;
  min-height: 40px;
  padding: 0 20px;
  background: var(--accent);
  color: var(--accent-ink);
  font-weight: 600;
  font-size: 15px;
  border-radius: var(--pill);
}
.go:disabled { opacity: 0.45; }
.lines { margin-top: 4px; }
.preview {
  margin-top: 10px;
  list-style: none;
  padding: 0;
  font-size: 13.5px;
  max-height: 260px;
  overflow-y: auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
}
.preview li { border-bottom: 1px solid var(--line); }
.preview li:last-child { border-bottom: 0; }
.preview label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 11px 14px;
  cursor: pointer;
  min-height: 40px;
  color: var(--ink-2);
}
.preview input[type='checkbox'] {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  accent-color: var(--accent);
  flex: none;
}
@media (max-width: 1024px) {
  .grid { grid-template-columns: 1fr; gap: 40px; }
}
@media (max-width: 900px) {
  h1 { font-size: 44px; }
}
</style>
