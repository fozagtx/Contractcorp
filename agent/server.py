"""ContractCop cockpit server: FastAPI over the claim-check agent.

Run from the workspace root:
    .venv/bin/uvicorn agent.server:app --reload --port 8600
"""
import os
import time
import uuid

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from agent import claim_check, memory, transcript, zetaris

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
COCKPIT = os.path.join(AGENT_DIR, "cockpit", "index.html")

app = FastAPI(title="ContractCop")


class ClaimIn(BaseModel):
    session: str = ""
    text: str


class TranscriptIn(BaseModel):
    session: str = ""
    text: str


@app.post("/api/claim")
def post_claim(body: ClaimIn):
    session = body.session or time.strftime("%Y%m%d")
    return claim_check.check_claim(session, body.text.strip())


@app.post("/api/transcript")
def post_transcript(body: TranscriptIn):
    """Parse a pasted/uploaded transcript into the rep's claim lines."""
    session = body.session or time.strftime("%Y%m%d")
    lines = transcript.parse_transcript(body.text)
    return {"session": session, "lines": lines, "total": len(lines)}


@app.get("/api/clauses")
def get_clauses():
    try:
        return {"clauses": zetaris.clause_rail()}
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
    checks = {}
    try:
        result = zetaris.run_sql("SELECT 1 AS one")
        checks["zetaris"] = "ok" if result["rows"] == [["1"]] else "unexpected"
    except Exception as error:
        checks["zetaris"] = str(error)[:120]
    return checks


@app.get("/")
def cockpit():
    return FileResponse(COCKPIT)
