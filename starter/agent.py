from __future__ import annotations

from pathlib import Path

from agent.catalog import Catalog
from agent.policy import ASK, RETRIEVE, decide
from agent.rerank import rerank
from agent.retrieve import Retriever, build_query
from agent.slots import HARD_CONSTRAINTS, WEAK_FILL, parse_slots, preference_snippet
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
            if (
                state.last_asked in WEAK_FILL
                and state.last_asked not in parsed
            ):
                snippet = preference_snippet(user_message)
                if snippet:
                    parsed[state.last_asked] = snippet
            for attr, value in parsed.items():
                current = state.slots.get(attr)
                if current is not None and current != value:
                    apply_override(state, attr, value)
                else:
                    state.slots[attr] = value

            tags = [
                str(tag)
                for tag in (state.profile.get("preference_tags") or [])
                if tag
            ]
            query = build_query(user_message, state.slots, extra=tags)
            matched = self.retriever.search(
                query,
                limit=81,
                required=[
                    value
                    for key, value in state.slots.items()
                    if key in HARD_CONSTRAINTS
                ],
            )
            shortlist = matched[:50]
            texts: dict[str, str] = {}
            for parent_asin in shortlist:
                product = self.catalog.get(parent_asin) or {}
                title = str(product.get("title") or "")
                features = product.get("features")
                feat = " ".join(str(item) for item in features) if isinstance(features, list) else str(features or "")
                texts[parent_asin] = f"{title} {feat}".strip()
            ranked = rerank(shortlist, user_message, state.slots, texts=texts)

            action, attr = decide(state, turn, candidate_count=len(matched))

            ask_attribute: str | None = None
            if action == ASK and attr:
                state.asked.add(attr)
                state.last_asked = attr
                ask_attribute = attr
                message = f"What {attr} are you looking for?"
            else:
                state.last_asked = None
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
