from __future__ import annotations

import os
from typing import Any

_ENCODER: Any = None
_ENCODER_FAILED = False
_MODEL_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def apply_order(shortlist: list[str], proposed: list[str]) -> list[str]:
    allowed = set(shortlist)
    return [item for item in proposed if item in allowed]


def _query_text(message: str, slots: dict[str, str]) -> str:
    parts = [value for value in slots.values() if value]
    if message:
        parts.append(message)
    return " ".join(parts).strip() or message


def _local_rerank(
    shortlist: list[str],
    message: str,
    slots: dict[str, str],
    texts: dict[str, str],
) -> list[str] | None:
    global _ENCODER, _ENCODER_FAILED
    if _ENCODER_FAILED or len(shortlist) < 2:
        return None
    query = _query_text(message, slots)
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
    ranked = [item for _, item in sorted(zip(scores, keep, strict=True), key=lambda row: (-float(row[0]), keep.index(row[1])))]
    return ranked


def rerank(
    shortlist: list[str],
    message: str,
    slots: dict[str, str],
    api_key: str | None = None,
    texts: dict[str, str] | None = None,
) -> list[str]:
    """Return shortlist order. Local MiniLM is fail-closed. DeepSeek unused."""
    try:
        if os.environ.get("OPOYO_NO_MINILM", "").strip() in {"1", "true", "yes"}:
            return shortlist
        if texts:
            local = _local_rerank(shortlist, message, slots, texts)
            if local:
                return apply_order(shortlist, local)
        key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            return shortlist
        return apply_order(shortlist, shortlist)
    except Exception:
        global _ENCODER_FAILED
        _ENCODER_FAILED = True
        return shortlist
