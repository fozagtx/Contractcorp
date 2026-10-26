"""The claim-check loop: a bounded two-hop agent with an evidence chain.

Hop 1 (route):   Nemotron reads the rep's sentence and picks the Zetaris
                 topic to look up, or marks the sentence unrelated.
Lookup:          run_sql fetches the contract clauses AND the matching sales
                 policy rows from Zetaris in one cross-source JOIN query.
Hop 2 (verdict): Nemotron judges the claim against the literal clause text
                 and the policy rows, plus H-Mem memories, and returns a
                 STRICT JSON verdict: it picks clause/policy IDs and gives
                 a reason. It never writes clause text - the words in the
                 alert always come from Zetaris.

Safety (from the ClauseCatcher discipline):
  - any model/parse/network error resolves to "unclear", never an accusation
  - the topic from hop 1 is whitelist-validated before it touches SQL
  - alerts require a clause_id the checker actually judged contradicted
"""
import json
import re
import time

from agent import llm, memory, zetaris

UNRELATED = "unrelated"
UNCLEAR = "unclear"


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in reply")
    return json.loads(match.group(0))


def _route(claim: str) -> dict:
    """Hop 1: decide which topic to look up in Zetaris."""
    prompt = (
        "You route sentences said by a sales rep on a customer call.\n"
        "Topics: discounts, support, data_residency, termination, uptime.\n"
        'If the sentence makes or implies a commitment about one of these, '
        'reply {"topic": "<one topic>"}. If it is small talk or nothing a '
        'contract could contradict, reply {"topic": null}. JSON only.\n\n'
        f"Sentence: {claim}"
    )
    content, _ = llm.chat([{"role": "user", "content": prompt}], max_tokens=600)
    parsed = _extract_json(content)
    topic = parsed.get("topic")
    if topic is not None and topic not in zetaris.TOPIC_WHITELIST:
        topic = None
    return {"topic": topic}


def _judge(claim: str, clauses: list, memories: dict) -> dict:
    """Hop 2: verdict against the literal clause text + policy + memory."""
    clause_lines = "\n".join(
        f'- CLAUSE {c["clause_id"]} ({c["section"]}): {c["text"]}\n'
        f'  POLICY {c["policy_id"]}: {c["policy_rule"]}'
        for c in clauses
    )
    memory_lines = []
    for m in memories.get("same_session", []):
        memory_lines.append(
            f'- earlier this call ({m["when"]}): rep said "{m["claim"]}" '
            f'-> verdict {m["verdict"]}'
            + (f', clause {m["clause_id"]}' if m.get("clause_id") else ""))
    for m in memories.get("earlier_calls", []):
        memory_lines.append(
            f'- on an earlier call ({m["date"]}): rep said "{m["claim"]}" '
            f'-> verdict {m["verdict"]}'
            + (f', clause {m["clause_id"]}' if m.get("clause_id") else ""))
    memory_block = ("\nMemory of earlier claims (facts, use them):\n"
                    + "\n".join(memory_lines)) if memory_lines else ""

    prompt = (
        "A sales rep is on a call with a customer. Judge the rep's claim "
        "against the signed contract clauses and sales policy below.\n\n"
        f"CONTRACT CLAUSES + POLICY:\n{clause_lines}\n"
        f"{memory_block}\n\n"
        f"REP CLAIM: {claim}\n\n"
        "Reply with STRICT JSON, no other text:\n"
        '{"verdict": "contradiction" | "consistent" | "unclear", '
        '"clause_id": "<id from the clauses above or null>", '
        '"policy_id": "<id or null>", '
        '"reason": "<one sentence citing what the claim contradicts>"}\n'
        "contradiction = the claim conflicts with a clause or policy above. "
        "consistent = the clause/policy allows it. unclear = you cannot tell. "
        "A vague statement with no specific figure or commitment ('we might "
        "do something on price', 'our uptime is great, trust me') is unclear, "
        "NOT a contradiction - only a concrete claim can contradict. "
        "Only use clause_id values that appear above. Never invent clause text."
    )
    content, _ = llm.chat([{"role": "user", "content": prompt}], max_tokens=1500)
    parsed = _extract_json(content)
    verdict = parsed.get("verdict", UNCLEAR)
    if verdict not in ("contradiction", "consistent", UNCLEAR):
        verdict = UNCLEAR
    clause_id = parsed.get("clause_id")
    policy_id = parsed.get("policy_id")
    if verdict == "contradiction" and not clause_id:
        # an alert requires an evidence clause the checker named
        verdict = UNCLEAR
    return {
        "verdict": verdict,
        "clause_id": clause_id,
        "policy_id": policy_id,
        "reason": (parsed.get("reason") or "")[:300],
    }


def check_claim(session_id: str, claim: str) -> dict:
    """The full pipeline for one rep sentence. Returns the event card."""
    hops = []
    started = time.time()
    memories = {"same_session": [], "earlier_calls": []}
    try:
        memories = memory.recall(session_id, claim)
    except Exception as error:  # a memory failure must not kill the check
        hops.append({"hop": "memory", "detail": str(error)[:120]})
    try:
        t0 = time.time()
        route = _route(claim)
        hops.append({"hop": "route", "ms": int((time.time() - t0) * 1000)})
        if route["topic"] is None:
            memory.remember(session_id, claim, UNRELATED)
            return {
                "claim": claim, "verdict": UNRELATED, "clause": None,
                "policy": None, "memory": memories, "hops": hops,
                "sql": None, "model": llm.MODEL, "ms": int((time.time() - started) * 1000),
            }
        fetched = zetaris.fetch_topic(route["topic"])
        if not fetched["clauses"]:
            raise zetaris.ZetarisError(f"no rows for topic {route['topic']}")
        t1 = time.time()
        verdict = _judge(claim, fetched["clauses"], memories)
        hops.append({"hop": "verdict", "ms": int((time.time() - t1) * 1000)})
        clause = next((c for c in fetched["clauses"]
                       if c["clause_id"] == verdict["clause_id"]), None)
        policy = ({"policy_id": clause["policy_id"], "rule": clause["policy_rule"]}
                  if clause else None)
        memory.remember(session_id, claim, verdict["verdict"],
                        verdict["clause_id"], verdict["policy_id"])
        return {
            "claim": claim,
            "verdict": verdict["verdict"],
            "clause": ({"clause_id": clause["clause_id"], "section": clause["section"],
                        "text": clause["text"]} if clause else None),
            "policy": policy,
            "reason": verdict["reason"],
            "memory": memories,
            "hops": hops,
            "sql": fetched["sql"],
            "sql_ms": fetched["ms"],
            "model": llm.MODEL,
            "ms": int((time.time() - started) * 1000),
        }
    except Exception as error:  # never accuse on failure
        memory.remember(session_id, claim, UNCLEAR)
        hops.append({"hop": "error", "detail": str(error)[:200]})
        return {
            "claim": claim, "verdict": UNCLEAR, "clause": None,
            "policy": None, "memory": memories, "hops": hops,
            "sql": None, "model": llm.MODEL,
            "error": str(error)[:200],
            "ms": int((time.time() - started) * 1000),
        }
