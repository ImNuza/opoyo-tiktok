# Track 4 BM25 plus Policy C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vendor the official Track 4 kit into `opoyo` and ship a working Agent that adds Policy C and session state on top of in-memory BM25, with a no-op DeepSeek rerank, without editing the evaluator.

**Architecture:** `starter/agent.py` stays the evaluator entry point and becomes a thin wrapper. Catalog, slots, policy, retrieve, and rerank live in `agent/`. Saturday baseline is BM25 plus Policy C. Local embeddings are out of this plan.

**Tech Stack:** Python 3.10+, stdlib only for this slice (sqlite FTS5 BM25, urllib for DeepSeek stub that is unused unless a key exists). pytest is not required; use `unittest`.

**Spec:** `docs/superpowers/specs/2026-08-26-track-4-shopping-copilot-design.md`

## Global Constraints

- Do not edit `evaluator/` or `data/public_set.jsonl`.
- Do not commit `.env`, `data/catalog.jsonl`, or `data/catalog.jsonl.gz`.
- Do not print API keys. Do not add `console.log`. No emojis in code. No em dashes in writing.
- `starter/agent.py` must export `class Agent` with `reset(self, session_id: str, user_profile: dict) -> None` and `respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict`.
- `ask_attribute` is one of `category`, `material`, `color`, `size`, `style`, `brand`, `budget`, `feature`, `use_case`, `other`, or `null`.
- Recommendations are `{"parent_asin": str}` dicts from the catalog only. Strip invalid and duplicate IDs. At most 10 unique valid IDs after stripping.
- Catalog missing: refuse to construct `Agent` with a clear error. Do not half-run.
- Fail closed inside `respond`: never raise after a successful `reset`. Timeouts and DeepSeek errors skip rerank.
- Turn 10 always RETRIEVE. `ask_attribute` is null.
- Always return catalog IDs when any slot is filled, including on ASK turns.
- DeepSeek must never be the source of ASINs. Drop any ID not in the local shortlist.
- Official starter scores to record, not to match after Policy C: Hit Rate@10 `0.125`, MRR `0.068034`, MTTC `9.81`.
- Python 3.10 or later. This slice uses the standard library plus nothing that requires a paid install.
- Work only in the isolated worktree this plan is executed from. Do not push. Do not commit secrets.

## File map

- Create: `agent/__init__.py`, `agent/catalog.py`, `agent/state.py`, `agent/slots.py`, `agent/policy.py`, `agent/retrieve.py`, `agent/rerank.py`
- Modify: `starter/agent.py` (wrapper only), `.gitignore` (merge kit ignore rules without dropping ours)
- Create: `tests/test_catalog.py`, `tests/test_state.py`, `tests/test_slots.py`, `tests/test_policy.py`, `tests/test_retrieve.py`, `tests/test_rerank.py`, `tests/test_agent_wrapper.py`
- Create: `docs/policy-table.md`, `docs/miss-log.md`
- Modify: `README.md` (keep kit instructions, add opoyo run notes and a Baseline scores heading)
- Do not modify: `evaluator/local_evaluator.py`, `tests/test_evaluator.py`, `data/public_set.jsonl`

### Task 1: Vendor the official kit and catalog

**Files:**
- Create (copied from kit, do not rewrite): `starter/__init__.py`, `evaluator/__init__.py`, `evaluator/local_evaluator.py`, `tests/__init__.py`, `tests/test_evaluator.py`, `data/README.md`, `data/public_set.jsonl`, `docs/agent_api_contract.json`, `docs/baseline_results.json`, `docs/competition_specification.md`, `docs/evaluation_config.json`, `docs/submission_rules.md`, `DATA_ATTRIBUTION.md`, kit `README.md` content merged as described below
- Create: `data/catalog.jsonl` on disk only (gitignored)
- Modify: `.gitignore`, `README.md`
- Keep: `.env.example`, `docs/superpowers/**`, `LICENSE`

**Interfaces:**
- Consumes: GitHub repo `TechJam2026/techjam-conversational-search` at `main`, release tag `participant-kit`
- Produces: kit files in the worktree; `data/catalog.jsonl` present; `SHA256SUMS` recorded in README

- [ ] **Step 1: Clone the kit to a temp dir and copy participant files**

```bash
git clone --depth 1 https://github.com/TechJam2026/techjam-conversational-search.git /tmp/techjam-kit
```

Copy these paths into the worktree root, creating directories as needed:

- `starter/__init__.py`
- `starter/agent.py` (temporary; Task 6 replaces it)
- `evaluator/__init__.py`
- `evaluator/local_evaluator.py`
- `tests/__init__.py`
- `tests/test_evaluator.py`
- `data/README.md`
- `data/public_set.jsonl`
- `docs/agent_api_contract.json`
- `docs/baseline_results.json`
- `docs/competition_specification.md`
- `docs/evaluation_config.json`
- `docs/submission_rules.md`
- `DATA_ATTRIBUTION.md`

Do not copy `.git`. Do not copy `organizer/` if present. Do not overwrite `docs/superpowers/`. Do not overwrite `.env.example`.

- [ ] **Step 2: Merge gitignore**

Keep every existing `opoyo` ignore rule. Add any kit rules that are missing. The file must still ignore `.env`, `data/catalog.jsonl`, `data/catalog.jsonl.gz`, `results.json`, `.venv/`, `venv/`, `__pycache__/`, `.worktrees/`.

- [ ] **Step 3: Download and verify the catalog**

```bash
mkdir -p data
curl -L -A "Mozilla/5.0 (compatible; DewaResearch/1.0)" \
  -o data/catalog.jsonl.gz \
  https://github.com/TechJam2026/techjam-conversational-search/releases/download/participant-kit/catalog.jsonl.gz
curl -L -A "Mozilla/5.0 (compatible; DewaResearch/1.0)" \
  -o /tmp/SHA256SUMS \
  https://github.com/TechJam2026/techjam-conversational-search/releases/download/participant-kit/SHA256SUMS
cd data && shasum -a 256 catalog.jsonl.gz
```

Expected SHA256 of `catalog.jsonl.gz`:

`07fd142631fd6b03e2b4d09988c3eb7d53720e9d57010c79db48eeaada50a8f8`

Then:

```bash
gzip -dk catalog.jsonl.gz
# result: data/catalog.jsonl
python3 -c "print(sum(1 for _ in open('data/catalog.jsonl', encoding='utf-8')))"
```

Expected row count: 50000.

Do not `git add` `data/catalog.jsonl` or `data/catalog.jsonl.gz`.

- [ ] **Step 4: Merge README**

Keep the official kit README content. Add an `## Opoyo` section at the top (after the title) with:

- This repo is the SMU team fork for Track 4.
- Copy `.env.example` to `.env`. Never commit `.env`.
- Download catalog steps (already in the kit README).
- Run tests: `python3 -m unittest discover -s tests -v`
- Run evaluator: `python3 -m evaluator.local_evaluator`
- A `## Baseline scores` heading that records the official starter numbers (Hit Rate@10 0.125, MRR 0.068034, MTTC 9.81) and a line `Opoyo BM25+policy: not yet measured`.

- [ ] **Step 5: Prove the kit tests still pass**

```bash
python3 -m unittest tests.test_evaluator -v
```

Expected: PASS (these tests use a tiny temp catalog, not the 50k file).

- [ ] **Step 6: Commit**

```bash
git add starter evaluator tests data/README.md data/public_set.jsonl \
  docs/agent_api_contract.json docs/baseline_results.json \
  docs/competition_specification.md docs/evaluation_config.json \
  docs/submission_rules.md DATA_ATTRIBUTION.md README.md .gitignore
git status
# confirm data/catalog.jsonl is NOT staged
git commit -m "Vendor TechJam Track 4 participant kit."
```

### Task 2: Catalog loader

**Files:**
- Create: `agent/__init__.py`, `agent/catalog.py`
- Test: `tests/test_catalog.py`

**Interfaces:**
- Consumes: a JSONL path of catalog rows with `parent_asin`
- Produces:
  - `class CatalogError(Exception)`
  - `class Catalog` with:
    - `def __init__(self, path: str | Path) -> None`
    - `ids: set[str]`
    - `products: dict[str, dict]`
    - `def get(self, parent_asin: str) -> dict | None`
    - `def contains(self, parent_asin: str) -> bool`
  - Missing file or empty file raises `CatalogError` with a message that includes the path.

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.catalog import Catalog, CatalogError


class CatalogTest(unittest.TestCase):
    def _write(self, rows: list[dict]) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        for row in rows:
            handle.write(json.dumps(row) + "\n")
        handle.close()
        return Path(handle.name)

    def test_indexes_by_parent_asin(self) -> None:
        path = self._write([
            {"parent_asin": "A", "title": "Blue shoe"},
            {"parent_asin": "B", "title": "Red hat"},
        ])
        catalog = Catalog(path)
        self.assertEqual(catalog.ids, {"A", "B"})
        self.assertEqual(catalog.get("A")["title"], "Blue shoe")
        self.assertTrue(catalog.contains("A"))
        self.assertFalse(catalog.contains("Z"))

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(CatalogError) as ctx:
            Catalog("/tmp/does-not-exist-opoyo-catalog.jsonl")
        self.assertIn("does-not-exist-opoyo-catalog.jsonl", str(ctx.exception))

    def test_empty_file_raises(self) -> None:
        path = self._write([])
        with self.assertRaises(CatalogError):
            Catalog(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m unittest tests.test_catalog -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `agent.catalog`.

- [ ] **Step 3: Write minimal implementation**

`agent/__init__.py` can be empty or export `Catalog`.

`agent/catalog.py`:

```python
from __future__ import annotations

import json
from pathlib import Path


class CatalogError(Exception):
    pass


class Catalog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise CatalogError(f"catalog file is missing: {self.path}")
        products: dict[str, dict] = {}
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                products[str(row["parent_asin"])] = row
        if not products:
            raise CatalogError(f"catalog file is empty: {self.path}")
        self.products = products
        self.ids = set(products)

    def get(self, parent_asin: str) -> dict | None:
        return self.products.get(parent_asin)

    def contains(self, parent_asin: str) -> bool:
        return parent_asin in self.products
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest tests.test_catalog -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/__init__.py agent/catalog.py tests/test_catalog.py
git commit -m "Add catalog loader that refuses a missing file."
```

### Task 3: Session state and rule-based slots

**Files:**
- Create: `agent/state.py`, `agent/slots.py`
- Test: `tests/test_state.py`, `tests/test_slots.py`

**Interfaces:**
- Consumes: none
- Produces:
  - `ALLOWED_ATTRIBUTES: tuple[str, ...] = ("category", "material", "color", "size", "style", "brand", "budget", "feature", "use_case", "other")`
  - `class SessionState` with fields: `session_id: str`, `profile: dict`, `slots: dict[str, str]`, `asked: set[str]`, `turn: int`
  - `def new_state(session_id: str, profile: dict) -> SessionState`
  - `def apply_override(state: SessionState, attribute: str, value: str) -> None` which replaces `slots[attribute]` if the new value differs (case-insensitive), and removes `attribute` from `asked` so Policy C may ask it again
  - `def parse_slots(message: str, profile: dict | None = None) -> dict[str, str]` using rules only (no network)
  - Color words: black, white, blue, red, pink, green, brown, gray, grey, purple, yellow, orange
  - Material words: cotton, polyester, nylon, leather, wool, spandex, silk, rayon, fabric
  - Size tokens: `xs`, `s`, `m`, `l`, `xl`, `xxl`, and patterns like `size 8`, `size 10`
  - Budget: `$` amounts or `under 50` / `under $50`
  - Brand: `preference_tags` from profile that are not color/material words, plus `by <Name>` in the message
  - Category: leftover noun phrases are not required this task. If the message contains `shoes`, `boots`, `dress`, `jacket`, `shirt`, `hat`, `jeans`, `sneakers`, set `category` to that word.

- [ ] **Step 1: Write the failing tests**

`tests/test_state.py`:

```python
from __future__ import annotations

import unittest

from agent.state import apply_override, new_state


class StateTest(unittest.TestCase):
    def test_new_state_is_empty(self) -> None:
        state = new_state("s1", {"summary": "x"})
        self.assertEqual(state.slots, {})
        self.assertEqual(state.asked, set())
        self.assertEqual(state.profile["summary"], "x")

    def test_override_erases_old_slot_and_allows_reask(self) -> None:
        state = new_state("s1", {})
        state.slots["color"] = "red"
        state.asked.add("color")
        apply_override(state, "color", "blue")
        self.assertEqual(state.slots["color"], "blue")
        self.assertNotIn("color", state.asked)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_slots.py`:

```python
from __future__ import annotations

import unittest

from agent.slots import parse_slots


class SlotsTest(unittest.TestCase):
    def test_parses_color_and_material(self) -> None:
        slots = parse_slots("I want a red leather jacket")
        self.assertEqual(slots.get("color"), "red")
        self.assertEqual(slots.get("material"), "leather")
        self.assertEqual(slots.get("category"), "jacket")

    def test_parses_budget(self) -> None:
        slots = parse_slots("looking for boots under $50")
        self.assertEqual(slots.get("budget"), "50")
        self.assertEqual(slots.get("category"), "boots")

    def test_uses_profile_tags_as_brand_prior(self) -> None:
        slots = parse_slots("need shoes", {"preference_tags": ["Nike", "red"]})
        self.assertEqual(slots.get("brand"), "Nike")
        self.assertEqual(slots.get("category"), "shoes")

    def test_empty_message(self) -> None:
        self.assertEqual(parse_slots(""), {})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m unittest tests.test_state tests.test_slots -v
```

Expected: FAIL with import errors.

- [ ] **Step 3: Write minimal implementation**

Keep parsers as simple regexes. `apply_override` compares lowercased strings and no-ops if equal.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest tests.test_state tests.test_slots -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/state.py agent/slots.py tests/test_state.py tests/test_slots.py
git commit -m "Add session state and rule-based slot parsing."
```

### Task 4: Policy C

**Files:**
- Create: `agent/policy.py`
- Test: `tests/test_policy.py`

**Interfaces:**
- Consumes: `SessionState` from `agent.state` (`slots`, `asked`, `turn`)
- Produces:
  - `ASK = "ask"`
  - `RETRIEVE = "retrieve"`
  - `FIELD_ORDER: tuple[str, ...] = ("category", "budget", "brand", "size", "color", "material", "style", "feature", "use_case")`
  - `def decide(state: SessionState, turn: int, candidate_count: int | None = None) -> tuple[str, str | None]`
    - Returns `(RETRIEVE, None)` or `(ASK, attribute)`
  - Rules, in this order:
    1. If `turn >= 10`: `(RETRIEVE, None)`
    2. If `slots` has a hard constraint (`category` or `brand` or `budget` or `size` or `material` or `color`): `(RETRIEVE, None)` unless `candidate_count` is an int greater than 80 and there is a missing field in `FIELD_ORDER` not in `asked` and not in `slots`, in which case `(ASK, that field)`
    3. If `slots` is empty or only weak keys (`style`, `feature`, `use_case`, `other`): ASK the first `FIELD_ORDER` item not in `asked` and not in `slots`. If none remain, `(RETRIEVE, None)`
    4. Never choose an attribute in `asked`
    5. If nothing to ask: `(RETRIEVE, None)`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import unittest

from agent.policy import ASK, RETRIEVE, decide
from agent.state import new_state


class PolicyTest(unittest.TestCase):
    def test_turn_10_always_retrieves(self) -> None:
        state = new_state("s", {})
        action, attr = decide(state, turn=10)
        self.assertEqual(action, RETRIEVE)
        self.assertIsNone(attr)

    def test_buying_hard_constraint_retrieves(self) -> None:
        state = new_state("s", {})
        state.slots["color"] = "red"
        action, attr = decide(state, turn=1)
        self.assertEqual(action, RETRIEVE)
        self.assertIsNone(attr)

    def test_browsing_vague_asks_category(self) -> None:
        state = new_state("s", {})
        action, attr = decide(state, turn=1)
        self.assertEqual(action, ASK)
        self.assertEqual(attr, "category")

    def test_does_not_reask(self) -> None:
        state = new_state("s", {})
        state.asked.add("category")
        action, attr = decide(state, turn=2)
        self.assertEqual(action, ASK)
        self.assertEqual(attr, "budget")

    def test_huge_pool_asks_missing_field(self) -> None:
        state = new_state("s", {})
        state.slots["color"] = "red"
        action, attr = decide(state, turn=2, candidate_count=200)
        self.assertEqual(action, ASK)
        self.assertEqual(attr, "category")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m unittest tests.test_policy -v
```

Expected: FAIL with import error.

- [ ] **Step 3: Write minimal implementation matching the rule order above**

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest tests.test_policy -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/policy.py tests/test_policy.py
git commit -m "Add Policy C ask versus retrieve table."
```

### Task 5: BM25 retrieve

**Files:**
- Create: `agent/retrieve.py`
- Test: `tests/test_retrieve.py`

**Interfaces:**
- Consumes: `Catalog` and a query string built from slots plus the latest message
- Produces:
  - `def build_query(message: str, slots: dict[str, str]) -> str` joining unique non-empty slot values and the message
  - `class Retriever` with:
    - `def __init__(self, catalog: Catalog) -> None` building an in-memory sqlite FTS5 table the same way as the official starter (`unicode61 remove_diacritics 2`, columns `parent_asin UNINDEXED, title, categories, features, details, store, description`)
    - `def search(self, query: str, limit: int = 50) -> list[str]` returning `parent_asin` strings in BM25 order
  - Empty query returns `[]`
  - IDs not in `catalog.ids` never appear

Reuse the starter tokenization idea: alphanumeric tokens length greater than 1, drop the same STOPWORDS set as `starter/agent.py` in the kit. MATCH expression is `OR`-joined quoted terms, capped at 40 unique terms.

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.catalog import Catalog
from agent.retrieve import Retriever, build_query


def write_catalog(rows: list[dict]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for row in rows:
        handle.write(json.dumps(row) + "\n")
    handle.close()
    return Path(handle.name)


class RetrieveTest(unittest.TestCase):
    def setUp(self) -> None:
        path = write_catalog([
            {
                "parent_asin": "A",
                "title": "Blue running shoe",
                "categories": ["Shoes"],
                "features": ["mesh"],
                "details": {},
                "store": "Example",
                "description": "light running shoe",
            },
            {
                "parent_asin": "B",
                "title": "Black winter boot",
                "categories": ["Boots"],
                "features": ["leather"],
                "details": {},
                "store": "Example",
                "description": "warm boot",
            },
        ])
        self.catalog = Catalog(path)
        self.retriever = Retriever(self.catalog)

    def test_title_fragment_ranks_matching_product(self) -> None:
        ids = self.retriever.search("blue running shoe", limit=10)
        self.assertGreaterEqual(len(ids), 1)
        self.assertEqual(ids[0], "A")
        self.assertTrue(set(ids) <= self.catalog.ids)

    def test_empty_query_returns_empty(self) -> None:
        self.assertEqual(self.retriever.search("", limit=10), [])

    def test_build_query_includes_slots(self) -> None:
        q = build_query("need this", {"color": "red", "category": "jacket"})
        self.assertIn("red", q)
        self.assertIn("jacket", q)
        self.assertIn("need this", q)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m unittest tests.test_retrieve -v
```

Expected: FAIL with import error.

- [ ] **Step 3: Write minimal implementation** using sqlite FTS5 BM25 like the kit starter. Build the index from `catalog.products.values()`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest tests.test_retrieve -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/retrieve.py tests/test_retrieve.py
git commit -m "Add in-memory BM25 retrieval over the catalog."
```

### Task 6: No-op rerank, Agent wrapper, contract tests

**Files:**
- Create: `agent/rerank.py`
- Modify: `starter/agent.py` (replace the kit class with a wrapper)
- Test: `tests/test_rerank.py`, `tests/test_agent_wrapper.py`

**Interfaces:**
- Consumes: `Catalog`, `Retriever`, `parse_slots`, `new_state`, `apply_override`, `decide`, catalog path default `data/catalog.jsonl`
- Produces:
  - `def rerank(shortlist: list[str], message: str, slots: dict[str, str], api_key: str | None = None) -> list[str]`
    - If `api_key` is None or empty, return `shortlist` unchanged
    - If a stub/test sets `RERANK_OVERRIDE` later, still drop IDs not in `shortlist`
    - Never call the network in unit tests. Implementation may read `os.environ.get("DEEPSEEK_API_KEY")` but must catch all exceptions and return the original shortlist
  - `class Agent` in `starter/agent.py`:
    - `__init__(self, catalog_path: str | Path = "data/catalog.jsonl")` loads `Catalog` (raises `CatalogError` if missing) and `Retriever`
    - `reset` creates `SessionState` in `self._sessions: dict[str, SessionState]`
    - `respond`:
      1. If session missing, call `reset` with empty profile rather than raising (fail closed)
      2. Parse slots from the message plus profile; for each parsed attribute, if state already has a different value call `apply_override`, else set the slot
      3. `query = build_query(user_message, state.slots)`
      4. `shortlist = retriever.search(query, limit=50)`
      5. `ranked = rerank(shortlist, user_message, state.slots)`
      6. `action, attr = decide(state, turn, candidate_count=len(shortlist))`
      7. If action is ASK and attr: add attr to `state.asked`; message is a short question naming that field
      8. If action is RETRIEVE: `attr` is None; message is `"Here are the closest matches I found."`
      9. Recommendations: first `top_k` IDs from `ranked` that `catalog.contains`, unique, as `{"parent_asin": id}`
      10. Wrap the body in try/except. On unexpected error return empty recommendations, `ask_attribute` None, message `"Here are the closest matches I found."`, usage zeros
      11. `usage` is `{"prompt_tokens": 0, "completion_tokens": 0}` in this slice
    - Always attach recommendations when `state.slots` is non-empty, even on ASK turns (search already ran)

- [ ] **Step 1: Write the failing tests**

`tests/test_rerank.py`:

```python
from __future__ import annotations

import unittest

from agent.rerank import rerank


class RerankTest(unittest.TestCase):
    def test_no_key_returns_local_order(self) -> None:
        ids = ["A", "B", "C"]
        self.assertEqual(rerank(ids, "hello", {"color": "red"}, api_key=None), ids)

    def test_drops_ids_not_in_shortlist(self) -> None:
        ids = ["A", "B"]
        # even if a future LLM returns junk, public function must not introduce it
        self.assertEqual(rerank(ids, "hello", {}, api_key=""), ids)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_agent_wrapper.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starter.agent import Agent


ALLOWED = {
    "category", "material", "color", "size", "style", "brand",
    "budget", "feature", "use_case", "other", None,
}


def write_catalog(rows: list[dict]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for row in rows:
        handle.write(json.dumps(row) + "\n")
    handle.close()
    return Path(handle.name)


class AgentWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        path = write_catalog([
            {
                "parent_asin": "A",
                "title": "Blue running shoe",
                "categories": ["Shoes"],
                "features": ["mesh"],
                "details": {},
                "store": "Example",
                "description": "light running shoe",
            },
            {
                "parent_asin": "B",
                "title": "Black winter boot",
                "categories": ["Boots"],
                "features": ["leather"],
                "details": {},
                "store": "Example",
                "description": "warm boot",
            },
        ])
        self.agent = Agent(path)

    def test_missing_catalog_raises(self) -> None:
        from agent.catalog import CatalogError
        with self.assertRaises(CatalogError):
            Agent("/tmp/missing-opoyo-catalog.jsonl")

    def test_contract_keys_and_ask_attribute(self) -> None:
        self.agent.reset("s1", {"preference_tags": [], "summary": "x"})
        out = self.agent.respond("s1", "hi", turn=1, top_k=10)
        self.assertIn("message", out)
        self.assertIn("ask_attribute", out)
        self.assertIn("recommendations", out)
        self.assertIn(out["ask_attribute"], ALLOWED)
        for row in out["recommendations"]:
            self.assertIn("parent_asin", row)
            self.assertIn(row["parent_asin"], {"A", "B"})

    def test_buying_returns_ids_and_does_not_ask(self) -> None:
        self.agent.reset("s1", {})
        out = self.agent.respond("s1", "I want a blue running shoe", turn=1, top_k=10)
        self.assertIsNone(out["ask_attribute"])
        self.assertGreaterEqual(len(out["recommendations"]), 1)
        self.assertEqual(out["recommendations"][0]["parent_asin"], "A")

    def test_turn_10_never_asks(self) -> None:
        self.agent.reset("s1", {})
        out = self.agent.respond("s1", "hi", turn=10, top_k=10)
        self.assertIsNone(out["ask_attribute"])

    def test_override_switches_color_slot(self) -> None:
        self.agent.reset("s1", {})
        self.agent.respond("s1", "red leather jacket", turn=1, top_k=10)
        out = self.agent.respond("s1", "actually I want black boots", turn=4, top_k=10)
        self.assertEqual(self.agent._sessions["s1"].slots.get("color"), "black")
        asins = [row["parent_asin"] for row in out["recommendations"]]
        self.assertTrue(set(asins) <= {"A", "B"})

    def test_respond_without_reset_does_not_raise(self) -> None:
        out = self.agent.respond("ghost", "blue shoe", turn=1, top_k=10)
        self.assertIn("recommendations", out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m unittest tests.test_rerank tests.test_agent_wrapper -v
```

Expected: FAIL (wrapper still the kit class or imports missing).

- [ ] **Step 3: Implement `agent/rerank.py` and replace `starter/agent.py` with the wrapper.** Keep `from starter.agent import Agent` working for the evaluator. Do not edit `evaluator/local_evaluator.py`.

- [ ] **Step 4: Run focused tests, then the full suite**

```bash
python3 -m unittest tests.test_rerank tests.test_agent_wrapper -v
python3 -m unittest discover -s tests -v
```

Expected: PASS, including `tests.test_evaluator`.

- [ ] **Step 5: Commit**

```bash
git add agent/rerank.py starter/agent.py tests/test_rerank.py tests/test_agent_wrapper.py
git commit -m "Wire Policy C Agent wrapper with fail-closed rerank."
```

### Task 7: Policy table, miss log, README baseline line

**Files:**
- Create: `docs/policy-table.md`, `docs/miss-log.md`
- Modify: `README.md` (Baseline scores section only)

**Interfaces:**
- Consumes: Policy C rules from Task 4
- Produces: human-readable table SOB/SOA can edit; empty miss log with a header; README still says `Opoyo BM25+policy: not yet measured` unless the implementer ran the full 200 (optional, do not block on the 50k evaluator if it takes too long)

- [ ] **Step 1: Write `docs/policy-table.md`** with a markdown table matching Task 4 rule order (turn 10 retrieve, hard constraint retrieve, vague ask category then budget, no re-ask, huge pool asks next missing field). State that rows CS cannot code get dropped.

- [ ] **Step 2: Write `docs/miss-log.md`** with heading `Miss log` and a short how-to: after `python3 -m evaluator.local_evaluator`, pick 5 misses from `results.json` and append one line each (`session_id`, scenario if present, what the shopper meant, router or retrieval). No sample fake sessions.

- [ ] **Step 3: Do not run the 200-session evaluator unless catalog is present and time is under a few minutes.** If you do run it, paste Hit Rate / MRR / MTTC into README under `Opoyo BM25+policy`. If you skip it, leave `not yet measured`.

- [ ] **Step 4: Commit**

```bash
git add docs/policy-table.md docs/miss-log.md README.md
git commit -m "Add policy table and miss log for non-tech labeling."
```
