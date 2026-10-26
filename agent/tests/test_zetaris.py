"""Live integration tests: Zetaris REST + the measured accuracy fixture.

These hit the real local Zetaris and the real Nemotron route through
Meterless Nightshift (both must be running). The accuracy test is the
honest measured-evidence run for the demo: verdict accuracy against the
labeled fixture, plus per-claim latency.
"""
import json
import os
import statistics
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent import claim_check, zetaris

HERE = os.path.dirname(os.path.abspath(__file__))


def test_zetaris_select_one():
    result = zetaris.run_sql("SELECT 1 AS one")
    assert result["rows"] == [["1"]]


def test_zetaris_clause_rail_has_all_five_clauses():
    rail = zetaris.clause_rail()
    ids = sorted(c["clause_id"] for c in rail)
    assert ids == ["3.1", "4.2", "6.1", "8.3", "9.1"]


def test_zetaris_cross_source_join():
    fetched = zetaris.fetch_topic("uptime")
    assert fetched["clauses"], "the JOIN must return the uptime clause + policy"
    clause = fetched["clauses"][0]
    assert clause["clause_id"] == "9.1"
    assert clause["policy_id"] == "POL-04"


@pytest.mark.skipif(os.environ.get("SKIP_ACCURACY") == "1",
                    reason="SKIP_ACCURACY=1")
def test_labeled_claims_accuracy():
    """Verdict accuracy + median latency on the labeled fixture.

    Not a pass/fail quality gate: the point is an honest, reproducible
    number for the submission (pass = every claim produced a verdict
    card without crashing; the accuracy figure is printed for evidence).
    """
    claims = json.load(open(os.path.join(HERE, "labeled_claims.json")))
    correct = 0
    clause_correct = 0
    latencies = []
    per_claim = []
    session = "accuracy-run-" + time.strftime("%H%M%S")
    for item in claims:
        t0 = time.time()
        card = claim_check.check_claim(session, item["claim"])
        latencies.append(time.time() - t0)
        verdict_ok = card["verdict"] == item["expected_verdict"]
        clause_ok = (card["clause"] or {}).get("clause_id") == item["expected_clause"]
        correct += verdict_ok
        clause_correct += clause_ok
        per_claim.append(f"  {card['verdict']:13} (want {item['expected_verdict']:13}) "
                          f"got-clause={(card['clause'] or {}).get('clause_id')} "
                          f"{'OK' if verdict_ok else 'MISS'} "
                          f"[{item['label']}] {card.get('error', '')}")
    print("\n=== labeled-claims accuracy run ===")
    print("\n".join(per_claim))
    print(f"verdict accuracy: {correct}/{len(claims)}")
    print(f"clause accuracy:  {clause_correct}/{len(claims)}")
    print(f"median latency: {statistics.median(latencies):.1f}s per claim")
    assert len(per_claim) == len(claims)
