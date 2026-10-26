"""Sample mode: fixtures + recorded verdicts with no Zetaris or Nightshift."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import openai
import pytest

from agent import claim_check, zetaris


@pytest.fixture
def sample_on(monkeypatch, tmp_path):
    monkeypatch.setattr(zetaris, "SAMPLE_MODE", True)
    monkeypatch.setattr(claim_check, "SAMPLE_MODE", True)
    import agent.memory as memory
    monkeypatch.setattr(memory, "DB_PATH", str(tmp_path / "m.db"))
    monkeypatch.setattr(memory, "recall", lambda *a, **k: {"same_session": [], "earlier_calls": []})
    monkeypatch.setattr(memory, "remember", lambda *a, **k: None)


def test_sample_fetch_topic_discounts(sample_on):
    out = zetaris.fetch_topic("discounts")
    assert out["clauses"][0]["clause_id"] == "3.1"
    assert "-- SAMPLE_MODE: served from agent/data fixtures, not Zetaris" in out["sql"]
    assert "WHERE c.topic = 'discounts'" in out["sql"]


def test_sample_check_claim_recorded(sample_on, monkeypatch):
    def dead(*a, **k):
        raise openai.APIConnectionError(request=None)

    monkeypatch.setattr(claim_check.llm, "chat", dead)
    card = claim_check.check_claim(
        "s1", "We'll give you the 10 percent automatic discount on this order, no approval needed.")
    assert card["verdict"] == "contradiction"
    assert card["clause"]["clause_id"] == "3.1"
    assert card["model"] == "recorded (sample mode)"


def test_sample_unknown_claim_is_unclear(sample_on, monkeypatch):
    def dead(*a, **k):
        raise openai.APIConnectionError(request=None)

    monkeypatch.setattr(claim_check.llm, "chat", dead)
    card = claim_check.check_claim("s1", "This claim was never recorded anywhere.")
    assert card["verdict"] == "unclear"
    assert card["reason"] == "sample mode: no recorded verdict for this claim"


def test_live_fetch_topic_calls_rest(monkeypatch):
    monkeypatch.setattr(zetaris, "SAMPLE_MODE", False)
    called = {}

    def fake_run_sql(sql, limit=50):
        called["sql"] = sql
        return {"columns": [], "rows": [], "total": 0, "ms": 1}

    monkeypatch.setattr(zetaris, "run_sql", fake_run_sql)
    zetaris.fetch_topic("discounts")
    assert "WHERE c.topic = 'discounts'" in called["sql"]
