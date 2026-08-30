from __future__ import annotations

from agent.router import BROWSING
from agent.state import SessionState

ASK = "ask"
RETRIEVE = "retrieve"

# Simulator-answerable fields only. classify_constraint never returns
# category or brand, so asking those burns a turn.
FIELD_ORDER: tuple[str, ...] = (
    "material",
    "color",
    "use_case",
    "feature",
    "style",
    "size",
    "budget",
)

_HARD_CONSTRAINTS: frozenset[str] = frozenset(
    {"category", "brand", "budget", "size", "material", "color"}
)

_WEAK_KEYS: frozenset[str] = frozenset({"style", "feature", "use_case", "other"})


def _missing_fields(state: SessionState) -> list[str]:
    missing: list[str] = []
    for field in FIELD_ORDER:
        if field in state.asked:
            continue
        if field in state.slots:
            continue
        missing.append(field)
    return missing


def _best_ask(
    state: SessionState,
    pool_attrs: dict[str, set[str]] | None = None,
) -> str | None:
    missing = _missing_fields(state)
    if not missing:
        return None
    if pool_attrs:
        scored: list[tuple[int, int, str]] = []
        for index, field in enumerate(missing):
            values = {
                str(value).lower()
                for value in (pool_attrs.get(field) or set())
                if value
            }
            if len(values) >= 2:
                scored.append((-len(values), index, field))
        if scored:
            scored.sort()
            return scored[0][2]
    return missing[0]


def _has_hard_constraint(state: SessionState) -> bool:
    return any(key in _HARD_CONSTRAINTS for key in state.slots)


def _only_category_hard(state: SessionState) -> bool:
    hard_keys = [key for key in state.slots if key in _HARD_CONSTRAINTS]
    return bool(hard_keys) and all(key == "category" for key in hard_keys)


def _is_empty_or_weak_only(state: SessionState) -> bool:
    if not state.slots:
        return True
    return all(key in _WEAK_KEYS for key in state.slots)


def decide(
    state: SessionState,
    turn: int,
    candidate_count: int | None = None,
    pool_attrs: dict[str, set[str]] | None = None,
    track: str | None = None,
) -> tuple[str, str | None]:
    if turn >= 10:
        return (RETRIEVE, None)

    hard = _has_hard_constraint(state)
    if track == BROWSING and _only_category_hard(state):
        hard = False

    if hard:
        if isinstance(candidate_count, int) and candidate_count > 80:
            missing = _best_ask(state, pool_attrs)
            if missing is not None:
                return (ASK, missing)
        return (RETRIEVE, None)

    if _is_empty_or_weak_only(state) or (track == BROWSING and _only_category_hard(state)):
        missing = _best_ask(state, pool_attrs)
        if missing is not None:
            return (ASK, missing)
        return (RETRIEVE, None)

    missing = _best_ask(state, pool_attrs)
    if missing is not None:
        return (ASK, missing)
    return (RETRIEVE, None)
