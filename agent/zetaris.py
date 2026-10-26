"""run_sql: one SQL statement against the local Zetaris instance, over REST.

Reads ZETARIS_REST_URL, ZETARIS_API_KEY and ZETARIS_ORG_ID from the
workspace .env. Every request is a POST to /sql-editor/sqls/run with a
Bearer API key, X-Org-ID and a fresh UUID X-Request-ID.
"""
import json
import os
import re
import time
import uuid

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

SAMPLE_MODE = os.environ.get("SAMPLE_MODE", "").strip().lower() == "true"

REST_URL = os.environ["ZETARIS_REST_URL"].rstrip("/")
API_KEY = os.environ["ZETARIS_API_KEY"]
ORG_ID = os.environ["ZETARIS_ORG_ID"]

ID_RE = re.compile(r"^[a-z0-9_.-]+$")

_topic_cache: dict = {}  # contract_id -> (fetched_at, [topics])


def _checked_id(value: str) -> str:
    if not ID_RE.fullmatch(value or ""):
        raise ZetarisError(f"bad identifier for query: {value!r}")
    return value.replace("'", "''")


class ZetarisError(RuntimeError):
    pass


def run_sql(sql: str, limit: int = 50) -> dict:
    """Run one statement. Returns {columns, rows, total, ms}."""
    started = time.time()
    if SAMPLE_MODE:
        if sql.strip() == "SELECT 1 AS one":
            return {"columns": ["one"], "rows": [["1"]], "total": 1,
                    "ms": int((time.time() - started) * 1000)}
        raise ZetarisError("sample mode: run_sql is not backed by fixtures")
    response = requests.post(
        REST_URL + "/sql-editor/sqls/run",
        headers={
            "Authorization": "Bearer " + API_KEY,
            "X-Org-ID": ORG_ID,
            "X-Request-ID": str(uuid.uuid4()),
        },
        json={"queryId": str(uuid.uuid4()), "sql": sql,
              "source": "SqlEditor", "limit": limit},
        timeout=90,
    )
    if response.status_code != 200:
        raise ZetarisError(f"Zetaris REST {response.status_code}: {response.text[:120]}")
    body = response.json()
    columns = body.get("headers", [])
    rows = body.get("data", [])
    return {
        "columns": columns,
        "rows": rows,
        "total": body.get("total", len(rows)),
        "ms": int((time.time() - started) * 1000),
    }


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _fixture_rows(topic: str | None = None) -> list:
    """Local contract + policy JSON, joined on topic, in the live row shape."""
    contract = json.load(open(os.path.join(DATA_DIR, "contract.json")))
    policy = json.load(open(os.path.join(DATA_DIR, "policy.json")))
    rules = {r["topic"]: r for r in policy["rules"]}
    rows = []
    for c in contract["clauses"]:
        if topic is not None and c["topic"] != topic:
            continue
        r = rules.get(c["topic"], {})
        rows.append(["demo", c["clause_id"], c["section"], c["text"],
                     c["topic"], r.get("policy_id"), r.get("rule")])
    return rows


def topics(contract_id: str) -> list:
    """Distinct topics for a contract; cached 60 s per id."""
    if SAMPLE_MODE:
        return sorted({r[4] for r in _fixture_rows()})
    cached = _topic_cache.get(contract_id)
    if cached and time.time() - cached[0] < 60:
        return cached[1]
    result = run_sql(
        "SELECT DISTINCT topic FROM contractcop.contract_flat "
        f"WHERE contract_id = '{_sql_id(contract_id)}'"
    )
    ts = sorted(row[0] for row in result["rows"])
    _topic_cache[contract_id] = (time.time(), ts)
    return ts


def _sql_id(v: str) -> str:
    return v if SAMPLE_MODE else _checked_id(v)


def fetch_topic(contract_id: str, topic: str) -> dict:
    """Clauses + matching policy rows for one contract and topic.

    contract_id and topic are pattern-validated before they touch SQL.
    """
    sql = (
        "SELECT c.clause_id, c.section, c.text, p.policy_id, p.rule "
        "FROM contractcop.contract_flat c "
        "LEFT JOIN contractcop.policy_flat p "
        "ON c.topic = p.topic AND c.contract_id = p.contract_id "
        f"WHERE c.contract_id = '{_sql_id(contract_id)}' AND c.topic = '{_sql_id(topic)}'"
    )
    if SAMPLE_MODE:
        started = time.time()
        clauses = [
            {
                "clause_id": row[1], "section": row[2], "text": row[3],
                "policy_id": row[5], "policy_rule": row[6],
            }
            for row in _fixture_rows(topic)
        ]
        return {
            "sql": "-- SAMPLE_MODE: served from agent/data fixtures, not Zetaris\n" + sql,
            "clauses": clauses,
            "ms": int((time.time() - started) * 1000),
        }
    result = run_sql(sql)
    clauses = [
        {
            "clause_id": row[0], "section": row[1], "text": row[2],
            "policy_id": row[3], "policy_rule": row[4],
        }
        for row in result["rows"]
    ]
    return {"sql": sql, "clauses": clauses, "ms": result["ms"]}


def clause_rail(contract_id: str) -> list:
    """All clauses with their policy counterparts, for one contract."""
    if SAMPLE_MODE:
        return [
            {"clause_id": row[1], "section": row[2], "text": row[3],
             "topic": row[4], "policy_id": row[5], "policy_rule": row[6]}
            for row in sorted(_fixture_rows(), key=lambda r: r[1])
        ]
    result = run_sql(
        "SELECT c.clause_id, c.section, c.text, c.topic, p.policy_id, p.rule "
        "FROM contractcop.contract_flat c "
        "LEFT JOIN contractcop.policy_flat p "
        "ON c.topic = p.topic AND c.contract_id = p.contract_id "
        f"WHERE c.contract_id = '{_sql_id(contract_id)}' "
        "ORDER BY c.clause_id"
    )
    return [
        {"clause_id": row[0], "section": row[1], "text": row[2],
         "topic": row[3], "policy_id": row[4], "policy_rule": row[5]}
        for row in result["rows"]
    ]
