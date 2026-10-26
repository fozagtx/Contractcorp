"""Contract store: uploaded contracts + clauses + policy rules.

Persists to agent/store/contracts.json (gitignored). Written through a lock
and saved atomically (tmp file + rename). Starts empty: nothing is seeded.
"""
import json
import os
import re
import threading
import time
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store")
STORE_PATH = os.path.join(DATA_DIR, "contracts.json")

_lock = threading.Lock()


def _empty() -> dict:
    return {"contracts": [], "clauses": [], "rules": []}


def load() -> dict:
    with _lock:
        try:
            return json.load(open(STORE_PATH))
        except OSError:
            return _empty()


def save(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = STORE_PATH + ".tmp"
    with _lock:
        with open(tmp, "w") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, STORE_PATH)


def list_contracts() -> list:
    return load()["contracts"]


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "contract"
    return slug[:48]


def add_contract(name: str, clauses: list, rules: list) -> str:
    data = load()
    contract_id = _slug(name)
    taken = {c["contract_id"] for c in data["contracts"]}
    if contract_id in taken:
        contract_id = f"{contract_id}-{uuid.uuid4().hex[:4]}"
    data["contracts"].append({
        "contract_id": contract_id,
        "name": name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "files": [],
    })
    for c in clauses:
        row = dict(c)
        row["contract_id"] = contract_id
        data["clauses"].append(row)
    for r in rules:
        row = dict(r)
        row["contract_id"] = contract_id
        data["rules"].append(row)
    save(data)
    return contract_id


def delete_contract(contract_id: str) -> bool:
    data = load()
    before = len(data["contracts"])
    data["contracts"] = [c for c in data["contracts"] if c["contract_id"] != contract_id]
    if len(data["contracts"]) == before:
        return False
    data["clauses"] = [c for c in data["clauses"] if c["contract_id"] != contract_id]
    data["rules"] = [r for r in data["rules"] if r["contract_id"] != contract_id]
    save(data)
    return True


def clauses_feed() -> list:
    rows = load()["clauses"]
    return rows or [{"contract_id": "_none", "clause_id": "", "section": "",
                     "text": "", "topic": ""}]


def rules_feed() -> list:
    rows = load()["rules"]
    return rows or [{"contract_id": "_none", "policy_id": "", "topic": "",
                     "rule": ""}]
