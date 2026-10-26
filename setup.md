# Open Agent Hackathon 2026, Workspace Setup

Runbook for this workspace: `~/Desktop/openagent`
Distilled from the official Participant Setup Guide (PDF, last updated 21 October 2026).
Work top to bottom. Each phase ends with a **Done when** gate, do not move on until it passes.

---

## 0. The three layers and the rules

| Layer | Tool | Requirement |
|---|---|---|
| DATA | **Zetaris**, internal data, runs in Docker (headline sponsor) | Must use |
| BUILD | **Cursor** (recommended, not required) + **1+ Meterless Engine** in working code | Engine required |
| POWER | **Meterless Nightshift** as primary AI provider; **NVIDIA Nemotron** via Nightshift | Must use |

**Eligibility:** Zetaris and Meterless must be running on your machine.

**The one rule:** your coding tool's own models (Composer / Grok, on Cursor credit) pay while
you code. The Nemotron route (Meterless Nightshift, or NVIDIA's free API) is used only when
your product runs. Never put the Meterless Runtime token or NVIDIA key into Cursor's
model-provider settings, the NVIDIA key goes in Nightshift's Providers tab, and the
Nightshift URL + API key go into your app.

**Event tracks:** *Solving Fragmented Intelligence* and *The Agent That Can Explain Why* —
agents that work across scattered sources and back answers with evidence. Grounding every
answer in Zetaris-first data fits both tracks.

**NVIDIA Nemotron Award (DGX Spark):** power at least one working feature with a Nemotron
model through Meterless Nightshift. Judging: technical depth, usefulness, polish. Simply
listing Nemotron as an available model does not count, show what it actually does.

---

## 1. This machine (audited 25 Oct 2026)

| Requirement | State | Action |
|---|---|---|
| RAM >= 16 GB | 16 GB (Apple M5) | OK, give Docker 8 GB / 4 CPUs |
| Disk >= 15 GB free | ~124 GB free | OK |
| Docker >= v25 | 29.2.1, Compose v5.0.2 | OK |
| Python 3 | 3.14.7 | OK |
| Git | 2.53.0 | OK |
| Cursor | Not installed | Phase B |
| Nightshift | Not installed | Phase C |
| Zetaris | Not installed | Phase A |

Apple Silicon specifics:

- Zetaris images are built for Intel/AMD → enable **Use Rosetta** in Docker Desktop
  settings, and expect a slower first start (30–45 min total).
- Nightshift: download the **Mac M5+** edition (for Tahoe, M5–M6). This machine is
  macOS 26.7.1 on an M5.

---

## 2. Order of operations

1. **Start Phase A (Zetaris) first**, it downloads ~4 GB of container images and takes
   30–45 min. Register and kick off the install, then do B and C while it runs.
2. Phase B (Cursor) and Phase C (Nightshift + NVIDIA) take minutes each.
3. Phase D (scaffold) is already done in this workspace, see below.
4. Phase E (verification), run at least two days before kickoff.

---

## 3. Workspace layout

```
~/Desktop/openagent/
├── setup.md               # this runbook
├── .env                   # your secrets, create from .env.example, gitignored
├── .env.example           # template listing every setting you need
├── .gitignore             # keeps .env and installs out of git
├── smoke_test.py          # the all-in-one Data+Power check (Phase E)
├── .venv/                 # Python venv with openai, python-dotenv, requests
├── prompts/               # optional: saved Meterless prompt-library files
├── agent/                 # build during the event (see Phase D scaffold prompt)
├── getting-started/       # Zetaris recipes repo (clone in A8), reference only
├── zetaris-platform/      # Zetaris Docker install (unzip in A3), gitignored
└── GenAI Works Hackathon.pdf  # the source guide (gitignored)
```

Three secrets to collect along the way, all end up in `.env` (never in git):

1. Zetaris password (you set it yourself in A4)
2. Zetaris API key (created in the web UI in A9)
3. Meterless / Nightshift API key (from Nightshift's Console in C5)

---

## Phase A, DATA: Zetaris

### A1. Register and download (browser, ~5 min)

1. Register at <https://cloud.enterprise.zetaris.com/register>.
2. Open the **Run locally** page: <https://cloud.enterprise.zetaris.com/dashboard/download>.
3. Download `zetaris-platform.zip`.
4. Copy the **registry sign-in command** shown on that page (you need it in A3).
   If that page shows a different sign-in command than below, use theirs.

Full instructions: <https://github.com/zetaris/getting-started/blob/main/README.md>

### A2. Prepare Docker (GUI, ~2 min)

1. Open Docker Desktop → Settings → Resources: give Docker **8 GB memory** and **4 CPUs**
   (preflight fails below 6 GB). Disk: at least 15 GB free, you have ~124 GB.
2. Settings → General (or Rosetta section): enable **Use Rosetta** for x86/amd64
   emulation on Apple Silicon.
3. Apply and restart Docker, then confirm:

```bash
docker version
docker compose version
```

### A3. Unpack, sign in to the registry, run preflight

```bash
cd ~/Desktop/openagent
unzip zetaris-platform.zip          # put the downloaded zip here first
cd zetaris-platform
docker login zetarishackathon.azurecr.io   # paste the credentials from the Run locally page
./preflight.sh
```

`preflight.sh` checks: Docker, memory, disk, registry sign-in. Fix every failed check
before continuing. **Run all remaining Zetaris commands from this `zetaris-platform` folder.**

### A4. Set your administrator account (before the first start)

Edit `.env` inside `zetaris-platform`, keep every supplied value, set these three:

| Setting | What to put |
|---|---|
| `ZETARIS_ADMIN_EMAIL` | The email you'll sign in with |
| `ZETARIS_ADMIN_PASSWORD` | >= 8 chars with a lowercase letter, an uppercase letter, a digit and one of `$ @ ! % * ? &` (other punctuation is rejected) |
| `ZETARIS_ADMIN_ORG` | Your organisation / team name |

Confirm these laptop-tested values are set (they should be the defaults):

| Setting | Value |
|---|---|
| `ZSPARK_DRIVER_MEM` | `2g` |
| `ZSPARK_DRIVER_CORES` | `2` |
| `ZSPARK_MASTER_URL` | `local[2]` |
| `ZETARIS_API_MAX_HEAP` | `1g` |
| `UI_PORT` | `3000` |
| `ALLOWED_ORIGINS` and `GUI_URL` | `http://localhost:3000` |
| `COMPOSE_PROFILES` | empty |
| `ZETARIS_SEED_TPCH` | `true` (keeps the bundled sample data) |

Changing these after the first start does not reset an account that already exists.

Lock the file and validate it:

```bash
chmod 600 .env
docker compose config --quiet
```

This `.env` belongs to the Zetaris platform, never commit it or copy it into your project.

### A5. Download and start Zetaris (~30–45 min; ~4 GB)

```bash
docker compose pull      # 5–15 min
docker compose up -d    # first-time setup continues after this returns
docker compose ps --all
```

Ready when `postgres`, `driver`, `api`, `ui`, `ai-datasteward` show `running`, and the
one-time jobs `init` and `bootstrap` show `Exited (0)` (exit 0 = success).

Watch progress:

```bash
docker compose logs --tail=80 driver api bootstrap
```

### A6. Verify the install

```bash
./verify.sh
```

Expect **9/9 passed** (includes sign-in and a query through the web interface, the API
and the query engine). If checks fail while setup is still running, wait a minute and
run it again.

### A7. Sign in and run your first query

1. Open <http://localhost:3000>, sign in with the admin email/password from A4.
   If you kept a supplied password, change it immediately from the user menu.
2. Open the **SQL Editor** and run `SELECT 1 AS one;`, expect one row containing `1`.

### A8. Load your first dataset (PokeAPI recipe)

```bash
cd ~/Desktop/openagent
git clone https://github.com/zetaris/getting-started.git
```

1. Open `getting-started/open_data/rest_apis/sql/non_rate_limited/02_pokeapi_create.sql`.
2. In the SQL Editor, run these four statements **one complete statement at a time**,
   waiting for each to finish:
   - `CREATE LIGHTNING DATABASE POKEAPI_REST ...`
   - `CREATE SCHEMASTORE CONTAINER pokeapi;`
   - `CREATE LIGHTNING REST TABLE pikachu_facts ...`
   - `CREATE SCHEMASTORE VIEW pikachu_abilities_table ...`
3. Query the result:

```sql
SELECT pokemon_name, ability_name, is_hidden
FROM pokeapi.pikachu_abilities_table;
```

Expect 2 rows: `pikachu / static / false` and `pikachu / lightning-rod / true`.
Leave the rest of the file (types, stats, Charizard) for later. For more data see the
repo's recipe readiness guide, **skip the PUDL recipe** (Zetaris lists it as known to fail).

### A9. Connect Cursor and your app to Zetaris

Routes on a local install:

| Route | Address | Use it for |
|---|---|---|
| Web UI + SQL Editor | `http://localhost:3000` | Exploring data, registering sources, testing SQL |
| REST API | `http://localhost:8888/api/v1.0` | Your agent sending SQL, reading JSON |
| JDBC | `jdbc:zetaris:lightning@localhost:10000` | JDBC tools; needs Java 11+ and the driver file |

Do **not** use port 8889, it is internal to Zetaris. Full API reference:
<http://localhost:8888/redoc/index.html>.

1. In the Zetaris web UI, create an API key for your user and copy it immediately (it may
   be shown only once). **Create the key yourself, do not ask an AI agent to create or
   fetch it.**
2. Copy `.env.example` to `.env` in the project root and fill in the ZETARIS_* values:

```dotenv
ZETARIS_BASE_URL=http://localhost:3000
ZETARIS_REST_URL=http://localhost:8888/api/v1.0
ZETARIS_ORG_ID=1
ZETARIS_API_KEY=your-zetaris-api-key
ZETARIS_USERNAME=your-sign-in-email
ZETARIS_PASSWORD=your-password
```

`1` is the organisation ID on a local install. Username/password are only needed to
download the API's specification.

Every REST request is a `POST` to `{ZETARIS_REST_URL}/sql-editor/sqls/run` with headers
`Authorization: Bearer <API key>`, `X-Org-ID: <org id>` and `X-Request-ID: <fresh UUID>`
(a new UUID for every request).

First message to send Cursor once you have it (open the `getting-started` repo folder in
Cursor, put the same settings in its `.env.local`):

```text
Read AGENTS.md and follow it. Run python3 scripts/preflight.py and show me the
result. Then connect over REST to the instance configured in .env.local and
confirm with SELECT 1 and SHOW LIGHTNING DATABASES.
Goal: <for example: onboard pokeapi>
Dry-run before creating anything and wait for my go-ahead.
```

Stop / restart Zetaris (run from `zetaris-platform/`):

```bash
docker compose stop      # stop, keeping your data
docker compose start     # resume
```

`docker compose down -v` deletes everything including data and encryption keys, only
use it to start over.

**Done when:** `./verify.sh` passes 9/9, `SELECT 1 AS one;` works in the SQL Editor, the
Pikachu query returns two rows, and your Zetaris API key is saved in `.env`.

---

## Phase B, BUILD: Cursor + Meterless Engines

### B1. Set up your coding tool

Any AI coding agent that can edit files and run commands works (Cursor, Claude Code,
Windsurf, GitHub Copilot). Cursor is recommended and used in the workshop.

1. Download Cursor: <https://cursor.com/download>, install, sign in. Grok and Composer
   are included, paid from your Cursor credit, no API key of your own needed.
2. Open the Agent chat and pick a model: **Composer** for everyday speed, **Grok** for
   harder, longer-running work.
3. New to AI coding? Work through the short Cursor Learn lessons on tool calling and
   working with agents.
4. Sanity check: ask the agent to create and run a Python file that prints "hello".
   The file must appear and "hello" must print, with no API key entered.

### B2. Build with Meterless Engines (REQUIRED: 1+ engine in working code)

Engines are open-source building blocks. A **working integration is required**, merely
mentioning an engine in your submission, copying a prompt, or adding an unused
dependency does NOT satisfy the Build rule.

| Engine | What it adds | Demo you can show |
|---|---|---|
| H-Mem | Persistent memory and retrieval | Agent remembers a fact from an earlier session and uses it later |
| Markovian | Long-running tasks in bounded steps | Multi-step job completes with controlled context between steps |
| World Model | Shared state for agents, entities, events | Two agents update common project state without losing changes |
| Scout Intent | Understanding requests, routing actions, risk checks | App routes two different requests to different tools/workflows |

Workflow via the prompt library at <https://meterless.ai/engines.html>:

1. **Find a use case (IDEATE):** have a project idea? Use *IDEATE → Map it onto my
   product*. Still deciding? Use *IDEATE → Find my best use case* or the one-prompt
   starter. Copy the prompt into your agent chat and describe what you want to build.
   Let the agent recommend which engine belongs in your product.
2. **Implement (IMPLEMENT):** pick the prompt that fits, *Give my agent memory*
   (H-Mem), *Long tasks, flat context* (Markovian), *Keep parallel agents in sync*
   (World Model), *Route tools by intent* (Scout Intent), or *Scaffold a working agent*
   if starting from nothing (keep its engine wiring intact as you adapt it). Have the
   agent implement the engine in your actual application, connect it to a user-facing
   workflow, and run the tests/conformance checks the prompt describes.
3. **Improve and verify (COMBINE / HARDEN):** COMBINE prompts wire several engines
   together (e.g. H-Mem memory carried into a Markovian long-running task). HARDEN
   prompts add tests, guardrails, concurrency handling, privacy checks.
4. Show an **actual feature** powered by the engine, and keep a clear record of: which
   engine, where it appears in the code, and the test or live demo proving it works.

Meterless prompts and engine access are also in the HackOS resources tab.

Note: the **POWER → Add Meterless as a provider** prompt is for the Power section only —
on its own it does not meet the Build requirement.

### B3. Vibe coding workshop

Aired 20 October, 9:00 PM PST, watch the recording: <https://youtu.be/Qxg5xCJIAcQ>.
It builds a small agent from scratch using Cursor + the Meterless prompt library. Come
with all three layers set up so you can follow along on your own machine.

**Done when:** your coding tool's agent has created and run a file in your project;
you've used meterless.ai/engines.html to pick an engine and implementation path; at
least one engine is integrated into working code; you can demonstrate the feature (not
just describe it); and the engine's conformance suite / evaluation / reproducible feature
test passes with evidence you can show.

---

## Phase C, POWER: Meterless Nightshift + NVIDIA Nemotron

**The Power rule:** your app must support Meterless Nightshift as a **primary AI
provider**. Your app sends requests to Nightshift; Nightshift serves them with the local
or cloud models you configure.

### C1. Add Meterless to your app with the Power Prompt

1. Open <https://meterless.ai/engines.html>, select the **POWER** category, find
   **Add Meterless as a provider**, click Copy.
2. Paste the prompt into your coding assistant with your app's codebase open.
3. Ask it to implement the prompt: Meterless Runtime as a first-class, selectable
   provider and the **primary provider for your demo**, with settings for Meterless
   base URL, Meterless Runtime token and Meterless routing mode. Existing providers can
   stay available.
4. Have it run the prompt's connection, authorization, model-discovery and
   text-request checks.

The official Power Prompt specifies the OpenAI-compatible API, authentication, model
discovery and error states, use the live Engines page as your implementation contract.
The NVIDIA API key is configured inside Nightshift, never hard-coded into your app.

### C2. Download and install Nightshift

Nightshift is the Meterless AI Hotspot: it serves AI requests from your apps, manages
local models and connected cloud providers, and runs model lanes. For this challenge it
is the AI backend your product calls.

1. Visit <https://meterless.ai> and scroll to the bottom install cards.
2. Pick the **Mac M5+** edition (Tahoe, M5–M6) for this machine.
3. Enter your email at the access gate, open the confirmation email, complete verification.
4. Download the verified edition, install, launch. Complete any first-run prompts and
   leave Nightshift running while you test.

Use the installed edition with its Runtime/API hotspot, the free browser experience
does not necessarily expose the local Runtime your app needs.

### C3. Add NVIDIA in Nightshift's Providers tab

1. Open <https://build.nvidia.com/models>, sign in, and select a Nemotron model that
   offers an API endpoint (some are marked *Free Endpoint* for development/prototyping,
   subject to NVIDIA's limits and terms).
2. Generate or copy your **NVIDIA API key**.
3. In Nightshift: **Setup tab → Providers** (sub-menu) → select **NVIDIA** from the
   Cloud Providers list.
4. Paste the NVIDIA API key into the NVIDIA credential field and save.
5. Confirm NVIDIA is connected, this unlocks NVIDIA models in Nightshift's catalog.
   Refresh the model list if needed.

The NVIDIA key goes in **Providers**, not in the Console and not in your app's `.env`.

### C4. Configure your first model lanes

Click the **NIGHT** tab (top left of the main menu) → **LANES** in the left sidebar.
Use each lane's **Add** button to add a model (or load a fleet from the Fleets subtab).

| Lane | Suggested model | Job |
|---|---|---|
| Lane 1: fast worker | `nvidia/nemotron-3.5-lightning-30b-a3b` | Quick responses, tool use, first attempts |
| Lane 2: deep worker | `nvidia/nemotron-3.5-super-vl-120b-a12b` | Complex reasoning, planning, second opinions |
| Optional judge lane | A suitable available Nemotron or other supported model | Check outputs against your app's requirements |

These are examples, not entitlements, select the exact Nemotron names shown in your
NVIDIA catalog and Nightshift's model picker. You can start with just Lane 1. Local
models are optional; you don't need a local download to use NVIDIA-hosted endpoints.

**Make sure at least one active lane uses Nemotron.** Run a short test inside Nightshift
and confirm the response plus the selected provider and model.

### C5. Open the Console and connect your app

The **Console** (top right of Nightshift) holds your Runtime URL and API key, these are
Nightshift connection credentials, separate from the NVIDIA key.

1. Click Console, find the Runtime/API connection details.
2. Copy the **Nightshift URL** (base URL) and **Nightshift API key** (Runtime access token).
3. Paste them into your app's Meterless provider settings or private env vars:

```dotenv
METERLESS_BASE_URL=http://127.0.0.1:8088/v1
METERLESS_RUNTIME_TOKEN=<your-real-nightshift-runtime-token>
METERLESS_MODEL=meterless/auto
```

`http://127.0.0.1:8088/v1` is only an example for apps on the same computer, copy the
URL the Console actually shows. Use the real Runtime token, never the NVIDIA provider
key or a placeholder. `meterless/auto` is a routing mode, not an NVIDIA model ID, use
Runtime model discovery to pin an available `meterless/*` route.

**Runtime contract** (your coding assistant should implement this from the Power Prompt):
`Authorization: Bearer <token>`, the `meterless-app` header, `meterless-scope: user` for
chat, `GET /v1/models` for discovery, and OpenAI-compatible
`POST /v1/chat/completions`. A working `/healthz` response is not proof a real model
is connected.

### C6. Verify with a real request

Export the token in your shell first (a `.env` file does not export automatically), or
use your app's Test Connection action:

```bash
export METERLESS_RUNTIME_TOKEN="your-real-nightshift-runtime-token"
curl -sS http://127.0.0.1:8088/v1/chat/completions \
  -H "Authorization: Bearer $METERLESS_RUNTIME_TOKEN" \
  -H "Content-Type: application/json" \
  -H "meterless-app: hackathon-demo" \
  -H "meterless-scope: user" \
  -d '{
    "model": "meterless/auto",
    "messages": [{"role": "user", "content": "Reply with one sentence confirming this connection works."}]
  }'
```

Then test the real feature end to end: app → Meterless Runtime → active NVIDIA Nemotron
lane → result shown in your app. Check Nightshift's run details/logs/receipts to confirm
which model handled the request. `meterless/auto` may route to a non-NVIDIA model if
several are eligible, pin a Nemotron-backed lane (or demonstrate an explicit Nemotron
task) so your award evidence is unambiguous.

**Done when:** Meterless is a working primary AI provider in your app (not just a
README dependency); Nightshift is installed, running and reachable, and your real token
authenticates; NVIDIA credentials are saved in Providers and Nemotron models unlocked;
the Console supplies the URL + key your app uses; a Nemotron lane answers a real request
and a feature in your app produces an actual answer through Meterless; and for the
award, the underlying run visibly uses Nemotron.

### C7. What to show judges

In a short demo: (1) the finished app solving a useful problem, (2) its Meterless
provider connection, (3) one real request passing through Nightshift and returning a
result. You can show where the app connects to the Console-provided Runtime URL, hide
all keys and tokens.

---

## Phase D, Putting it together (scaffold)

The app pattern is a simple loop: Nemotron decides what to do → your code fetches the
data it asks for from Zetaris → the result goes back to Nemotron → repeat until it can
answer.

```
User asks → (2) app sends question to Nemotron via Meterless + tool descriptions
→ (3) Nemotron replies with a tool call, e.g. run_sql("SELECT ...")
→ (4) your code runs it against Zetaris and sends the rows back
→ (5) repeat 3–4 as needed → Nemotron writes the final, data-grounded answer
```

Build is where all this code is written, Cursor's Composer/Grok do the heavy lifting on
your Cursor credit.

**Scaffold with Cursor** (paste into Agent chat; attach a Meterless prompt file with `@`
if using the library). This creates the `agent/` folder in this workspace:

```text
Create a Python agent in the agent/ folder. In llm.py, use the openai package
with base URL MODEL_BASE_URL, key MODEL_API_KEY and model NEMOTRON_MODEL, all
read from .env. Give the agent one tool, run_sql, which sends one SQL
statement to Zetaris with a POST to ZETARIS_REST_URL + /sql-editor/sqls/run,
using ZETARIS_API_KEY as a bearer token plus X-Org-ID and a fresh UUID
X-Request-ID header, and returns the rows. Keep all secrets in .env and
explain each file.
```

Two patterns that put Zetaris at the center:

1. **Ground every answer in Zetaris**, the agent queries Zetaris first for facts, and
   uses web data only to add context. Traceable answers are what *The Agent That Can
   Explain Why* asks for.
2. **Bring outside data into Zetaris**, register a web API as a table (like the PokeAPI
   starter) so a public JSON API sits alongside your business data in one SQL query.

Files on your laptop: Zetaris cannot read a file sitting on your laptop, put it in
storage Zetaris can reach (such as an S3 bucket) before registering it.

Check the event rules for how much project code may be prepared in advance.

**Done when:** the project folder exists, `.env` holds all your secrets and settings,
and `.gitignore` keeps them out of version control.

---

## Phase E, Verify your setup (two days before kickoff)

### Check 1, DATA: Zetaris is running and answers queries

From `zetaris-platform/` run `./verify.sh`. Then in the SQL Editor at
<http://localhost:3000> run `SELECT 1 AS one;` and the Pikachu query from A8.

**PASS:** all nine `verify.sh` checks pass, `SELECT 1` returns one row, the Pikachu
query returns two rows.

### Check 2, BUILD: Cursor builds on its own models

In the Agent chat, select Composer or Grok and ask it to create and run a Python file
that prints "hello".

**PASS:** the file appears in your project and "hello" prints in the terminal, without
entering any API key.

### Check 3, DATA + POWER: the all-in-one smoke test

`smoke_test.py` (in this workspace) sends a real query to Zetaris through its REST API
and a real prompt to Nemotron through your chosen route. It needs in `.env`:

```dotenv
ZETARIS_REST_URL=http://localhost:8888/api/v1.0
ZETARIS_ORG_ID=1
ZETARIS_API_KEY=your-zetaris-api-key
MODEL_BASE_URL=provider-address-for-your-route
MODEL_API_KEY=your-meterless-or-nvapi-key
NEMOTRON_MODEL=the-nemotron-model-id-for-your-route
```

Run it (with Zetaris running) using this workspace's venv:

```bash
cd ~/Desktop/openagent
source .venv/bin/activate
python smoke_test.py
```

**PASS:** all three lines say PASS. Each FAIL line includes the error, see
Troubleshooting below.

- Option A (Nightshift route): `MODEL_BASE_URL` = the Console URL (e.g.
  `http://127.0.0.1:8088/v1`), `MODEL_API_KEY` = the Nightshift Runtime token (same
  value as `METERLESS_RUNTIME_TOKEN`), `NEMOTRON_MODEL` = a Nemotron model pinned in
  your lanes.
- Option B (NVIDIA direct route): `MODEL_BASE_URL` = the NVIDIA integrate API address
  (e.g. `https://integrate.api.nvidia.com/v1`), `MODEL_API_KEY` = your `nvapi-...` key
  from build.nvidia.com, `NEMOTRON_MODEL` = the exact model ID from the model page.

Take all three MODEL_* settings from the **same** route.

---

## Ready-for-kickoff checklist

- [x] 01 DATA, Zetaris Cloud account created and `zetaris-platform.zip` downloaded (26 Oct)
- [x] 02 DATA, `./verify.sh` passes 9/9 and the Pikachu query returns two rows (26 Oct)
- [x] 03 DATA, Zetaris API key created and saved in `.env` (26 Oct)
- [x] 04 BUILD, Cursor 3.27.14 installed (sign in + Check 2 hello-world still pending)
- [ ] 05 BUILD, Meterless prompt library downloaded (optional) and the workshop watched
- [x] 06 POWER, Nemotron route via Meterless Nightshift (Option A): Runtime URL,
      Runtime token and model ID `nvidia/nemotron-3.5-lightning-30b-a3b` in `.env`,
      all from the same route; chain verified end to end (26 Oct)
- [x] 07 ALL, `.env` listed in `.gitignore`, and `smoke_test.py` shows three PASS lines
      on the Nightshift route (26 Oct)

Setup notes (26 Oct): Nightshift Runtime token lives in
`~/Library/Application Support/ai.meterless.runtime/proxy-token` (same value as the
Console Runtime token). Nightshift's first run auto-downloads a ~10 GB local model
starter pack, cancelled; local models are optional and the judged lane is the
NVIDIA-hosted Nemotron. Admin password for `http://localhost:3000` is set in
`zetaris-platform/.env`.

## Phase D, built (26 Oct): ContractCop

The event project is built in `agent/` (see `agent/README.md` for the full
record, measured results and the demo script). Quick facts:

- **DATA**: demo contract + sales policy served from a public gist, registered
  as two Zetaris REST tables (`clauseguard.contract_flat`, `clauseguard.policy_flat`),
  JOINed in one query per claim.
- **BUILD**: Meterless **H-Mem** engine in working code (`agent/memory.py`),
  with 6 conformance tests in `agent/tests/test_memory.py`, persistent
  claim memory across calls.
- **POWER**: claim-check runs on `nvidia/nemotron-3.5-lightning-30b-a3b` through
  Meterless Nightshift (`127.0.0.1:8088/v1`), thinking disabled for ~2.8s
  verdicts, retry on transient empty responses.
- **Evidence**: 5/5 contradictions caught with correct clause IDs, 3/3 consistent
  claims, 0 false accusations, 10/12 strict fixture accuracy (the 2 "misses"
  are defensible verbal-commitment readings, see README). 11 unit + 4
  integration tests pass.
- **Run**: `.venv/bin/uvicorn agent.server:app --port 8600` → http://127.0.0.1:8600

---

## Troubleshooting

| Layer | Symptom | Likely cause | Fix |
|---|---|---|---|
| DATA | No platform bundle or registry credentials | Haven't registered at Zetaris Cloud | Register, download from the Run locally page; if download isn't enabled, contact Zetaris support or ask in Help Zetaris on HackOS |
| DATA | `./preflight.sh` reports failures | Docker not running / too little memory or disk / registry sign-in missing | Give Docker 8 GB + 4 CPUs, free 15 GB, rerun registry sign-in, rerun preflight |
| DATA | `docker compose pull` fails with denied/unauthorized | Registry didn't accept the sign-in | Rerun `docker login` with credentials from the Run locally page |
| DATA | `./verify.sh` fails right after starting | First-time setup still running | Wait for bootstrap `Exited (0)`, wait a minute, run again |
| DATA | Very slow first start on Mac | Apple Silicon runs Intel-built images under emulation | Use Rosetta in Docker Desktop; allow extra time |
| DATA | Sign-in fails | Wrong email/password; editing `.env` after first start doesn't reset an account | Use the details set before the first start |
| DATA | REST requests return 401 | Zetaris API key missing, wrong or expired | Create a new key in the web UI, update `.env` |
| DATA | REST requests return 400 | Wrong `X-Org-ID`, or `X-Request-ID` isn't a UUID | Org ID `1` on local; fresh UUID every request |
| DATA | "Object already exists" | That create statement already ran | Check the existing object, reuse it, move on |
| DATA | Table created but returns no rows | Zetaris server can't reach the source / wrong path | Check the source address, Zetaris itself (not just your laptop) must reach it |
| DATA | A file on your laptop won't query | Zetaris can't read laptop files | Put the file in reachable storage (e.g. S3 bucket), then register it |
| BUILD | Grok/Composer missing from Cursor, or requests stop | Cursor credit inactive or exhausted | Check plan/usage in Cursor settings; ask organisers about credit |
| BUILD | Charges on Meterless credit while coding | Meterless key ended up in Cursor's settings | Remove it from Cursor; code with Grok or Composer |
| POWER | Nemotron calls fail though each setting looks right | Settings mixed from two routes | Take all three settings from the same route |
| POWER | Smoke test says a MODEL_ setting is missing | Not in `.env`, or `.env` isn't in the folder you ran from | Add it; run the script from the project folder |
| POWER | Nemotron returns 401 or 403 | Key doesn't match the route in `MODEL_BASE_URL` | Copy the key again from Meterless or build.nvidia.com |
| POWER | Nemotron returns 404 / model not found | Model ID doesn't match the route's model list | Copy the exact model ID from Meterless or the NVIDIA model page |
| POWER | Credit or rate-limit errors | Meterless credit exhausted, or NVIDIA free-tier limit hit | Wait and retry, check limits, or switch routes (change all three settings) |
| ALL | `pip install` fails: externally-managed-environment | System Python blocks global installs | Use a venv, already created here: `.venv` |
| ALL | `python` isn't found | Python missing or not on PATH | Reinstall Python 3 (this machine: 3.14.7 is fine) |

Still stuck? Post in the **Help desk** channel on HackOS: <https://hackathon.genai.works/messages>.
Include your OS, the exact command, the full error, and the last step that worked.
Remove passwords, API keys and tokens before sharing anything. Ask early, not on the
morning of the event.

---

## Key links

| What | Where |
|---|---|
| Zetaris Cloud register | <https://cloud.enterprise.zetaris.com/register> |
| Zetaris Run locally / download page | <https://cloud.enterprise.zetaris.com/dashboard/download> |
| Zetaris getting-started docs | <https://zetaris.github.io/getting-started> |
| Zetaris getting-started repo | <https://github.com/zetaris/getting-started> |
| AWS fallback (if under 16 GB RAM) | zetaris.github.io/getting-started/docs/install/aws-free-tier-checklist.html |
| Cursor download | <https://cursor.com/download> |
| Meterless Engines + prompt library | <https://meterless.ai/engines.html> |
| Nightshift downloads | <https://meterless.ai> |
| NVIDIA model catalog + API keys | <https://build.nvidia.com/models> |
| Workshop recording (aired 20 Oct) | <https://youtu.be/Qxg5xCJIAcQ> |
| HackOS help desk | <https://hackathon.genai.works/messages> |
