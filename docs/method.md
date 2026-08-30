# Opoyo method

Track 4 shopping copilot. Frozen public 200 (MiniLM on): Hit Rate@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648. Dual-track held that floor. Re-run `python3 -m evaluator.local_evaluator` after the bidirectional hypernym AND and revert if Hit < 0.77 or MTTC > 6.83.

## Method

1. Dual-track router on official simulator templates: buying (`A key requirement is:`), browsing (`still exploring`), override (`Actually, ignore…` / `What I need is:`), boundary (no preference). Override wipes slots before parse.
2. Parse slots from the shopper message (category including Amazon plurals, material, color, size, brand, budget).
3. Fill the last-asked weak slot from `what matters is:` replies.
4. BM25 over sqlite FTS5. Hard-slot tokens are AND. Closed bidirectional hypernym OR groups: any of shoe/clog/mule/boot → footwear; rain → raincoat/waterproof; wallet/billfold → wallet. If a query term hits a family, that family is AND even on browsing, so extras cannot OR-blast the catalog. Other non-family tokens are OR inside that AND. Evaluator template words (`key`, `requirement`, `exploring`) are stopwords.
5. Anonymized `preference_tags` are extra BM25 terms, not AND.
6. Rank the BM25 shortlist of 50 with a local MiniLM cross-encoder (`ms-marco-MiniLM-L-6-v2`) on title+features+details. Query text strips simulator wrappers. Fail-closed: missing torch keeps BM25 order.
7. Policy C: ask a missing *answerable* field when the pool is huge or slots are empty/weak; browsing-category-only still asks. Prefer the field that splits the current pool; else FIELD_ORDER starting at material. Never ask `category` or `brand`. Always return up to 10 catalog ASINs.

## Model and cost

No LLM API. Token usage reported as 0. Estimated cost $0. No API keys required to score.

Latency: public 200 on this Mac took 93s wall (about 0.46s per session) with MiniLM already cached. Local CPU only.

MiniLM is optional and local. First load may fetch from Hugging Face; scoring does not need network if the model is cached.

## Reproducibility

One command in this repo: `python3 -m evaluator.local_evaluator` (imports `starter.agent.Agent`).

The frozen MiniLM public-200 (Hit Rate 0.77, MTTC 6.78) was measured on Python 3.11.15, torch 2.13.0, sentence-transformers 6.0.0. The stdlib path is Python 3.10+ with no packages; bare Python 3.14.2 scores Hit Rate 0.55.

No non-obvious environment variables. Network is not required at scoring time if MiniLM is already cached.

## Limits

- Official judging may disable network and may not have torch. The stdlib path still runs.
- Override hits before the flip are ignored by the simulator.
- Crumbs with no product noun still miss if expansion and BM25 both miss.
- Gold can match every AND token and still sit past BM25 rank 81.
- Preference tags in the MiniLM query cut Hit Rate from 0.77 to 0.685. Tags stay in BM25 only.
- Skipping MiniLM on empty slots hurt browsing. Widening the shortlist to 100 hurt MTTC.

See `docs/miss-log.md` for eight real misses from the frozen run.
