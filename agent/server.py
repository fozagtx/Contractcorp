"""ContractCop server: FastAPI over the claim-check agent.

Run from the workspace root:
    .venv/bin/uvicorn agent.server:app --reload --port 8600

The UI is the Nuxt app in web/: `cd web && pnpm install && pnpm dev` for
development on http://localhost:3100, or `cd web && pnpm generate` and this
server will serve the static build at http://localhost:8600/.
"""
import logging
import os
import re
import secrets
import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import claim_check, extract, memory, store, transcript, zetaris

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIST = os.path.join(os.path.dirname(AGENT_DIR), "web", ".output", "public")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(message)s",
)

LOG_DIR = os.path.join(AGENT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.getLogger("contractcop.trace").addHandler(
    logging.FileHandler(os.path.join(LOG_DIR, "trace.log"))
)

app = FastAPI(title="ContractCop")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100", "http://127.0.0.1:3100"],
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi import File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

SAMPLES_DIR = os.path.join(AGENT_DIR, "data", "samples")



class ClaimIn(BaseModel):
    session: str = ""
    text: str
    contract_id: str = ""


class TranscriptIn(BaseModel):
    session: str = ""
    text: str


@app.post("/api/claim")
def post_claim(body: ClaimIn):
    if not body.contract_id:
        raise HTTPException(status_code=400, detail="contract_id is required")
    known = {c["contract_id"] for c in store.list_contracts()}
    if zetaris.SAMPLE_MODE:
        known.add("demo")
    if body.contract_id not in known:
        raise HTTPException(status_code=400, detail=f"unknown contract_id: {body.contract_id}")
    session = body.session or time.strftime("%Y%m%d")
    return claim_check.check_claim(session, body.text.strip(), body.contract_id)


@app.post("/api/transcript")
def post_transcript(body: TranscriptIn):
    """Parse a pasted/uploaded transcript into the rep's claim lines."""
    session = body.session or time.strftime("%Y%m%d")
    lines = transcript.parse_transcript(body.text)
    return {"session": session, "lines": lines, "total": len(lines)}


@app.get("/api/clauses")
def get_clauses(contract_id: str = ""):
    try:
        return {"clauses": zetaris.clause_rail(contract_id or "demo")}
    except Exception as error:
        return JSONResponse(status_code=502, content={"error": str(error)[:200]})


@app.get("/api/report")
def get_report(session: str):
    history = memory.session_history(session)
    contradictions = [h for h in history if h["verdict"] == "contradiction"]
    return {
        "session": session,
        "claims_total": len(history),
        "contradictions": len(contradictions),
        "timeline": history,
    }


@app.get("/api/health")
def health():
    if zetaris.SAMPLE_MODE:
        return {"zetaris": "sample mode"}
    checks = {}
    try:
        result = zetaris.run_sql("SELECT 1 AS one")
        checks["zetaris"] = "ok" if result["rows"] == [["1"]] else "unexpected"
    except Exception as error:
        checks["zetaris"] = str(error)[:120]
    return checks


@app.get("/store/contract.json")
def store_contract_feed():
    return {"clauses": store.clauses_feed()}


@app.get("/store/policy.json")
def store_policy_feed():
    return {"rules": store.rules_feed()}


@app.post("/api/contracts/extract")
async def extract_contracts(
    files: list[UploadFile] = File(...),
    kinds: list[str] = Form(...),
):
    if len(files) != len(kinds):
        raise HTTPException(status_code=400, detail="files and kinds must align")
    out = {"clauses": [], "rules": [], "dropped": 0, "chars": 0}
    pairs = []
    for f, kind in zip(files, kinds):
        data = await f.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{f.filename}: over 5 MB")
        pairs.append((f.filename or "file", data, kind))
    # contracts first so their topics steer the policy topics
    batches = [p for p in pairs if p[2] == "contract"] + [p for p in pairs if p[2] != "contract"]
    seen_topics: list = []
    for fname, data, kind in batches:
        hints = seen_topics if kind != "contract" else None
        if kind != "contract" and not hints:
            existing = {c.get("topic") for c in store.load()["clauses"]}
            hints = sorted(t for t in existing if t) or None
        part = extract.extract_document(fname, data, kind, hints)
        for c in part["clauses"]:
            if c["topic"] not in seen_topics:
                seen_topics.append(c["topic"])
        out["clauses"] += part["clauses"]
        out["rules"] += part["rules"]
        out["dropped"] += part["dropped"]
        out["chars"] += part["chars"]
    return out


class ContractIn(BaseModel):
    name: str
    clauses: list = []
    rules: list = []


@app.post("/api/contracts")
def save_contract(body: ContractIn):
    contract_id = store.add_contract(body.name, body.clauses, body.rules)
    sql = None
    zetaris_rows = None
    try:
        sql = ("SELECT COUNT(*) FROM contractcop.contract_flat "
               f"WHERE contract_id = '{contract_id}'")
        zetaris_rows = int(zetaris.run_sql(sql)["rows"][0][0])
    except Exception:
        pass
    return {"contract_id": contract_id, "clauses": len(body.clauses),
            "rules": len(body.rules), "zetaris_rows": zetaris_rows, "sql": sql}


@app.get("/api/contracts")
def list_contracts():
    data = store.load()
    out = []
    for c in data["contracts"]:
        cid = c["contract_id"]
        out.append({**c,
                    "clauses": sum(1 for x in data["clauses"] if x["contract_id"] == cid),
                    "rules": sum(1 for x in data["rules"] if x["contract_id"] == cid)})
    return {"contracts": out}


@app.delete("/api/contracts/{contract_id}")
def delete_contract(contract_id: str):
    if not store.delete_contract(contract_id):
        raise HTTPException(status_code=404, detail="unknown contract")
    return {"deleted": contract_id}



@app.get("/api/samples/{name}")
def get_sample(name: str):
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+", name):
        raise HTTPException(status_code=400, detail="bad name")
    path = os.path.join(SAMPLES_DIR, name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="no such sample")
    return FileResponse(path, filename=name)


if os.path.isdir(WEB_DIST):
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True))
else:

    @app.get("/")
    def root():
        return {
            "app": "ContractCop",
            "ui": "run pnpm dev in web/ or pnpm generate",
        }
