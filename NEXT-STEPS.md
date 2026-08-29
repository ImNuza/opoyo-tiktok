# Next steps: Track 4 Shopping Copilot

Last updated: 2026-08-29

`main` is BM25 + Policy C + fail-closed MiniLM rerank of 50. It is not the finished jam entry.

Public 200:

- Official starter: Hit Rate@10 0.125, MRR 0.068034, MTTC 9.81
- Opoyo without MiniLM: Hit Rate@10 0.55
- Opoyo with MiniLM: Hit Rate@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648

Deadline: Tue 1 Sep 2026, 12pm Devpost. 72 hours started Sat 29 Aug, 12pm.

## What is already on main

- Official kit vendored (evaluator, 200 sessions, Agent contract).
- Agent in `starter/agent.py`, logic in `agent/`.
- Plural Amazon category crumbs, preference tags as extra BM25 terms (not AND), template stopwords.
- MiniLM `cross-encoder/ms-marco-MiniLM-L-6-v2` on the shortlist of 50. Fail-closed if torch is missing.
- DeepSeek rerank is still a no-op. Empty `.env` still runs.
- 44 unit tests. Catalog at `data/catalog.jsonl` (50k), gitignored.
- `docs/method.md` and `docs/miss-log.md` are filled.
- `requirements.txt` documents the stdlib path. No hard pip deps.

Do not commit `.env`, `data/catalog.jsonl`, or `results.json`.

## Do not repeat (measured fails)

- Do not AND-require budget or material (material AND helps; dropping it cut Hit to 0.745).
- Do not widen BM25 to 200 / MiniLM shortlist to 100 (MTTC got worse).
- Do not skip MiniLM when slots are empty (browsing dropped).
- Do not parse running/walking crumbs as `use_case` (MTTC got worse).
- Do not put preference tags into the MiniLM query (Hit 0.77 to 0.685).

## Remaining (in order)

1. Leave retrieval frozen unless a miss in `docs/miss-log.md` has a new token-level cause.
2. Devpost story, 3-minute video, who-did-what. No UI score.
3. Monday evening feature freeze. Tuesday morning is buffer.

## How we know we are winning

Only exact `parent_asin` hits count. Turn 11 is a miss.

| Signal | Now |
|---|---|
| Hit Rate well above 0.125 | 0.77 |
| MRR up | 0.457 |
| MTTC down from 9.81 | 6.78 |
| Remaining misses | 46 / 200. See `docs/miss-log.md` |

## Out of scope

Chat UI. Hosted vector DB. Letting DeepSeek invent ASINs. Track 1.
