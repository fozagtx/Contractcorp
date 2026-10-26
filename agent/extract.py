"""Extract clause/policy rows from uploaded documents via Nemotron.

Every returned text/rule is validated as a verbatim substring of the source
document (whitespace-normalized, case-insensitive, 1500-char limit); rows the
model invented are dropped and counted, never passed through.
"""
import json
import re

from agent import llm
from agent.claim_check import _extract_json
from agent.textmatch import validate_span

MAX_BYTES = 5 * 1024 * 1024
CHUNK = 6000
TEXT_EXTS = {".txt", ".md", ".csv", ".json"}


def _doc_text(filename: str, data: bytes) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in TEXT_EXTS:
        return data.decode("utf-8", errors="replace")
    if ext == ".pdf":
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"unsupported file type: {filename}")


def _chunks(text: str) -> list[str]:
    if len(text) <= CHUNK:
        return [text]
    paras = re.split(r"\n\s*\n", text)
    out, cur = [], ""
    for para in paras:
        if cur and len(cur) + len(para) + 2 > CHUNK:
            out.append(cur)
            cur = para
        else:
            cur = cur + "\n\n" + para if cur else para
    if cur:
        out.append(cur)
    return out or [text]


def _norm_topic(topic: object) -> str:
    return re.sub(r"[\s-]+", "_", str(topic or "general").strip().lower())


def _prompt(kind: str, chunk: str, topics: list | None = None) -> str:
    if kind == "policy":
        shape = '{"rules":[{"policy_id","topic","rule"}]}'
        what = ("each sales-policy rule. `rule` must be copied verbatim from "
                "the document; `policy_id` is the document numbering if "
                "present else POL-1, POL-2...")
        if topics:
            what += (" Assign each rule's `topic` to the closest value from "
                     f"this list: [{', '.join(topics)}]. Only if none applies, "
                     "create a new snake_case topic.")
    else:
        shape = '{"clauses":[{"clause_id","section","text","topic"}]}'
        what = ("each contractual obligation, one per row, 1 to 4 sentences. "
                "`text` must be copied verbatim from the document; "
                "`clause_id` is the numbering in the document if present "
                "else C1, C2...; `section` is the clause heading or short "
                "title")
        what += (" Use broad topics (one or two words) and reuse the same "
                 "topic for clauses about the same subject; aim for at most "
                 "8 distinct topics per document.")
    return (
        f"Extract {what}. `topic` is a short snake_case subject.\n\n"
        f"DOCUMENT:\n{chunk}\n\n"
        f"Reply with STRICT JSON only, no other text:\n{shape}"
    )


def extract_document(filename: str, data: bytes, kind: str, topics: list | None = None) -> dict:
    """One file -> verified clause/rule rows. Preview only, nothing saved."""
    if len(data) > MAX_BYTES:
        raise ValueError(f"{filename}: over 5 MB")
    text = _doc_text(filename, data)
    if not text.strip():
        return {"clauses": [], "rules": [], "dropped": 0, "chars": 0}

    if filename.lower().endswith(".json"):
        parsed = _extract_json(text)
        if isinstance(parsed.get("clauses"), list) or isinstance(parsed.get("rules"), list):
            clauses = [c for c in parsed.get("clauses", []) if validate_span(text, c.get("text"), 1500)]
            rules = [r for r in parsed.get("rules", []) if validate_span(text, r.get("rule"), 1500)]
            dropped = len(parsed.get("clauses", [])) - len(clauses) + len(parsed.get("rules", [])) - len(rules)
            return {"clauses": clauses, "rules": rules, "dropped": dropped,
                    "chars": len(text)}

    clauses, rules, dropped = [], [], 0
    for chunk in _chunks(text):
        content, _ = llm.chat(
            [{"role": "user", "content": _prompt(kind, chunk, topics)}],
            max_tokens=4000)
        parsed = _extract_json(content)
        for c in parsed.get("clauses", []):
            verified = validate_span(text, c.get("text"), 1500)
            if verified:
                clauses.append({
                    "clause_id": str(c.get("clause_id") or f"C{len(clauses) + 1}"),
                    "section": str(c.get("section") or "")[:120],
                    "text": verified,
                    "topic": _norm_topic(c.get("topic")),
                })
            else:
                dropped += 1
        for r in parsed.get("rules", []):
            verified = validate_span(text, r.get("rule"), 1500)
            if verified:
                rules.append({
                    "policy_id": str(r.get("policy_id") or f"POL-{len(rules) + 1}"),
                    "topic": _norm_topic(r.get("topic")),
                    "rule": verified,
                })
            else:
                dropped += 1
    return {"clauses": clauses, "rules": rules, "dropped": dropped,
            "chars": len(text)}
