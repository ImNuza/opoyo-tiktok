# Opoyo method

Track 4 shopping copilot. Public 200 MiniLM off + catalog category lexicon: Hit Rate@10 0.81, MRR 0.422776, MTTC 6.28, tech 0.626233 (`docs/opoyo_public200_lexical.json`; 162/200 hits). MiniLM on the previous (regex-only) parse: Hit Rate@10 0.79 (`docs/opoyo_public200.json`). Previous MiniLM freeze on the old parser (`cad6c1c`): Hit 0.77. Older stdlib MiniLM-off note: Hit Rate@10 0.55. Re-run MiniLM on the lexicon parser before treating 0.79 as current MiniLM-on.

## Method

1. Parse slots from the shopper message. Category prefers the longest catalog leaf / last-two crumb that appears in `I'm looking for …` (`Catalog.category_lexicon`). Regex noun list is fallback; then the raw crumb.
2. Fill the last-asked weak slot from `what matters is:` replies.
3. BM25 over sqlite FTS5, limit 81. Specific hard-slot tokens are AND. Hypernyms (`shoes`, `women`, `men`, `clothing`, …) and multi-word crumbs are not AND. Budget is not AND. Other query tokens are OR. Evaluator template words (`key`, `requirement`, `exploring`) are stopwords.
4. Anonymized `preference_tags` are extra BM25 terms, not AND.
5. Rank the BM25 shortlist of 50 with a local MiniLM cross-encoder (`ms-marco-MiniLM-L-6-v2`). Fail-closed: missing torch or `OPOYO_NO_MINILM=1` keeps BM25 order.
6. Policy C: ask a missing field when the pool is huge or slots are empty/weak; always return up to 10 catalog ASINs.

Session writeup of the lexical pass (what landed, what was reverted): `docs/lexical-pass.md`.

## Model and cost

No LLM API. Token usage reported as 0. Estimated cost $0. No API keys required to score.

Latency: public 200 MiniLM-on on Windows CPU (torch 2.13.0) is minutes, not seconds — MiniLM reranks up to 50 products every turn. The evaluator prints `n/200` progress; after Hugging Face “Loading weights: 100%” the first `predict()` can sit silent for 1–2 min (warmup). `TOKENIZERS_PARALLELISM=false` is set in `agent/rerank.py` to avoid a Windows tokenizer/torch deadlock. An older Mac MiniLM-on timing (cached) was 93s wall.

MiniLM is optional and local. First load may fetch from Hugging Face; scoring does not need network if the model is cached.

## Reproducibility

One command in this repo: `python3 -m evaluator.local_evaluator` (imports `starter.agent.Agent`).

Current MiniLM public-200 (Hit 0.79, MTTC 6.265) was measured with this repo venv: torch 2.13.0+cpu, sentence-transformers 6.0.0. The previous freeze (Hit 0.77, MTTC 6.78) was Python 3.11.15 / torch 2.13.0 / sentence-transformers 6.0.0 on `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11`. Without torch, MiniLM is fail-closed (lexical Hit 0.715 on the current parser).

`OPOYO_NO_MINILM=1` skips MiniLM even if torch is installed. Network is not required at scoring time if MiniLM is already cached.

## Measured fails after the freeze (do not retry)

Interpreter for both runs: `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11`, torch 2.13.0, sentence-transformers 6.0.0. Tests green before each eval. `results.json` not committed.

- Dual-track router + answerable FIELD_ORDER + hypernym BM25 expansion (`abc26c2` through `4e64b82`, scored on `76ef77f` after AND revert). Hit 0.69, MRR 0.437931, MTTC 6.135, tech 0.573679. Scenario: boundary 0.7 / 5.5, browsing 0.75 / 5.5125, buying 0.7125 / 5.7875, intent_override 0.466667 / 8.933333. Floor Hit 0.77 / MTTC 6.83. Restored `agent/`, `starter/`, `tests/` to `cad6c1c` and removed `agent/router.py`.
- Bidirectional hypernym AND even on browsing (`0f31b23`). Hit 0.69, MRR 0.433944, MTTC 6.13, tech 0.572583. Same Hit as dual-track without AND (AND +1 browsing, -1 buying). Of eight freeze misses (`public_0015`, `0017`, `0019`, `0020`, `0022`, `0026`, `0034`, `0074`), only `public_0015` flipped. Reverted as `76ef77f`.
- Dense title-union (BM25 81 ∪ title cosine 81, MiniLM on the union). Probe `miss_enter=3` (`public_0097` / `0124` / `0188`), `leave_hits=0`. Public-200 MiniLM: Hit 0.73, MRR 0.457063, MTTC 7.265, tech 0.576819. Reverted on scratch. Do not retry title-union, MiniLM-on-full-union, or RRF of the same first-stage.

## Limits

- Official judging may disable network and may not have torch. The stdlib path still runs.
- Override hits before the flip are ignored by the simulator. Erasing the old slot on `actually/ignore` did not raise override hit rate on MiniLM-off (0.533). MiniLM-on raised override Hit to 0.70 by promoting in-shortlist gold after the flip — not by counting pre-flip hits.
- Some crumbs still miss after fallback parse (`Running Trail Running`, `Novelty Women`).
- Gold can match every AND token and still sit past BM25 rank 81. Raising BM25 limit to 200 with MiniLM off did not change Hit/MRR/MTTC (Top 10 is BM25 top 10).
- Preference tags in the MiniLM query cut Hit Rate from 0.77 to 0.685 on the old freeze. Tags stay in BM25 only; MiniLM query is slots + message.
- Skipping MiniLM on empty slots hurt browsing. Widening the shortlist to 100 hurt MTTC. Union-fill AND→OR, dropping generic-material AND, and dropping utterance/tags from BM25 cut MiniLM-off Hit from 0.645 to 0.51; those stay reverted.

See `docs/miss-log.md` for eight real misses from the frozen run.
