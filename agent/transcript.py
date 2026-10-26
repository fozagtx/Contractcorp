"""Transcript parsing: turn a pasted or uploaded call transcript into
the rep's claim lines, one per line, ready for check_claim.

Handles the shapes a real transcript arrives in:
  - plain lines (one claim per line, no labels)
  - timestamps: "14:32 we can do 10% off" or "[14:32:07] we can do 10% off"
  - speaker labels: "Rep: ...", "Rep - ...", "Sales rep: ...",
    "Customer: ...", "Prospect: ..." (only rep-side lines are claims)

If any speaker labels are present, only rep-side lines are kept; if none
are, every non-empty line is treated as something the rep said.
"""
import re

_TIMESTAMP = re.compile(r"^\s*(?:\[)?\d{1,2}:\d{2}(?::\d{2})?(?:\])?\s*[-–]?\s*")
_SPEAKER = re.compile(r"^\s*([A-Za-z][A-Za-z ']{0,20}?)\s*[:\-–]\s+")
REP_LABELS = {"rep", "sales rep", "sales", "me", "seller", "agent", "us", "ae"}
CUSTOMER_LABELS = {"customer", "client", "prospect", "buyer", "them", "lead", "caller"}


def _strip_timestamp(line: str) -> str:
    return _TIMESTAMP.sub("", line).strip()


def _split_speaker(line: str) -> tuple[str | None, str]:
    match = _SPEAKER.match(line)
    if not match:
        return None, line
    return match.group(1).strip().lower(), line[match.end():].strip()


def parse_transcript(text: str) -> list[str]:
    """Returns the rep's claim lines, in call order, stripped of noise."""
    claims = []
    labeled = False
    for raw in text.splitlines():
        line = _strip_timestamp(raw)
        if not line:
            continue
        speaker, content = _split_speaker(line)
        if speaker is not None:
            labeled = True
            if speaker in CUSTOMER_LABELS or speaker not in REP_LABELS:
                continue
            line = content
        if line:
            claims.append(line)
    # second pass safety: if labels were present but nothing matched the
    # rep side (an all-moderator transcript, say), fall back to every
    # non-empty line with labels stripped, rather than returning []
    if labeled and not claims:
        fallback = []
        for raw in text.splitlines():
            line = _strip_timestamp(raw)
            if not line:
                continue
            _, content = _split_speaker(line)
            if content or line:
                fallback.append(content or line)
        return fallback
    return claims
