export type Verdict = 'contradiction' | 'consistent' | 'unclear' | 'unrelated'

export interface ClauseRef {
  clause_id: string
  section: string
  text: string
}

export interface PolicyRef {
  policy_id: string
  rule: string
}

export interface MemoryItem {
  claim: string
  verdict: Verdict
  clause_id?: string
  when?: string
  date?: string
}

export interface Hop {
  hop: string
  ms?: number
  detail?: string
}

export interface ClaimEvent {
  claim: string
  verdict: Verdict
  clause: ClauseRef | null
  policy: PolicyRef | null
  reason?: string
  memory?: { same_session: MemoryItem[]; earlier_calls: MemoryItem[] }
  hops?: Hop[]
  spans?: { claim: string | null; clause: string | null }
  sql?: string
  sql_ms?: number
  model?: string
  ms?: number
  error?: string
  open?: boolean
}

export interface PendingState {
  stage: 'routing' | 'zetaris' | 'judging'
  progress?: { done: number; total: number; line: string }
}

export interface RailClause {
  clause_id: string
  section: string
  text: string
  topic?: string
  policy_id: string
  policy_rule: string
}

export interface ReportEntry {
  ts: number
  verdict: Verdict
  claim: string
  clause_id?: string
}

export interface Report {
  session: string
  claims_total: number
  contradictions: number
  timeline: ReportEntry[]
}

const session = ref('')
const contracts = ref<{ contract_id: string; name: string; clauses?: number; rules?: number }[]>([])
const activeContractId = ref('')
const events = ref<ClaimEvent[]>([])
const pending = ref<PendingState | null>(null)
const clauses = ref<RailClause[]>([])
const health = ref<'ok' | 'bad' | 'unknown'>('unknown')
const railError = ref(false)

let stageTimer: ReturnType<typeof setInterval> | null = null

function makeSessionId() {
  return `call-${Date.now().toString(36)}`
}

function ensureSession() {
  if (!session.value) session.value = makeSessionId()
}

function startStageCycler() {
  stopStageCycler()
  const steps: PendingState['stage'][] = ['routing', 'zetaris', 'judging']
  let i = 0
  stageTimer = setInterval(() => {
    if (!pending.value) return stopStageCycler()
    i = (i + 1) % steps.length
    pending.value = { ...pending.value, stage: steps[i]! }
  }, 700)
}

function stopStageCycler() {
  if (stageTimer) {
    clearInterval(stageTimer)
    stageTimer = null
  }
}

function failureEvent(text: string, err: unknown): ClaimEvent {
  return {
    claim: text,
    verdict: 'unclear',
    clause: null,
    policy: null,
    reason: 'The check itself failed, so nothing can be concluded.',
    error: err instanceof Error ? err.message : String(err),
    open: false,
  }
}

export function useContractCop() {
  const checked = computed(() => events.value.length)
  const contradictions = computed(
    () => events.value.filter((e) => e.verdict === 'contradiction').length,
  )
  const counts = computed<Record<Verdict, number>>(() => {
    const c: Record<Verdict, number> = {
      contradiction: 0,
      consistent: 0,
      unclear: 0,
      unrelated: 0,
    }
    for (const e of events.value) c[e.verdict]++
    return c
  })

  async function checkClaim(text: string) {
    const claim = text.trim()
    if (!claim || !activeContractId.value) return
    ensureSession()
    pending.value = { stage: 'routing' }
    startStageCycler()
    try {
      const e = await $fetch<ClaimEvent>('/api/claim', {
        method: 'POST',
        body: { session: session.value, text: claim, contract_id: activeContractId.value },
      })
      e.open = e.verdict === 'contradiction'
      events.value.push(e)
    } catch (err) {
      events.value.push(failureEvent(claim, err))
    } finally {
      stopStageCycler()
      pending.value = null
    }
  }

  async function parseTranscript(text: string): Promise<string[]> {
    ensureSession()
    const d = await $fetch<{ lines: string[]; total: number }>('/api/transcript', {
      method: 'POST',
      body: { session: session.value, text },
    })
    return d.lines
  }

  async function runTranscript(lines: string[]) {
    ensureSession()
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]!
      pending.value = {
        stage: i === 0 ? 'routing' : 'judging',
        progress: { done: i + 1, total: lines.length, line },
      }
      try {
        const e = await $fetch<ClaimEvent>('/api/claim', {
          method: 'POST',
          body: { session: session.value, text: line, contract_id: activeContractId.value },
        })
        e.open = e.verdict === 'contradiction'
        events.value.push(e)
      } catch (err) {
        events.value.push(failureEvent(line, err))
      }
    }
    pending.value = null
  }

  async function loadClauses() {
    railError.value = false
    try {
      const d = await $fetch<{ clauses: RailClause[] }>('/api/clauses', {
        query: { contract_id: activeContractId.value || 'demo' },
      })
      clauses.value = d.clauses
    } catch {
      railError.value = true
    }
  }

  async function loadContracts() {
    try {
      const d = await $fetch<{ contracts: { contract_id: string; name: string }[] }>(
        '/api/contracts',
      )
      contracts.value = d.contracts
      const saved =
        typeof localStorage !== 'undefined'
          ? localStorage.getItem('cc_contract')
          : null
      const ids = new Set(contracts.value.map((c) => c.contract_id))
      activeContractId.value =
        saved && ids.has(saved) ? saved : (contracts.value[0]?.contract_id ?? '')
    } catch {
      contracts.value = []
      activeContractId.value = ''
    }
  }

  function setContract(id: string) {
    if (id === activeContractId.value) return
    activeContractId.value = id
    if (typeof localStorage !== 'undefined') localStorage.setItem('cc_contract', id)
    newSession()
    loadClauses()
  }

  async function loadHealth() {
    try {
      const d = await $fetch<{ zetaris: string }>('/api/health')
      health.value = d.zetaris === 'ok' ? 'ok' : 'bad'
    } catch {
      health.value = 'bad'
    }
  }

  async function loadReport(): Promise<Report | null> {
    ensureSession()
    try {
      return await $fetch<Report>('/api/report', {
        query: { session: session.value },
      })
    } catch {
      return null
    }
  }

  function newSession() {
    session.value = makeSessionId()
    events.value = []
    pending.value = null
  }

  return {
    contracts,
    activeContractId,
    setContract,
    loadContracts,
    session,
    events,
    pending,
    clauses,
    health,
    railError,
    checked,
    contradictions,
    counts,
    ensureSession,
    checkClaim,
    parseTranscript,
    runTranscript,
    loadClauses,
    loadHealth,
    loadReport,
    newSession,
  }
}
