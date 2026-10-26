"""ContractCop server: FastAPI over the claim-check agent.

Run from the workspace root:
    .venv/bin/uvicorn agent.server:app --reload --port 8600

The UI is the Nuxt app in web/: `cd web && pnpm install && pnpm dev` for
development on http://localhost:3100, or `cd web && pnpm generate` and this
server will serve the static build at http://localhost:8600/.
"""
import os
import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import claim_check, memory, transcript, zetaris

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIST = os.path.join(os.path.dirname(AGENT_DIR), "web", ".output", "public")

app = FastAPI(title="ContractCop")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100", "http://127.0.0.1:3100"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


if os.path.isdir(WEB_DIST):
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True))
else:

    @app.get("/")
    def root():
        return {
            "app": "ContractCop",
            "ui": "run pnpm dev in web/ or pnpm generate",
        }
