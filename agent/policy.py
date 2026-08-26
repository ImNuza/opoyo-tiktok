from __future__ import annotations

from agent.state import SessionState

ASK = "ask"
RETRIEVE = "retrieve"

FIELD_ORDER: tuple[str, ...] = (
    "category",
    "budget",
    "brand",
    "size",
    "color",
    "material",
    "style",
    "feature",
    "use_case",
)

_HARD_CONSTRAINTS: frozenset[str] = frozenset(
    {"category", "brand", "budget", "size", "material", "color"}
)

_WEAK_KEYS: frozenset[str] = frozenset({"style", "feature", "use_case", "other"})


def _first_missing(state: SessionState) -> str | None:
    for field in FIELD_ORDER:
        if field in state.asked:
            continue
        if field in state.slots:
            continue
        return field
    return None


def _has_hard_constraint(state: SessionState) -> bool:
    return any(key in _HARD_CONSTRAINTS for key in state.slots)


def _is_empty_or_weak_only(state: SessionState) -> bool:
    if not state.slots:
        return True
    return all(key in _WEAK_KEYS for key in state.slots)


def decide(
    state: SessionState,
    turn: int,
    candidate_count: int | None = None,
) -> tuple[str, str | None]:
    if turn >= 10:
        return (RETRIEVE, None)

    if _has_hard_constraint(state):
        if isinstance(candidate_count, int) and candidate_count > 80:
            missing = _first_missing(state)
            if missing is not None:
                return (ASK, missing)
        return (RETRIEVE, None)

    if _is_empty_or_weak_only(state):
        missing = _first_missing(state)
        if missing is not None:
            return (ASK, missing)
        return (RETRIEVE, None)

    missing = _first_missing(state)
    if missing is not None:
        return (ASK, missing)
    return (RETRIEVE, None)
