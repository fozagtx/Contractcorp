"""Extraction: verbatim validation and json passthrough (no live model)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json

from agent import extract


def test_extract_drops_invented_rows(monkeypatch):
    doc = b"# Agreement\n\n3.1 Payment is due net thirty days."
    monkeypatch.setattr(extract.llm, "chat", lambda *a, **k: (
        json.dumps({"clauses": [
            {"clause_id": "3.1", "section": "Payment",
             "text": "Payment is due net thirty days.", "topic": "payment"},
            {"clause_id": "9.9", "section": "Invented",
             "text": "Free upgrades forever for everyone.", "topic": "upsell"},
        ]}), None))
    out = extract.extract_document("a.md", doc, "contract")
    assert len(out["clauses"]) == 1
    assert out["clauses"][0]["clause_id"] == "3.1"
    assert out["dropped"] == 1


def test_extract_json_passthrough():
    payload = json.dumps({"clauses": [
        {"clause_id": "1", "section": "X", "text": "verbatim row", "topic": "x"}]})
    doc = f"prefix {payload} suffix verbatim row".encode()
    out = extract.extract_document("doc.json", doc, "contract")
    assert out["clauses"][0]["text"] == "verbatim row"
