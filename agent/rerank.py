from __future__ import annotations

import os


def apply_order(shortlist: list[str], proposed: list[str]) -> list[str]:
    allowed = set(shortlist)
    return [item for item in proposed if item in allowed]


def rerank(
    shortlist: list[str],
    message: str,
    slots: dict[str, str],
    api_key: str | None = None,
) -> list[str]:
    """Return shortlist order. Optional LLM path is fail-closed and unused here."""
    try:
        key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            return shortlist
        # No network call in this slice. Keep shortlist order and drop unknowns.
        return apply_order(shortlist, shortlist)
    except Exception:
        return shortlist
