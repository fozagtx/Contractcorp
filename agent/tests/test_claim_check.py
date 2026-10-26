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
    """If Zetaris/Nemotron are down, the verdict is unclear — never a false alert."""
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
