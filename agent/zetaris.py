"""run_sql: one SQL statement against the local Zetaris instance, over REST.

Reads ZETARIS_REST_URL, ZETARIS_API_KEY and ZETARIS_ORG_ID from the
workspace .env. Every request is a POST to /sql-editor/sqls/run with a
Bearer API key, X-Org-ID and a fresh UUID X-Request-ID.
"""
import json
import os
import time
import uuid

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

REST_URL = os.environ["ZETARIS_REST_URL"].rstrip("/")
API_KEY = os.environ["ZETARIS_API_KEY"]
ORG_ID = os.environ["ZETARIS_ORG_ID"]

TOPIC_WHITELIST = {
    "discounts", "support", "data_residency", "termination", "uptime",
}


class ZetarisError(RuntimeError):
    pass


def run_sql(sql: str, limit: int = 50) -> dict:
    """Run one statement. Returns {columns, rows, total, ms}."""
    started = time.time()
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


def fetch_topic(topic: str) -> dict:
    """The demo cross-source query: contract clauses JOIN sales policy by topic.

    The topic comes from the model's routing step, so it is validated against
    a whitelist before it is ever placed in SQL.
    """
    if topic not in TOPIC_WHITELIST:
        raise ZetarisError(f"unknown topic: {topic!r}")
    sql = (
        "SELECT c.clause_id, c.section, c.text, p.policy_id, p.rule "
        "FROM clauseguard.contract_flat c "
        "JOIN clauseguard.policy_flat p ON c.topic = p.topic "
        f"WHERE c.topic = '{topic}'"
    )
    result = run_sql(sql)
    clauses = [
        {
            "clause_id": row[0], "section": row[1], "text": row[2],
            "policy_id": row[3], "policy_rule": row[4],
        }
        for row in result["rows"]
    ]
    return {"sql": sql, "clauses": clauses, "ms": result["ms"]}


def clause_rail() -> list:
    """All clauses with their policy counterparts, for the cockpit rail."""
    result = run_sql(
        "SELECT c.clause_id, c.section, c.text, p.policy_id, p.rule "
        "FROM clauseguard.contract_flat c "
        "JOIN clauseguard.policy_flat p ON c.topic = p.topic "
        "ORDER BY c.clause_id"
    )
    return [
        {"clause_id": row[0], "section": row[1], "text": row[2],
         "policy_id": row[3], "policy_rule": row[4]}
        for row in result["rows"]
    ]
