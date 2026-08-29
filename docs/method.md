# Opoyo method

Track 4 shopping copilot. Public 200 (MiniLM on): Hit Rate@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648. Without MiniLM: Hit Rate@10 0.55.

## Method

1. Parse slots from the shopper message (category including Amazon plurals, material, color, size, brand, budget).
2. Fill the last-asked weak slot from `what matters is:` replies.
3. BM25 over sqlite FTS5. Hard-slot tokens are AND. Other query tokens are OR. Evaluator template words (`key`, `requirement`, `exploring`) are stopwords.
4. Anonymized `preference_tags` are extra BM25 terms, not AND.
5. Rank the BM25 shortlist of 50 with a local MiniLM cross-encoder (`ms-marco-MiniLM-L-6-v2`). Fail-closed: missing torch keeps BM25 order.
6. Policy C: ask a missing field when the pool is huge or slots are empty/weak; always return up to 10 catalog ASINs.

## Model and cost

No LLM API. Token usage reported as 0. Estimated cost $0. No API keys required to score.

MiniLM is optional and local. First load may fetch from Hugging Face; scoring does not need network if the model is cached.

## Limits

- Official judging may disable network and may not have torch. The stdlib path still runs.
- Override hits before the flip are ignored by the simulator. Erasing the old slot on `actually/ignore` did not raise override hit rate.
- Crumbs with no product noun (`Running Trail Running`, `Novelty Women`) still miss.
- Gold can match every AND token and still sit past BM25 rank 81.
- Preference tags in the MiniLM query cut Hit Rate from 0.77 to 0.685. Tags stay in BM25 only.
- Skipping MiniLM on empty slots hurt browsing. Widening the shortlist to 100 hurt MTTC.

See `docs/miss-log.md` for eight real misses from this run.
