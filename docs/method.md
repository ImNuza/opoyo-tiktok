# Opoyo method

Track 4 shopping copilot. Frozen public 200 (MiniLM on, `cad6c1c`): Hit Rate@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648. Without MiniLM: Hit Rate@10 0.55.

Scoring files on `main` were restored to that freeze on 2026-08-30 after two later stacks both printed Hit 0.69.

## Method

1. Parse slots from the shopper message (category including Amazon plurals, material, color, size, brand, budget).
2. Fill the last-asked weak slot from `what matters is:` replies.
3. BM25 over sqlite FTS5. Hard-slot tokens are AND. Other query tokens are OR. Evaluator template words (`key`, `requirement`, `exploring`) are stopwords.
4. Anonymized `preference_tags` are extra BM25 terms, not AND.
5. Rank the BM25 shortlist of 50 with a local MiniLM cross-encoder (`ms-marco-MiniLM-L-6-v2`). Fail-closed: missing torch keeps BM25 order.
6. Policy C: ask a missing field when the pool is huge or slots are empty/weak; always return up to 10 catalog ASINs.

## Model and cost

No LLM API. Token usage reported as 0. Estimated cost $0. No API keys required to score.

Latency: public 200 on this Mac took 93s wall (about 0.46s per session) with MiniLM already cached. Local CPU only.

MiniLM is optional and local. First load may fetch from Hugging Face; scoring does not need network if the model is cached.

## Reproducibility

One command in this repo: `python3 -m evaluator.local_evaluator` (imports `starter.agent.Agent`).

The frozen MiniLM public-200 (Hit Rate 0.77, MTTC 6.78) was measured on Python 3.11.15, torch 2.13.0, sentence-transformers 6.0.0. Use `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11` for MiniLM-on. System `python3` is 3.14.2 with no torch; that path is fail-closed and scores Hit Rate 0.55.

No non-obvious environment variables. Network is not required at scoring time if MiniLM is already cached.

## Measured fails after the freeze (do not retry)

Interpreter for both runs: `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11`, torch 2.13.0, sentence-transformers 6.0.0. Tests green before each eval. `results.json` not committed.

- Dual-track router + answerable FIELD_ORDER + hypernym BM25 expansion (`abc26c2` through `4e64b82`, scored on `76ef77f` after AND revert). Hit 0.69, MRR 0.437931, MTTC 6.135, tech 0.573679. Scenario: boundary 0.7 / 5.5, browsing 0.75 / 5.5125, buying 0.7125 / 5.7875, intent_override 0.466667 / 8.933333. Floor Hit 0.77 / MTTC 6.83. Restored `agent/`, `starter/`, `tests/` to `cad6c1c` and removed `agent/router.py`.
- Bidirectional hypernym AND even on browsing (`0f31b23`). Hit 0.69, MRR 0.433944, MTTC 6.13, tech 0.572583. Same Hit as dual-track without AND (AND +1 browsing, -1 buying). Of eight freeze misses (`public_0015`, `0017`, `0019`, `0020`, `0022`, `0026`, `0034`, `0074`), only `public_0015` flipped. Reverted as `76ef77f`.
- Dense title-union (BM25 81 ∪ title cosine 81, MiniLM on the union). Probe `miss_enter=3` (`public_0097` / `0124` / `0188`), `leave_hits=0`. Public-200 MiniLM: Hit 0.73, MRR 0.457063, MTTC 7.265, tech 0.576819. Reverted on scratch. Do not retry title-union, MiniLM-on-full-union, or RRF of the same first-stage.

## Limits

- Official judging may disable network and may not have torch. The stdlib path still runs.
- Override hits before the flip are ignored by the simulator. Erasing the old slot on `actually/ignore` did not raise override hit rate.
- Crumbs with no product noun (`Running Trail Running`, `Novelty Women`) still miss.
- Gold can match every AND token and still sit past BM25 rank 81.
- Preference tags in the MiniLM query cut Hit Rate from 0.77 to 0.685. Tags stay in BM25 only.
- Skipping MiniLM on empty slots hurt browsing. Widening the shortlist to 100 hurt MTTC.

See `docs/miss-log.md` for eight real misses from the frozen run.
