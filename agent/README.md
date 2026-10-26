# ContractCop

A grounded compliance guardian for sales calls: the rep says something, and
ContractCop checks it against the signed contract stored in **Zetaris**,
judged by **NVIDIA Nemotron served through Meterless Nightshift**, with
persistent claim memory (**Meterless H-Mem engine**) so repeats get caught
with receipts.

Built for the Open Agent Hackathon 2026. Inspired by the live-voice
ClauseCatcher (sales-call compliance on AssemblyAI); this version is
text-first and re-grounded on the hackathon's three layers, with the
claim-check discipline kept: the words in every alert come from the
contract, never from the model.

## The loop

```
rep line (typed in the cockpit)
   │
   ├─ route (Nemotron): which topic? discounts | support | data_residency | termination | uptime | none
   │
   ├─ Zetaris (one cross-source JOIN query):
   │     contract clauses  ⋈  sales policy rules        ← two REST sources, one query
   │
   ├─ verdict (Nemotron): STRICT JSON — contradiction | consistent | unclear, clause_id, reason
   │     + H-Mem memories of earlier claims (this call and earlier calls)
   │
   └─ alert card: verbatim clause text (from Zetaris) + policy + reason
        + memory refs + the SQL + the model + per-hop latencies
```

Nothing the model writes ever reaches the alert text. The clause words are
fetched from Zetaris by clause_id. On any error — provider, parse, network —
the verdict is `unclear`, never an accusation.

## The three layers (hackathon requirements)

| Layer | Requirement | Where it lives |
|---|---|---|
| DATA | Zetaris must be used | `agent/zetaris.py` — every clause lookup is a live REST query; two sources (contract gist + policy gist) registered as Zetaris REST tables and JOINed in one statement (`clauseguard.contract_flat` ⋈ `clauseguard.policy_flat`) |
| BUILD | 1+ Meterless Engine in working code | **H-Mem** — `agent/memory.py`: persistent SQLite claim memory with word-overlap recall; conformance tests in `agent/tests/test_memory.py` |
| POWER | Nightshift primary provider, Nemotron via Nightshift | `agent/llm.py` — OpenAI-compatible client pointed at the Nightshift Runtime (`127.0.0.1:8088/v1`), model `nvidia/nemotron-3.5-lightning-30b-a3b`, headers `meterless-app` / `meterless-scope`; Nightshift receipts show which model served each request |

## Why H-Mem is load-bearing, not decorative

- **Within a call:** the rep repeats a contradicted commitment → the new
  alert carries the earlier claim with its timestamp and verdict
  ("earlier this call at 18:35 you said X — contradiction §3.1").
- **Across calls:** a later session recalls the same contradicted
  commitments from previous sessions — memory survives restarts
  (SQLite at `agent/memory.db`), which is exactly the persistence the
  engine exists for.
- Proof: `pytest agent/tests/test_memory.py` (6 conformance tests,
  including restart persistence) plus the live cross-session demo in the
  cockpit.

## Measured results (honest, from live runs)

- **Contradictions: 5/5 caught, each with the correct clause ID** (§3.1
  automatic discount, §4.2 24/7-on-Standard, §9.1 99.9%-on-Standard,
  §8.3 early-termination refund, §6.1 region move on demand). Reproduce:
  `pytest agent/tests/test_zetaris.py` (needs Zetaris + Nightshift up).
- **Consistent claims: 3/3, zero false accusations** (§4.2, §3.1, §8.3).
- **Unrelated lines: 2/2** correctly ignored (no clause lookup at all).
- **Fixture accuracy: 10/12 strict.** The two misses are the fixture's
  "unclear" labels: "we might be able to do something on the price" and
  "our uptime is really good, trust me" were judged contradictions citing
  §3.1 (verbal price commitments) and §9.1 (uptime commitments above
  target). Defensible readings — both clauses literally prohibit verbal
  commitments — reported as-is rather than tuned away.
- **Latency: median 2.7–2.9 s per claim** end to end (route hop + Zetaris
  JOIN + verdict hop), with Nemotron 3.5 run with thinking disabled and a
  retry on transient empty responses. With default reasoning the verdict
  hop alone was 19 s.
- Unit suite: 11/11 pass in 0.25 s (no backends needed). Integration suite:
  4/4 pass in ~40 s.

## Run it

```bash
# from ~/Desktop/openagent, with Zetaris up and Nightshift running
.venv/bin/uvicorn agent.server:app --port 8600
# open http://127.0.0.1:8600
```

The cockpit needs the workspace `.env` (Zetaris REST + API key + the
Nightshift route), all gitignored.

## Repo layout

```
agent/
├── llm.py           # Nemotron over the Nightshift Runtime (POWER)
├── zetaris.py       # run_sql + the cross-source clause JOIN (DATA)
├── memory.py        # H-Mem engine: persistent claim memory (BUILD)
├── claim_check.py   # the bounded two-hop claim-check loop + safety rules
├── server.py        # FastAPI: /api/claim, /api/clauses, /api/report, /api/health
├── cockpit/         # single-file text-first cockpit (transcript, alerts, rail, report)
├── tests/           # unit + integration + the labeled-claims accuracy fixture
└── data/            # contract + policy fixtures (also served via gist to Zetaris)
```

## Demo script (2 minutes)

1. Open the cockpit — the rail loads the five clauses straight from Zetaris.
2. Type: `And of course we will give you the 10 percent automatic discount
   on this deal, no paperwork needed.` → alert card: contradiction §3.1,
   verbatim clause, POL-01, the SQL that found it, model + latencies.
3. Type: `On the Standard Plan, support is available 9:00 to 17:00, Monday
   through Friday.` → consistent §4.2. (Errors never accuse: kill Nightshift
   mid-call and the next line is `unclear`, with the error shown.)
4. Type the discount line again, reworded → contradiction §3.1 **with an
   H-Mem memory ref to the earlier claim in the same call**.
5. Change the session id and repeat → the alert cites the earlier **call**.
6. End-of-call report → timeline of every claim and verdict.
7. (Optional, for the award) open Nightshift and show the run receipts: the
   checks were served by `nvidia/nemotron-3.5-lightning-30b-a3b`.

## Safety rules (kept from the claim-check discipline)

- Clause text is always literal, always from Zetaris, keyed by clause_id.
- The routed topic is whitelist-validated before it can touch SQL.
- A contradiction requires a clause_id the checker actually named.
- Errors resolve to `unclear`, never to an accusation.

## Sources

Demo contract and policy data live in `agent/data/` and are served to
Zetaris from a public gist, registered as two REST tables. Zetaris cannot
read laptop files, so the gist is the reachable storage for the demo data.
