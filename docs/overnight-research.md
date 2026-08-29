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

Do-not-retry: MiniLM fusion of BM25 ranks 1–4; drop AND on shoes/women/clothing; crumb into category AND; clothing wordlists from public misses; AND budget; BM25 limit 200 as MiniLM shortlist 100; skip MiniLM on empty slots; preference tags in MiniLM query; running/walking as `use_case`.

Only if first holds: (2) soft price rank as a score, never AND; (3) override string `Actually, ignore my earlier preference`. Stay on `overnight`. Do not commit to `main`.

## Fail log (do not retry)

- 2026-08-30 dense BM25+RRF first-stage (all-MiniLM-L6-v2 top 81 + RRF k=60 → 50 → MiniLM). Public-200 MiniLM: Hit 0.74, MRR 0.453823, MTTC 7.095, tech 0.584247. Floor Hit 0.77 / MTTC 6.83. Reverted `agent/retrieve.py`, `starter/agent.py`, `.gitignore`; removed `agent/dense.py`, `tests/test_rrf.py`, `tests/test_dense.py`. Do not retry dense+RRF, fusion k tweaks, or MiniLM shortlist width. Experiments (2) and (3) are gated on a holding first shot — not unlocked.
