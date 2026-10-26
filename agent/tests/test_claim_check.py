"""Unit tests for claim-check safety mechanics (no live model needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from agent import claim_check, zetaris


def test_extract_json_plain():
    assert claim_check._extract_json('noise {"verdict": "consistent"} noise')["verdict"] == "consistent"


def test_extract_json_multiline():
    text = 'reasoning...\n{"verdict": "contradiction",\n "clause_id": "3.1"}'
    assert claim_check._extract_json(text)["clause_id"] == "3.1"


def test_extract_json_rejects_garbage():
    with pytest.raises(ValueError):
        claim_check._extract_json("no json here")


def test_topic_whitelist_blocks_injection():
    # a model-returned topic must never reach SQL unchecked
    for bad in ("discounts' OR 1=1 --", "uptime; DROP TABLE x", "", "nonsense"):
        assert bad not in zetaris.TOPIC_WHITELIST
    with pytest.raises(zetaris.ZetarisError):
        zetaris.fetch_topic("discounts' OR 1=1 --")


def test_check_claim_unreachable_backend_is_unclear_not_accusation(monkeypatch, tmp_path):
    """If Zetaris/Nemotron are down, the verdict is unclear, never a false alert."""
    import agent.memory as memory
    monkeypatch.setattr(memory, "DB_PATH", str(tmp_path / "m.db"))

    def boom(*args, **kwargs):
        raise RuntimeError("backend on fire")

    monkeypatch.setattr(memory, "recall", boom)
    monkeypatch.setattr(memory, "remember", lambda *a, **k: None)
    monkeypatch.setattr(claim_check, "_route", boom)
    card = claim_check.check_claim("s1", "We give you 24/7 support on the Standard Plan")
    assert card["verdict"] == claim_check.UNCLEAR
    assert "error" in card


def test_validate_span_exact():
    text = "No discount is automatic. Any discount over ten percent needs approval."
    assert claim_check._validate_span(text, "No discount is automatic") == "No discount is automatic"


def test_validate_span_case_insensitive_returns_original():
    text = "Any discount greater than ten percent (10%) requires prior written approval"
    out = claim_check._validate_span(text, "any discount GREATER than ten percent")
    assert out == "Any discount greater than ten percent"


def test_validate_span_whitespace_normalized():
    text = "Any discount   greater than\n ten percent requires approval"
    out = claim_check._validate_span(text, "discount greater than ten percent")
    assert out == "discount greater than ten percent"


def test_validate_span_rejects_non_substring():
    assert claim_check._validate_span("the clause text", "words never said") is None


def test_validate_span_none():
    assert claim_check._validate_span("some text", None) is None
    assert claim_check._validate_span(None, "x") is None


def test_validate_span_over_limit():
    text = "word " * 60
    assert claim_check._validate_span(text, text) is None


def test_check_claim_drops_span_not_in_clause(monkeypatch, tmp_path):
    """A clause_span the model invented must not reach the event card."""
    import agent.memory as memory
    monkeypatch.setattr(memory, "DB_PATH", str(tmp_path / "m.db"))
    monkeypatch.setattr(memory, "recall", lambda *a, **k: {"same_session": [], "earlier_calls": []})
    monkeypatch.setattr(memory, "remember", lambda *a, **k: None)

    monkeypatch.setattr(claim_check, "_route", lambda claim: {"topic": "discounts"})
    clause = {
        "clause_id": "3.1", "section": "Fees and Discounts",
        "text": "No discount is automatic. Approval is required.",
        "policy_id": "POL-01", "policy_rule": "rule",
    }
    monkeypatch.setattr(claim_check.zetaris, "fetch_topic",
                        lambda topic: {"sql": "SELECT 1", "ms": 1, "clauses": [clause]})
    monkeypatch.setattr(claim_check, "_judge", lambda *a, **k: {
        "verdict": "contradiction", "clause_id": "3.1", "policy_id": "POL-01",
        "reason": "conflicts", "claim_span": "10 percent automatic discount",
        "clause_span": "words the model made up",
    })

    card = claim_check.check_claim("s1", "We give a 10 percent automatic discount")
    assert card["verdict"] == "contradiction"
    assert card["spans"]["clause"] is None
    assert card["spans"]["claim"] == "10 percent automatic discount"
