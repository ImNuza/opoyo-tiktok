# Lexical pass (this session)

Public-200, **MiniLM off**, BM25 limit **81**, shortlist 50. Frozen numbers: `docs/opoyo_public200_lexical.json`.

Reproduce:

```powershell
$env:OPOYO_NO_MINILM = "1"
.\venv\Scripts\python.exe -m evaluator.local_evaluator
```

(`OPOYO_NO_MINILM` is optional here: this venv has no torch, so MiniLM is already fail-closed.)

## Scores

| | Hit@10 | MRR | MTTC | Tech |
|--|--------|-----|------|------|
| MiniLM-off before this pass | 0.645 | 0.407 | 7.53 | 0.514 |
| After crumb / hypernym / no budget AND | 0.695 | 0.404 | 6.96 | 0.550 |
| **+ last noun in crumb (current)** | **0.715** | 0.406 | **6.87** | **0.562** |
| Historical MiniLM-on floor (`docs/opoyo_public200.json`) | 0.77 | 0.457 | 6.78 | 0.607 |

Scenario Hit@10 now: browsing 0.763, buying 0.713, boundary 0.90, intent_override 0.533 (unchanged).

## What landed (keep)

Scoring path is still Policy C + FTS5 BM25 `limit=81` + MiniLM shortlist 50. Changes are intent → query only.

1. **Crumb parse + last noun** (`agent/slots.py`)  
   Simulator first messages are `I'm looking for {coarse_category}…`. Category is the **last** `_CATEGORY_WORDS` hit in that crumb (`Tees & Blouses T-Shirts` → `shirts`, not `blouses`). If no noun matches, the crumb string becomes `category`. No extra clothing gazetteer from public titles.

2. **Hypernym / crumb AND** (`agent/retrieve.py` `and_required_terms`)  
   Hard-slot tokens used to all be AND-ed. `shoes` / `women` / `men` / `clothing` (and plurals) are no longer required MATCH; they stay as OR/BM25 terms. Multi-word crumbs are not AND-ed token-by-token.

3. **Budget is not AND** (`starter/agent.py`)  
   `budget` stays a slot and a free-text term. The numeric token (`50`) is not an FTS required term (it matched sizes, percents, noise).

Material AND is **unchanged** (dropping it previously cut MiniLM-on Hit to 0.745). Query still includes the raw utterance and `preference_tags` as OR terms.

## What was tried and reverted

| Try | Result |
|-----|--------|
| Union-fill AND results with looser OR up to 81; skip generic-material AND (`fabric`/`cotton`); drop utterance + tags from the BM25 query | Hit **0.51** (below 0.645). Reverted. |
| BM25 `limit` 81 → **200** and shortlist 50 → 200 | Hit/MRR/MTTC **identical** to 81. MiniLM off: Top 10 **is** BM25 top 10, so a longer page cannot promote gold at rank 82. Reverted to 81 / 50. |
| Skip AND on generic materials (`cotton`/`polyester`/`fabric`/…) | Hit **0.710** (below 0.715). Reverted. Material AND is still load-bearing on MiniLM-off. |
| Skip `leather` AND when category is wallet/handbag | Hit **identical** 0.715. Reverted as dead code. |

Do not retry those without a reranker that can promote ranks 11–200 into Top 10.

## Code

- `agent/slots.py` — `_LOOKING_FOR_RE` crumb fallback
- `agent/retrieve.py` — `HYPERNYM_TOKENS`, `and_required_terms`
- `starter/agent.py` — `limit=81`, skip `budget` in `required`
- `agent/rerank.py` — `OPOYO_NO_MINILM=1` short-circuit
- Tests: `tests/test_slots.py`, `tests/test_retrieve.py`, `tests/test_rerank.py`

## Still open

- Intent override Hit 0.533; pre-flip hits do not count
- Gold can still sit past BM25 rank 81 on a given query
- Buying MRR (0.318) is the weak rank problem, not miss-only
- MiniLM-on 0.77 was measured on another machine/venv with torch; not re-run here
