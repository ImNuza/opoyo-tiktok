# Dense BM25+RRF first-stage (implement THIS, not a different idea)

Hypothesis: Remaining public-200 misses are mostly gold not in BM25 81 (FTS5 AND/OR miss or rank>81); cosine over title+features recovers those ASINs, and rank-only RRF(k=60) keeps BM25-only hits MiniLM already promotes — unlike killed MiniLM fusion of BM25 ranks 1–4.

Pipeline: query → existing sqlite FTS5 AND/OR BM25 top 81 (one list; keep `Retriever.search`) → dense top 81 → RRF(k=60) → 50 → existing `rerank()` CrossEncoder `cross-encoder/ms-marco-MiniLM-L-6-v2`. Policy C unchanged.

RRF (Cormack/Clarke/Büttcher SIGIR 2009): `score(d) = Σ_i 1/(60 + rank_i(d))`. Ranks are 1-indexed (`hits[0]` has rank 1). If list i does not contain d, add no term (do not write rank=∞). Sort by `(-score, first_seen)`; cut 50. Never fuse raw BM25 vs cosine scores.

Bi-encoder: `sentence-transformers/all-MiniLM-L6-v2` (384-d). Encode `f"{title} {' '.join(features)}"` once (same string as `starter/agent.py` MiniLM texts). Cache `data/catalog_embeddings.npz` with `asins` (N,) and L2-normalized `embeddings` float32 (N,384); cosine = `np.dot`. Add `data/catalog_embeddings.npz` to `.gitignore`. Catalog is `data/catalog.jsonl` (50k, gitignored). No FAISS/Qdrant/ES/Haystack/Denser; no hosted vector DB; no LLM API; no DeepSeek on scoring.

Python with MiniLM (MUST use this binary for encode/eval/tests): `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11` (torch 2.13.0, sentence-transformers 6.0.0, numpy 2.4.3). System `python3` is 3.14.2 with NO torch — fail-closed must still import.

Files/functions (implementer; do not edit `evaluator/`, `data/`, or existing test bodies except adding new tests):
- `agent/dense.py` (new): `product_text(product)`, `DenseIndex.load_or_build(catalog)`, `DenseIndex.search(query, k=81)` via `np.dot` + argpartition. Lazy-import `SentenceTransformer` inside try (never at module top). Process singleton; build npz once (minutes); do not re-encode every wakeup. Dense query = `build_query(message, slots)` **without** preference_tags (tags stay BM25 extra only).
- `agent/retrieve.py`: add `rrf_fuse(rankings: list[list[str]], k=60, limit=50) -> list[str]` and `hybrid_search(retriever, dense, query, required) -> list[str]` = `rrf_fuse([retriever.search(query, limit=81, required=required), dense_hits_or_empty])`. Do not change AND/OR BM25.
- `starter/agent.py` `Agent.respond`: `bm25 = self.retriever.search(query, limit=81, required=HARD_CONSTRAINTS values)`; `shortlist = hybrid_search(...)[:50]`; pass into current `rerank(shortlist, user_message, state.slots, texts=texts)`. Keep `decide(..., candidate_count=len(bm25))`. Dense fail → `shortlist = bm25[:50]` (today).
- Tests: `tests/test_rrf.py` — 1-indexed k=60, unranked contributes no term, dual rank-3 beats single rank-1. `tests/test_dense.py` — missing torch / encode error → `[]`; cache load. Do not encode 50k in unittest.
- If floor holds: `docs/method.md` + `docs/miss-log.md`. Never commit npz, `data/catalog.jsonl`, `.env`, `results.json`.

Fail-closed: ImportError / encode / bad npz → BM25-only, identical to today. Sticky `_FAILED` like `agent/rerank.py`.

Eval: `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11 -m evaluator.local_evaluator`
Unittest: `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11 -m unittest discover -s tests -q`
Floor: Hit@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648. Revert scoring files if Hit < 0.77 or MTTC > 6.83.

Do-not-retry: MiniLM fusion of BM25 ranks 1-4; drop AND on shoes/women/clothing; crumb into category AND; clothing wordlists from public misses; AND budget; BM25 limit 200 as MiniLM shortlist 100; skip MiniLM on empty slots; preference tags in MiniLM query; running/walking as `use_case`; dual-track router + hypernym expansion; bidirectional hypernym AND on browsing; dense title-union; MiniLM-on-full-union; RRF of the same first-stage.

Only if first holds: (2) soft price rank as a score, never AND; (3) override string `Actually, ignore my earlier preference`. Stay on `overnight`. Do not commit to `main`.

## Fail log (do not retry)

- 2026-08-30 dense BM25+RRF first-stage (all-MiniLM-L6-v2 top 81 + RRF k=60 → 50 → MiniLM). Public-200 MiniLM: Hit 0.74, MRR 0.453823, MTTC 7.095, tech 0.584247. Floor Hit 0.77 / MTTC 6.83. Reverted `agent/retrieve.py`, `starter/agent.py`, `.gitignore`; removed `agent/dense.py`, `tests/test_rrf.py`, `tests/test_dense.py`. Do not retry dense+RRF, fusion k tweaks, or MiniLM shortlist width.
- 2026-08-30 skip FTS AND on budget (`FTS_AND_CONSTRAINTS = HARD_CONSTRAINTS - {budget}`). Public-200 MiniLM identical to floor: Hit 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648. No-op (budget never the miss driver). Reverted `agent/slots.py`, `starter/agent.py`, tests. Do not retry budget AND skip or numeric-token AND skip without a new miss-rank proof.
- 2026-08-30 soft price demote of MiniLM 50 (catalog price more than 2x off budget). Public-200 MiniLM identical to floor. No-op. Reverted `agent/rerank.py`, `starter/agent.py`, `tests/test_rerank.py`. Do not retry price-band rerank without evidence budget is in slots on miss turns.
- 2026-08-30 MiniLM query strip of retrieve stopwords (`_query_text` via `_terms`). Public-200 MiniLM: Hit 0.735, MRR 0.443016, MTTC 7.045, tech 0.579505. Floor Hit 0.77 / MTTC 6.83. Reverted `agent/rerank.py`, `tests/test_rerank.py`. Do not retry stripping simulator template out of the cross-encoder query.
- 2026-08-30 override suffix → `feature` fill (`Actually, ignore... What I need is:`). Public-200 MiniLM: Hit 0.76, MRR 0.447619, MTTC 6.8, tech 0.598286. intent_override Hit 0.733 → 0.667. Reverted `agent/slots.py`, `starter/agent.py`, `tests/test_slots.py`. Do not retry override feature-fill or erase (erase already had no lift).
- 2026-08-30 dual-track router + answerable FIELD_ORDER + hypernym BM25 expansion (`abc26c2` through `4e64b82`). Public-200 MiniLM on `76ef77f`: Hit 0.69, MRR 0.437931, MTTC 6.135, tech 0.573679. Floor Hit 0.77 / MTTC 6.83. Restored `agent/`, `starter/`, `tests/` to `cad6c1c`. Do not retry dual-track or hypernym expansion as a floor-hold.
- 2026-08-30 bidirectional hypernym AND even on browsing (`0f31b23`). Public-200 MiniLM: Hit 0.69, MRR 0.433944, MTTC 6.13, tech 0.572583. Hit-neutral vs dual-track without AND. Of eight freeze misses, only `public_0015` flipped. Reverted as `76ef77f`. Do not retry bidirectional hypernym AND.
- 2026-08-30 dense title-union (BM25 81 ∪ title cosine 81, MiniLM on the union). Probe miss_enter=3 / leave_hits=0. Public-200 MiniLM: Hit 0.73, MRR 0.457063, MTTC 7.265, tech 0.576819. Reverted on scratch. Do not retry title-union, MiniLM-on-full-union, or RRF of the same first-stage.
- Probed, do not eval (leave_hits or no-op on miss enter81): FTS porter; naive stem_or; last-crumb repeat (deduped MATCH no-op); AND-only required (leave 52 hits); drop CSJ hypernym extras; bm25 title/cat weight sweeps; Policy D empty/weak and count<=80 (0 turn-1 sessions); hypernym extra pad.

Scoring tree is the floor commit plus this fail log. Two consecutive floor drops this wakeup (MiniLM query strip, then override feature-fill). No unused named hypothesis that is not in this log.
