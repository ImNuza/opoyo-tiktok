from __future__ import annotations

from dataclasses import dataclass, field


ALLOWED_ATTRIBUTES: tuple[str, ...] = (
    "category",
    "material",
    "color",
    "size",
    "style",
    "brand",
    "budget",
    "feature",
    "use_case",
    "other",
)


@dataclass
class SessionState:
    session_id: str
    profile: dict
    slots: dict[str, str] = field(default_factory=dict)
    asked: set[str] = field(default_factory=set)
    last_asked: str | None = None
    turn: int = 0


def new_state(session_id: str, profile: dict) -> SessionState:
    return SessionState(session_id=session_id, profile=profile)


def apply_override(state: SessionState, attribute: str, value: str) -> None:
    current = state.slots.get(attribute)
    if current is not None and current.lower() == value.lower():
        return
    state.slots[attribute] = value
    state.asked.discard(attribute)


def clear_intent(state: SessionState) -> None:
    state.slots.clear()
    state.asked.clear()
    state.last_asked = None
