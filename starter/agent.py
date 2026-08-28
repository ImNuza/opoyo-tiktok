from __future__ import annotations

from pathlib import Path

from agent.catalog import Catalog
from agent.policy import ASK, RETRIEVE, decide
from agent.rerank import rerank
from agent.retrieve import Retriever, build_query
from agent.slots import parse_slots
from agent.state import SessionState, apply_override, new_state


class Agent:
    """Policy C wrapper: slots + BM25 retrieve + fail-closed no-op rerank."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.catalog = Catalog(catalog_path)
        self.retriever = Retriever(self.catalog)
        self._sessions: dict[str, SessionState] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self._sessions[session_id] = new_state(session_id, user_profile or {})

    def respond(
        self,
        session_id: str,
        user_message: str,
        turn: int,
        top_k: int,
    ) -> dict:
        empty_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        fallback = {
            "message": "Here are the closest matches I found.",
            "ask_attribute": None,
            "recommendations": [],
            "usage": empty_usage,
        }
        try:
            if session_id not in self._sessions:
                self.reset(session_id, {})

            state = self._sessions[session_id]
            state.turn = turn

            parsed = parse_slots(user_message, profile=state.profile)
            for attr, value in parsed.items():
                current = state.slots.get(attr)
                if current is not None and current != value:
                    apply_override(state, attr, value)
                else:
                    state.slots[attr] = value

            query = build_query(user_message, state.slots)
            matched = self.retriever.search(query, limit=81)
            shortlist = matched[:50]
            ranked = rerank(shortlist, user_message, state.slots)

            action, attr = decide(state, turn, candidate_count=len(matched))

            ask_attribute: str | None = None
            if action == ASK and attr:
                state.asked.add(attr)
                ask_attribute = attr
                message = f"What {attr} are you looking for?"
            else:
                message = "Here are the closest matches I found."

            recommendations: list[dict] = []
            seen: set[str] = set()
            for parent_asin in ranked:
                if parent_asin in seen:
                    continue
                if not self.catalog.contains(parent_asin):
                    continue
                seen.add(parent_asin)
                recommendations.append({"parent_asin": parent_asin})
                if len(recommendations) >= top_k:
                    break
            if len(recommendations) < top_k:
                for parent_asin in self.catalog.products:
                    if parent_asin in seen:
                        continue
                    seen.add(parent_asin)
                    recommendations.append({"parent_asin": parent_asin})
                    if len(recommendations) >= top_k:
                        break

            return {
                "message": message,
                "ask_attribute": ask_attribute,
                "recommendations": recommendations,
                "usage": empty_usage,
            }
        except Exception:
            return fallback
