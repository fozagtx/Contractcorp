<script setup lang="ts">
const cop = useContractCop()

const contradictionsByClause = computed(() => {
  const map = new Map<string, { count: number; spans: string[] }>()
  for (const e of cop.events.value) {
    if (e.verdict !== 'contradiction' || !e.clause) continue
    const entry = map.get(e.clause.clause_id) ?? { count: 0, spans: [] }
    entry.count++
    const span = e.spans?.clause
    if (span && !entry.spans.includes(span)) entry.spans.push(span)
    map.set(e.clause.clause_id, entry)
  }
  return map
})

function clauseHtml(text: string, clauseId: string) {
  const spans = contradictionsByClause.value.get(clauseId)?.spans ?? []
  return markSpans(text, spans, 'm-signed')
}

// upload flow
interface UpFile { file: File; kind: 'contract' | 'policy' }
const uploads = ref<UpFile[]>([])
const name = ref('')
const extracting = ref(false)
const extractError = ref('')
const preview = ref<{ clauses: any[]; rules: any[]; dropped: number } | null>(null)
const saved = ref<{ zetaris_rows: number | null; sql: string | null } | null>(null)
const saving = ref(false)
const dragging = ref(false)
const confirmDelete = ref<string | null>(null)
const confirmEl = ref<HTMLElement | null>(null)
const showAdd = ref(false)

onMounted(async () => {
})

function saveKey() {
}

function addFiles(list: FileList | null) {
  for (const f of list ?? []) {
    uploads.value.push({
      file: f,
      kind: /policy/i.test(f.name) ? 'policy' : 'contract',
    })
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false
  addFiles(e.dataTransfer?.files ?? null)
}

async function extract() {
  if (!uploads.value.length || extracting.value) return
  extracting.value = true
  extractError.value = ''
  const fd = new FormData()
  for (const u of uploads.value) {
    fd.append('files', u.file)
    fd.append('kinds', u.kind)
  }
  try {
    preview.value = await $fetch('/api/contracts/extract', { method: 'POST', body: fd })
  } catch (err: any) {
    extractError.value = err?.data?.detail || String(err)
  } finally {
    extracting.value = false
  }
}

function removeClause(i: number) { preview.value?.clauses.splice(i, 1) }
function removeRule(i: number) { preview.value?.rules.splice(i, 1) }

async function save() {
  if (!preview.value || !name.value.trim() || saving.value) return
  saving.value = true
  extractError.value = ''
  try {
    const r = await $fetch<{ contract_id: string; zetaris_rows: number | null; sql: string | null }>(
      '/api/contracts',
      {
        method: 'POST',
        body: { name: name.value.trim(), clauses: preview.value.clauses, rules: preview.value.rules },
      },
    )
    saved.value = r
    nextTick(() => confirmEl.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }))
    preview.value = null
    uploads.value = []
    await cop.loadContracts()
    cop.setContract(r.contract_id)
  } catch (err: any) {
    extractError.value = err?.data?.detail || String(err)
  } finally {
    saving.value = false
  }
}

async function remove(id: string) {
  if (confirmDelete.value !== id) {
    confirmDelete.value = id
    return
  }
  confirmDelete.value = null
  try {
    await $fetch(`/api/contracts/${id}`, {
      method: 'DELETE',
    })
    await cop.loadContracts()
  } catch (err: any) {
    extractError.value = err?.data?.detail || String(err)
  }
}
</script>

<template>
  <div class="wrap">
    <template v-if="!cop.contracts.value.length">
      <h1>Start with <em>your</em> contract.</h1>
      <p class="sub">
        Upload the signed agreement and your sales policy. ContractCop extracts
        the clauses, you review them, and they are served through Zetaris for
        every call.
      </p>
    </template>
    <template v-else>
      <h1>The <em>signed</em> contract.</h1>
      <p class="sub">Clauses and policies, served live from Zetaris.</p>
      <select
        class="cpicker mono"
        :value="cop.activeContractId.value"
        @change="cop.setContract(($event.target as HTMLSelectElement).value)"
      >
        <option v-for="c in cop.contracts.value" :key="c.contract_id" :value="c.contract_id">
          {{ c.name }}
        </option>
      </select>
    </template>

    <!-- saved confirmation -->
    <div v-if="saved" ref="confirmEl" class="card confirm">
      <p class="ctitle">Served through Zetaris</p>
      <p class="mono dim" v-if="saved.zetaris_rows != null">
        {{ saved.zetaris_rows }} rows in contractcop.contract_flat
      </p>
      <pre v-if="saved.sql" class="mono">{{ saved.sql }}</pre>
      <NuxtLink to="/transcript" class="go link">Next: check a call</NuxtLink>
    </div>

    <!-- clause cards when a contract exists -->
    <template v-if="cop.contracts.value.length">
      <section class="clauses" aria-live="polite">
        <article v-for="c in cop.clauses.value" :key="c.clause_id" class="clause card">
          <header>
            <span class="cid mono">Clause {{ c.clause_id }}</span>
            <h2>{{ c.section }}</h2>
            <span class="tp mono">{{ c.topic }}</span>
            <span v-if="contradictionsByClause.get(c.clause_id)" class="nc mono">
              {{ contradictionsByClause.get(c.clause_id)!.count }} contradictions this call
            </span>
          </header>
          <p class="ctext" v-html="clauseHtml(c.text, c.clause_id)"></p>
          <div v-if="c.policy_id" class="cpol">
            <span class="label">Policy {{ c.policy_id }}</span>
            <p class="rule">{{ c.policy_rule }}</p>
          </div>
        </article>
      </section>
      <div class="row2">
        <button type="button" class="ghost" @click="preview = null; saved = null; uploads = [] ; showAdd = !showAdd">
          Add another contract
        </button>
        <button type="button" class="ghost danger" @click="remove(cop.activeContractId.value)">
          {{ confirmDelete === cop.activeContractId.value ? 'Confirm delete' : 'Delete' }}
        </button>
      </div>
      <p v-if="extractError" class="err">{{ extractError }}</p>
    </template>

    <!-- upload card -->
    <div v-if="!cop.contracts.value.length || showAdd" class="card upload">
      <label
        class="drop"
        :class="{ dragging }"
        @dragover.prevent="dragging = true"
        @dragleave="dragging = false"
        @drop.prevent="onDrop"
      >
        <input
          type="file"
          multiple
          accept=".txt,.md,.csv,.json,.pdf"
          class="sr"
          @change="addFiles(($event.target as HTMLInputElement).files); ($event.target as HTMLInputElement).value = ''"
        />
        <span>Drop contract and policy files here</span>
        <span class="mono dim">.txt .md .csv .json .pdf · up to 5 MB each</span>
      </label>

      <ul v-if="uploads.length" class="flist">
        <li v-for="(u, i) in uploads" :key="i">
          <span class="mono fname">{{ u.file.name }}</span>
          <button
            type="button"
            class="kind mono"
            @click="u.kind = u.kind === 'contract' ? 'policy' : 'contract'"
          >{{ u.kind }}</button>
          <button type="button" class="x" @click="uploads.splice(i, 1)">×</button>
        </li>
      </ul>

      <input v-model="name" class="name" placeholder="Contract name" aria-label="Contract name" />

      <button
        type="button"
        class="go"
        :disabled="!uploads.length || extracting"
        @click="extract"
      >{{ extracting ? 'Extracting…' : 'Extract clauses' }}</button>

      <p v-if="extractError" class="err">{{ extractError }}</p>

      <p class="dim" style="margin-top:10px">
        Need files to try?
        <a href="/api/samples/acme-master-services-agreement.md" download>Download the sample agreement</a>
        and
        <a href="/api/samples/acme-sales-policy.md" download>sample policy</a>.
      </p>
    </div>

    <!-- preview tables -->
    <div v-if="preview" class="card preview">
      <p class="ctitle">
        {{ preview.clauses.length }} clauses · {{ preview.rules.length }} rules
      </p>
      <p v-if="preview.dropped" class="dim">
        {{ preview.dropped }} rows dropped because the text was not found verbatim in the document
      </p>
      <table v-if="preview.clauses.length">
        <thead><tr><th>Clause</th><th>Section</th><th>Text</th><th>Topic</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(c, i) in preview.clauses" :key="i">
            <td><span class="cid mono">{{ c.clause_id }}</span></td>
            <td>{{ c.section }}</td>
            <td class="ct">{{ c.text }}</td>
            <td><span class="tp mono">{{ c.topic }}</span></td>
            <td><button type="button" class="x" @click="removeClause(i)">×</button></td>
          </tr>
        </tbody>
      </table>
      <table v-if="preview.rules.length">
        <thead><tr><th>Policy</th><th>Topic</th><th>Rule</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(r, i) in preview.rules" :key="i">
            <td><span class="cid mono">{{ r.policy_id }}</span></td>
            <td><span class="tp mono">{{ r.topic }}</span></td>
            <td class="ct">{{ r.rule }}</td>
            <td><button type="button" class="x" @click="removeRule(i)">×</button></td>
          </tr>
        </tbody>
      </table>
      <button type="button" class="go" :disabled="saving" @click="save">
        {{ saving ? 'Saving to Zetaris' : 'Save to Zetaris' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.wrap { max-width: 860px; margin: 0 auto; }
h1 { font-family: var(--serif); font-size: 64px; font-weight: 400; letter-spacing: -0.015em; line-height: 0.98; margin-bottom: 18px; }
h1 em { font-style: italic; }
.sub { font-size: 18px; line-height: 26px; color: var(--ink-2); margin-bottom: 28px; }
.cpicker { margin-bottom: 24px; font-size: 12.5px; color: var(--ink-2); border: 1px solid var(--line); border-radius: var(--pill); padding: 6px 12px; background: var(--card); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); padding: 22px 24px; margin-bottom: 18px; }
.ctitle { font-weight: 600; font-size: 16px; margin-bottom: 8px; }
.dim { color: var(--ink-2); font-size: 13px; }
.drop { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; min-height: 110px; border: 1px dashed var(--line-strong); border-radius: 10px; cursor: pointer; color: var(--ink-2); text-align: center; }
.drop:hover, .drop.dragging { background: #fbfaf7; border-color: var(--ink-3); }
.drop .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.flist { list-style: none; padding: 0; margin: 12px 0; }
.flist li { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line); }
.fname { flex: 1; font-size: 12.5px; }
.kind { border: 1px solid var(--line); border-radius: var(--pill); padding: 3px 10px; font-size: 11px; color: var(--ink-2); }
.kind:hover { background: var(--surface); }
.x { color: var(--ink-3); font-size: 16px; padding: 0 6px; }
.name { display: block; width: 100%; margin-top: 12px; border: 1px solid var(--line); border-radius: 8px; padding: 9px 12px; font-size: 14px; }
.name:focus { outline: none; border-color: var(--line-strong); }
.go { margin-top: 14px; min-height: 40px; padding: 0 20px; background: var(--accent); color: var(--accent-ink); font-weight: 600; font-size: 15px; border-radius: var(--pill); display: inline-flex; align-items: center; text-decoration: none; }
.go:disabled { opacity: 0.45; }
.err { color: var(--red); font-size: 13px; margin-top: 10px; }
a { color: var(--ink); }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 12px; }
th { text-align: left; font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-3); padding: 6px 10px 6px 0; border-bottom: 1px solid var(--line); }
td { padding: 9px 10px 9px 0; border-bottom: 1px solid var(--line); vertical-align: top; }
td.ct { font-size: 12.5px; color: var(--ink-2); }
.cid { font-size: 11.5px; color: var(--ink-2); border: 1px solid var(--line); border-radius: var(--pill); padding: 3px 9px; white-space: nowrap; }
.tp { font-size: 11px; color: var(--ink-3); background: #f1efe9; border-radius: var(--pill); padding: 3px 9px; white-space: nowrap; }
.clauses { display: flex; flex-direction: column; gap: 18px; }
.clause header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
h2 { font-size: 18px; font-weight: 600; flex: 1; }
.nc { font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; color: var(--red); background: #fdeceb; border-radius: var(--pill); padding: 4px 10px; }
.ctext { margin-top: 14px; font-size: 16px; line-height: 26px; }
.cpol { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--line); }
.cpol .label { display: block; margin-bottom: 4px; }
.rule { color: var(--ink-2); font-size: 14px; }
.confirm pre { background: #f3f1ec; border-radius: 8px; padding: 12px 14px; overflow-x: auto; font-size: 12px; margin: 8px 0; }
.row2 { display: flex; gap: 10px; margin-top: 6px; }
.ghost { min-height: 40px; padding: 0 16px; border: 1px solid var(--line); border-radius: var(--pill); font-size: 14px; font-weight: 500; }
.ghost:hover { background: #efece6; }
.ghost.danger { color: var(--red); }
@media (max-width: 900px) { h1 { font-size: 44px; } }
</style>
