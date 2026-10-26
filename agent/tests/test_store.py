"""Contract store: add/list/delete and slug collisions."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent import store


def test_add_list_delete(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "contracts.json"))
    cid = store.add_contract("Acme MSA", [{"clause_id": "1"}], [])
    assert cid == "acme-msa"
    assert [c["contract_id"] for c in store.list_contracts()] == ["acme-msa"]
    assert store.delete_contract(cid) is True
    assert store.list_contracts() == []


def test_slug_collision(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "contracts.json"))
    a = store.add_contract("Acme", [], [])
    b = store.add_contract("Acme", [], [])
    assert a == "acme" and b != a and b.startswith("acme-")
