"""Unit tests for the H-Mem memory engine (agent/memory.py).

Uses a throwaway SQLite file per test so the agent's real memory.db is
never touched. These are the conformance tests for the Meterless engine
integration the hackathon BUILD rule asks for.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import agent.memory as memory


def fresh_memory(monkeypatch, tmp_path):
    db = tmp_path / "mem.db"
    monkeypatch.setattr(memory, "DB_PATH", str(db))
    memory.init()
    return db


def test_remember_and_recall_repeat_in_same_session(monkeypatch, tmp_path):
    fresh_memory(monkeypatch, tmp_path)
    memory.remember("call-1", "We'll give you the 10 percent automatic discount",
                    "contradiction", "3.1", "POL-01")
    result = memory.recall("call-1", "that 10 percent automatic discount is yours")
    assert result["same_session"], "a near-repeat must be recalled"
    assert result["same_session"][0]["verdict"] == "contradiction"
    assert result["same_session"][0]["clause_id"] == "3.1"
    assert result["earlier_calls"] == []


def test_recall_cross_session_persistence(monkeypatch, tmp_path):
    fresh_memory(monkeypatch, tmp_path)
    memory.remember("monday-call", "You get 24/7 support on the Standard Plan",
                    "contradiction", "4.2", "POL-02")
    result = memory.recall("tuesday-call", "you will have 24/7 support on the Standard Plan")
    assert result["earlier_calls"], "memory must survive across sessions"
    assert result["same_session"] == []
    assert result["earlier_calls"][0]["clause_id"] == "4.2"


def test_unrelated_claims_do_not_match(monkeypatch, tmp_path):
    fresh_memory(monkeypatch, tmp_path)
    memory.remember("call-1", "We will store your data in Frankfurt as signed",
                    "consistent", "6.1", "POL-03")
    result = memory.recall("call-1", "How about that game last night")
    assert result["same_session"] == [] and result["earlier_calls"] == []


def test_score_normalizes_punctuation_and_case():
    a = memory._normalize("We'll give you 10% — automatically!!")
    b = memory._normalize("well give you 10 automatically")
    assert memory._score(a, b) > 0.4


def test_session_history_orders_oldest_first(monkeypatch, tmp_path):
    fresh_memory(monkeypatch, tmp_path)
    memory.remember("call-1", "first claim", "consistent")
    memory.remember("call-1", "second claim", "contradiction", "3.1")
    history = memory.session_history("call-1")
    assert [h["claim"] for h in history] == ["first claim", "second claim"]


def test_persistence_survives_reopen(monkeypatch, tmp_path):
    db = fresh_memory(monkeypatch, tmp_path)
    memory.remember("call-1", "persistent claim", "contradiction", "9.1")
    # a brand-new connection is exactly what a server restart means here
    result = memory.recall("call-1", "persistent claim")
    assert result["same_session"], "memory must survive a restart"
    assert os.path.exists(db)
