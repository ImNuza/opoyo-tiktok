from __future__ import annotations

import re
from typing import Any

_ENCODER: Any = None
_ENCODER_FAILED = False
_MODEL_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_NOISE_RES = (
    re.compile(r"i['’]?m looking for\s+", re.I),
    re.compile(r",?\s*but i['’]?m still exploring\.?", re.I),
    re.compile(r"a key requirement is:\s*", re.I),
    re.compile(r"those options are not quite right yet\.?", re.I),
    re.compile(r"ask me about one specific attribute\.?", re.I),
    re.compile(r"for that, what matters is:\s*", re.I),
    re.compile(r"i don['’]?t have (an additional |a )?preference for \w+[.;,]?", re.I),
    re.compile(r"please use your judgment\.?", re.I),
    re.compile(r"actually,?\s+ignore my earlier preference\.?", re.I),
    re.compile(r"what i need is:\s*", re.I),
)


def apply_order(shortlist: list[str], proposed: list[str]) -> list[str]:
    allowed = set(shortlist)
    return [item for item in proposed if item in allowed]


def clean_query_text(message: str, slots: dict[str, str]) -> str:
    text = message or ""
    for pattern in _NOISE_RES:
        text = pattern.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip(" .;,-")
    parts = [value for value in slots.values() if value]
    if text:
        key = text.lower()
        if key not in {value.lower() for value in parts}:
            parts.append(text)
    return " ".join(parts).strip() or (message or "")


def _local_rerank(
    shortlist: list[str],
    message: str,
    slots: dict[str, str],
    texts: dict[str, str],
) -> list[str] | None:
    global _ENCODER, _ENCODER_FAILED
    if _ENCODER_FAILED or len(shortlist) < 2:
        return None
    query = clean_query_text(message, slots)
    if not query:
        return None
    pairs: list[tuple[str, str]] = []
    keep: list[str] = []
    for parent_asin in shortlist:
        body = (texts.get(parent_asin) or "").strip()
        if not body:
            continue
        pairs.append((query, body[:512]))
        keep.append(parent_asin)
    if len(keep) < 2:
        return None
    if _ENCODER is None:
        from sentence_transformers import CrossEncoder

        _ENCODER = CrossEncoder(_MODEL_ID)
    scores = _ENCODER.predict(pairs)
    ranked = [
        item
        for _, item in sorted(
            zip(scores, keep, strict=True),
            key=lambda row: (-float(row[0]), keep.index(row[1])),
        )
    ]
    return ranked


def rerank(
    shortlist: list[str],
    message: str,
    slots: dict[str, str],
    api_key: str | None = None,
    texts: dict[str, str] | None = None,
) -> list[str]:
    """Return shortlist order. Local MiniLM is fail-closed."""
    try:
        if texts:
            local = _local_rerank(shortlist, message, slots, texts)
            if local:
                return apply_order(shortlist, local)
        return shortlist
    except Exception:
        global _ENCODER_FAILED
        _ENCODER_FAILED = True
        return shortlist
