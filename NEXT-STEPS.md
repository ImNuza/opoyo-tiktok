# Next steps: Track 4 Shopping Copilot

Last updated: 2026-08-30

`main` is dual-track Policy C + BM25 hypernym expansion + fail-closed MiniLM rerank of 50. That is the scoring agent.

Public 200 freeze (pre dual-track, MiniLM on):

- Official starter: Hit Rate@10 0.125, MRR 0.068034, MTTC 9.81
- Opoyo without MiniLM: Hit Rate@10 0.55
- Opoyo with MiniLM: Hit Rate@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648

Re-run the evaluator after pulling this commit. Revert if Hit < 0.77 or MTTC > 6.83.

Deadline: Tue 1 Sep 2026, 12pm Devpost. 72 hours started Sat 29 Aug, 12pm.

## What is already on main

- Official kit vendored (evaluator, 200 sessions, Agent contract).
- Agent in `starter/agent.py`, logic in `agent/`.
- Dual-track router on official templates (`agent/router.py`).
- Simulator-answerable FIELD_ORDER (no category/brand asks). Pool-entropy ask when the shortlist splits.
- Hypernym OR groups for shoes/rain/wallet. Browsing crumbs are OR, not AND.
- MiniLM query strips simulator wrappers; rerank body is title+features+details.
- Plural Amazon category crumbs, preference tags as extra BM25 terms (not AND), template stopwords.
- MiniLM `cross-encoder/ms-marco-MiniLM-L-6-v2` on the shortlist of 50. Fail-closed if torch is missing.
- 60 unit tests. Catalog at `data/catalog.jsonl` (50k), gitignored.
- `docs/method.md` and `docs/miss-log.md` are filled.
- `requirements.txt` documents the stdlib path. No hard pip deps.

Do not commit `.env`, `data/catalog.jsonl`, or `results.json`.

## Do not repeat (measured fails)

- Do not AND-require budget or material (material AND helps; dropping it cut Hit to 0.745).
- Do not widen BM25 to 200 / MiniLM shortlist to 100 (MTTC got worse).
- Do not skip MiniLM when slots are empty (browsing dropped).
- Do not parse running/walking crumbs as `use_case` (MTTC got worse).
- Do not put preference tags into the MiniLM query (Hit 0.77 to 0.685).
- Do not inject BM25 ranks 1-4 into MiniLM top 10 (Hit 0.745).
- Do not stuff the looking-for crumb into category AND.

## Remaining (in order)

1. Run public 200. Keep or revert this commit on the floor rule.
2. Dense title-union only if this commit holds the floor.
3. Devpost story, 3-minute video, who-did-what. No UI score.

## How we know we are winning

Only exact `parent_asin` hits count. Turn 11 is a miss.

| Signal | Frozen (pre dual-track) |
|---|---|
| Hit Rate well above 0.125 | 0.77 |
| MRR up | 0.457 |
| MTTC down from 9.81 | 6.78 |
| Remaining misses | 46 / 200. See `docs/miss-log.md` |

## Out of scope

Chat UI. Hosted vector DB. Letting an LLM invent ASINs. Track 1.
