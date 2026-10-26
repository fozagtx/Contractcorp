# ContractCop

Compliance guardian for sales calls. Paste what the salesperson said on the call, or upload the call transcript, and every claim is checked against the signed contract. Each verdict cites the clause text, the policy rule, the SQL that fetched them, and the model that judged.

<p>
  <a href="https://www.zetaris.com"><img src="assets/sponsors/zetaris.svg" alt="Zetaris" height="36"></a>&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://meterless.ai"><img src="assets/sponsors/meterless.svg" alt="Meterless" height="36" valign="middle"> <b>Meterless Nightshift</b></a>&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://build.nvidia.com"><img src="assets/sponsors/nvidia.svg" alt="NVIDIA" height="30"></a>
</p>

Data layer by Zetaris, AI provider and H-Mem engine by Meterless Nightshift, model NVIDIA Nemotron.

## Features

- Claim check in one line: type a sentence, get `contradiction`, `consistent`, `unclear` or `unrelated`
- Transcript mode: upload `.txt`, `.md`, `.vtt`, `.srt`, `.csv` or paste the call; timestamps and speaker labels are parsed, salesperson-side lines are checked one by one with progress
- Evidence on every alert: verbatim clause from Zetaris, policy rule, reason, SQL, model id, per-hop latency
- H-Mem memory: repeated or reworded claims are flagged with the earlier claim, within the call and across calls (persists in SQLite)
- End-of-call report: timeline of every claim and verdict for the session
- Safety rules: clause text is never written by the model; a contradiction needs a clause id the judge actually named; any provider, parse or network error resolves to `unclear`

## How it works

```
salesperson line
  -> route (Nemotron): pick a topic or mark it unrelated
  -> Zetaris: one cross-source JOIN, contract clauses + sales policy
  -> verdict (Nemotron): strict JSON with clause_id and reason, plus H-Mem memories
  -> alert: clause text from Zetaris, policy, reason, memory refs, SQL, model, timings
```

| Layer | Where |
|---|---|
| Data: Zetaris | `agent/zetaris.py`, live REST queries; contract and policy registered as two REST tables and joined in one statement |
| Build: Meterless engine | `agent/memory.py`, H-Mem persistent claim memory with word-overlap recall |
| Power: Nemotron via Nightshift | `agent/llm.py`, OpenAI-compatible client on the Nightshift Runtime, model `nvidia/nemotron-3.5-lightning-30b-a3b` |

## Prerequisites

- Python 3.12+ and a virtualenv with `pip install -r requirements.txt`
- Node 20+ and `pnpm`
- Zetaris running locally (REST on `localhost:8888`) with an API key
- Meterless Nightshift running locally with the NVIDIA provider connected (Runtime on `127.0.0.1:8088`)

Environment setup is documented step by step in [setup.md](setup.md).

## Getting started

```bash
cp .env.example .env          # fill in the Zetaris key and the Nightshift token
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python smoke_test.py          # Zetaris + Nemotron reachable

.venv/bin/uvicorn agent.server:app --port 8600   # agent API
cd web && pnpm install && pnpm dev               # UI on http://localhost:3100
```

For a single-port build: `cd web && pnpm generate`, then the agent on `http://localhost:8600` serves the UI.

### Run without Zetaris or Nightshift

```bash
SAMPLE_MODE=true .venv/bin/uvicorn agent.server:app --port 8600
```

Sample mode serves the contract clauses and policy rules from the local
fixtures in `agent/data/` instead of Zetaris (the SQL on each card is the real
statement, marked as fixture-served). When Nightshift is unreachable the
verdicts come from recorded model runs in `agent/data/sample_verdicts.json`;
those cards show `recorded (sample mode)` as the model, and a claim with no
recording resolves to `unclear`.

## Usage

Sample inputs and outputs (captured from live runs):

| Claim | Verdict | Clause | Reason | Model | Total |
|---|---|---|---|---|---|
| We will give you the 10 percent automatic discount, no approval needed. | contradiction | 3.1, Fees and Discounts | Claim states 10% discount is automatic and needs no approval, but clause 3.1 requires written VP approval for any discount above 10%. | nvidia/nemotron-3.5-lightning-30b-a3b | 4.1s |
| On the Standard Plan, support is 9:00 to 17:00, Monday through Friday. | consistent | 4.2, Support | The claim matches the hours specified in clause 4.2. | nvidia/nemotron-3.5-lightning-30b-a3b | 2.2s |
| You will have 24/7 support on the Standard Plan, guaranteed. | contradiction | 4.2, Support | CL4.2 limits Standard Plan support to 9:00 to 17:00, Monday through Friday, excluding public holidays. | nvidia/nemotron-3.5-lightning-30b-a3b | 4.0s |

API, if you want to skip the UI:

```bash
curl -s localhost:8600/api/claim -H 'content-type: application/json' \
  -d '{"session":"demo","text":"We will honor a 99.99 percent uptime guarantee on Standard."}'
curl -s localhost:8600/api/transcript -H 'content-type: application/json' -d '{"text":"<transcript>"}'
curl -s 'localhost:8600/api/report?session=demo'
curl -s localhost:8600/api/health
```

## Tests

```bash
.venv/bin/python -m pytest agent/tests -q                 # unit tests, no backends needed
.venv/bin/python -m pytest agent/tests/test_zetaris.py -q # live: needs Zetaris + Nightshift
```

Every check writes a one-line JSON trace to `agent/logs/trace.log` with
topic, clause, verdict, model and per-hop timings.

Measured on the labeled fixture (`agent/tests/labeled_claims.json`): 5/5 contradictions caught with the right clause id, 3/3 consistent claims with zero false accusations, 2/2 unrelated lines ignored, 10/12 strict overall. Median latency 2.7 to 2.9 s per claim with Nemotron reasoning disabled.

## Repo layout

```
agent/            Python agent and FastAPI API (:8600)
  claim_check.py  route -> Zetaris -> verdict loop and safety rules
  llm.py          Nemotron over the Nightshift Runtime
  zetaris.py      run_sql and the cross-source clause JOIN
  memory.py       H-Mem persistent claim memory
  transcript.py   transcript parser
  server.py       /api/claim /api/transcript /api/clauses /api/report /api/health
  data/           demo contract and policy (served to Zetaris from a public gist)
  tests/
web/              Nuxt 4 UI (:3100 in dev)
setup.md          environment runbook
smoke_test.py     three-layer smoke test
```

## Troubleshooting

- `unclear` on every claim: Nightshift is not running or the Runtime token in `.env` is wrong. `curl -s 127.0.0.1:8088/v1/models` should list `nvidia/nemotron-3.5-lightning-30b-a3b`.
- Clause rail empty: Zetaris is down or the API key is wrong. `curl -s localhost:8600/api/health` should return `{"zetaris":"ok"}`.
- Port 3000 is used by Zetaris, which is why the UI runs on 3100.
