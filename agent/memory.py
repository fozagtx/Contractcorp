"""H-Mem: persistent claim memory for the ContractCop agent (Meterless engine).

This is the working Meterless Engine integration required by the hackathon
BUILD rule (engine: H-Mem, "persistent memory and retrieval").

What it does:
  - persists every rep claim and its verdict in SQLite (agent/memory.db),
    surviving server restarts and calls (sessions)
  - recalls, for each new claim, the earlier claims worth remembering:
    repeats of the same contradiction within the call, and the same
    claims made on earlier calls
  - surfaces those memories in the claim-check prompt as literal facts,
    with timestamps, so the agent can flag "already said and already wrong"

The demo the engine powers: a rep repeats a contradicted commitment later
in the same call, or makes the same contradicted commitment on a later
call, and the alert says so, citing the earlier claim.
"""
import os
import re
import sqlite3
import time
from contextlib import closing

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS claim_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    ts REAL NOT NULL,
    claim TEXT NOT NULL,
    norm TEXT NOT NULL,
    verdict TEXT NOT NULL,
    clause_id TEXT,
    policy_id TEXT,
    contract_id TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_memory_session ON claim_memory(session_id, ts);
CREATE INDEX IF NOT EXISTS idx_memory_norm ON claim_memory(norm);
"""


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def init() -> None:
    with closing(_connect()) as conn, conn:
        conn.executescript(_SCHEMA)
        try:
            conn.execute("ALTER TABLE claim_memory ADD COLUMN contract_id TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # column already there


def remember(session_id: str, claim: str, verdict: str,
             clause_id: str | None = None, policy_id: str | None = None,
             contract_id: str = "") -> None:
    init()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO claim_memory (session_id, ts, claim, norm, verdict, clause_id, policy_id, contract_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (session_id, time.time(), claim, _normalize(claim), verdict, clause_id, policy_id, contract_id),
        )


def _significant_words(norm: str) -> set:
    return {w for w in norm.split() if len(w) > 3}


def _score(new_norm: str, old_norm: str) -> float:
    """Word-overlap score between two claims (0..1).

    A repeat of the same commitment shares the load-bearing words even
    when the framing changes ("we'll give you the 10 percent automatic
    discount" vs "that 10 percent automatic discount is yours").
    """
    new_words = _significant_words(new_norm)
    old_words = _significant_words(old_norm)
    if not new_words or not old_words:
        return 0.0
    overlap = new_words & old_words
    return len(overlap) / min(len(new_words), len(old_words))


def recall(session_id: str, claim: str, limit: int = 4, contract_id: str = "") -> dict:
    """Memories worth attaching to a new claim-check.

    Returns {same_session: [...], earlier_calls: [...]} where each item is
    {claim, verdict, clause_id, ts, when, score}. `earlier_calls` holds
    matches from OTHER sessions only: that is the cross-call persistence
    the H-Mem engine exists for.
    """
    init()
    norm = _normalize(claim)
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT session_id, ts, claim, norm, verdict, clause_id, contract_id "
            "FROM claim_memory ORDER BY ts DESC LIMIT 400"
        ).fetchall()
    if contract_id:
        rows = [r for r in rows if (r["contract_id"] or "") == contract_id]
    same, earlier = [], []
    for row in rows:
        score = _score(norm, row["norm"])
        same_clause = bool(row["clause_id"]) and row["verdict"] == "contradiction"
        if score < 0.3 and not (same_clause and score >= 0.15):
            continue
        item = {
            "claim": row["claim"], "verdict": row["verdict"],
            "clause_id": row["clause_id"], "score": round(score, 2),
            "when": time.strftime("%H:%M", time.localtime(row["ts"])),
        }
        if row["session_id"] == session_id:
            if len(same) < limit:
                same.append(item)
        elif len(earlier) < limit:
            item["date"] = time.strftime("%d %b %H:%M", time.localtime(row["ts"]))
            earlier.append(item)
    same.sort(key=lambda m: -m["score"])
    earlier.sort(key=lambda m: -m["score"])
    return {"same_session": same, "earlier_calls": earlier}


def session_history(session_id: str) -> list:
    """Full timeline for the end-of-call report, oldest first."""
    init()
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT ts, claim, verdict, clause_id, policy_id FROM claim_memory "
            "WHERE session_id = ? ORDER BY ts",
            (session_id,),
        ).fetchall()
    return [dict(zip(("ts", "claim", "verdict", "clause_id", "policy_id"), tuple(r)))
            for r in rows]
