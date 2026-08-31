# Lexical pass (this session)

Public-200, BM25 limit **81**, shortlist 50. MiniLM-off numbers: `docs/opoyo_public200_lexical.json`. MiniLM-on numbers: `docs/opoyo_public200.json`.

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
| **+ last noun in crumb (MiniLM off)** | 0.715 | 0.406 | 6.87 | 0.562 |
| **+ catalog category lexicon (MiniLM off, current)** | **0.810** | 0.423 | **6.28** | **0.626** |
| Same parse + MiniLM on (before lexicon) | 0.790 | 0.408 | 6.27 | 0.612 |
| Previous MiniLM freeze, old parser (`cad6c1c`) | 0.77 | 0.457 | 6.78 | 0.607 |

Scenario Hit@10 MiniLM off: browsing 0.763, buying 0.713, boundary 0.90, intent_override 0.533.  
Scenario Hit@10 MiniLM on: browsing 0.80, buying 0.813, boundary 0.80, intent_override 0.70.

MiniLM vs last lexical run: **+15 hits** (57 → 42 misses). Turn-1 hits stayed ~28–29 (first-stage recall unchanged). Rank-1 fell 63 → 58; extra hits are mid/late promotions into Top 10, so MRR is almost flat. Override is the largest relative MiniLM lift (+0.17 Hit). Buying +0.10 Hit. Boundary 0.90 → 0.80 (n=10). Details: `docs/opoyo_public200.json`.

## What landed (keep)

Scoring path is still Policy C + FTS5 BM25 `limit=81` + MiniLM shortlist 50. Changes are intent → query only.

1. **Crumb parse + last noun** (`agent/slots.py`)  
   Simulator first messages are `I'm looking for {coarse_category}…`. Category is the **last** `_CATEGORY_WORDS` hit in that crumb (`Tees & Blouses T-Shirts` → `shirts`, not `blouses`). If no noun matches, the crumb string becomes `category`. No extra clothing gazetteer from public titles.

1b. **Catalog category lexicon** (`agent/catalog.py` `build_category_lexicon`)  
   Unique leaves and last-two crumbs from `catalog.jsonl`, longest substring match on the looking-for crumb. This **replaces the closed wordlist** for simulator crumbs (`athletic walking`, `tees & blouses t-shirts`). Regex list is fallback only. MiniLM-off Hit **0.715 → 0.81**.

1c. **Categories-column fill** (`agent/retrieve.py`)  
   If BM25 AND returns fewer than 81, append FTS `categories:"token"` hits. Hit stayed 0.81 (kept).

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
| Singular/plural OR (`clog`/`clogs`) on extras + category fill | MiniLM-off Hit **0.765** (below 0.81). Reverted. |

MiniLM on the 50-shortlist **does** promote in-list gold (Hit 0.715 → 0.79). It does not recover gold past BM25 81. Do not retry BM25 200 / shortlist 100 without a new measurement; the old MiniLM-on widen still hurt MTTC.

## Code

- `agent/slots.py` — `_LOOKING_FOR_RE` crumb fallback
- `agent/retrieve.py` — `HYPERNYM_TOKENS`, `and_required_terms`
- `starter/agent.py` — `limit=81`, skip `budget` in `required`
- `agent/rerank.py` — `OPOYO_NO_MINILM=1` short-circuit
- Tests: `tests/test_slots.py`, `tests/test_retrieve.py`, `tests/test_rerank.py`

## Still open

- 42 MiniLM-on misses: gold still not in BM25 81, or MiniLM left it at rank 11+
- Intent override MiniLM-on Hit 0.70; pre-flip hits still do not count
- Buying MiniLM-on MRR 0.373 — more hits, still weak ranks (MiniLM parks some gold at 5–10)
- Rank-1 count dropped slightly with MiniLM (63 → 58)
