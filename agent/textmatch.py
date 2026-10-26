"""Verbatim-span validation shared by the claim check and extraction."""


def validate_span(text: str | None, span: object, limit: int = 160) -> str | None:
    """Keep a copied span only if it is verbatim inside `text`.

    Whitespace runs are collapsed on both sides before the case-insensitive
    substring test; the returned value is sliced from the (normalized)
    original text so callers always show source wording.
    """
    if not text or not isinstance(span, str) or not span.strip():
        return None
    t_norm = " ".join(text.split())
    s_norm = " ".join(span.split())
    if len(s_norm) > limit:
        return None
    idx = t_norm.lower().find(s_norm.lower())
    if idx < 0:
        return None
    return t_norm[idx : idx + len(s_norm)]
