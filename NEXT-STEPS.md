# Next steps: Track 4 Shopping Copilot

Last updated: 2026-08-30

`main` scoring files are the `cad6c1c` freeze: BM25 + Policy C + fail-closed MiniLM rerank of 50.

Public 200 freeze (MiniLM on, `cad6c1c`):

- Official starter: Hit Rate@10 0.125, MRR 0.068034, MTTC 9.81
- Opoyo without MiniLM: Hit Rate@10 0.55
- Opoyo with MiniLM: Hit Rate@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648

Deadline: Tue 1 Sep 2026, 12pm Devpost. 72 hours started Sat 29 Aug, 12pm.

## What is already on main

- Official kit vendored (evaluator, 200 sessions, Agent contract).
- Agent in `starter/agent.py`, logic in `agent/`.
- Plural Amazon category crumbs, preference tags as extra BM25 terms (not AND), template stopwords.
- MiniLM `cross-encoder/ms-marco-MiniLM-L-6-v2` on the shortlist of 50. Fail-closed if torch is missing.
- Catalog at `data/catalog.jsonl` (50k), gitignored.
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
- Do not ship dual-track router + answerable FIELD_ORDER + hypernym BM25 expansion. Public-200 MiniLM on `76ef77f` (that stack, AND already reverted): Hit 0.69, MRR 0.437931, MTTC 6.135, tech 0.573679. Floor Hit 0.77 / MTTC 6.83.
- Do not AND bidirectional hypernym families on browsing (`0f31b23`). Public-200 MiniLM: Hit 0.69, MRR 0.433944, MTTC 6.13, tech 0.572583. Hit-neutral vs dual-track without AND. Of the eight freeze misses, only `public_0015` flipped. Reverted as `76ef77f`.
- Do not dense title-union (BM25 81 ∪ title cosine 81, MiniLM on the union). Probe `miss_enter=3` / `leave_hits=0`. Public-200 MiniLM: Hit 0.73, MRR 0.457063, MTTC 7.265, tech 0.576819. Reverted on scratch. Do not retry MiniLM-on-full-union or RRF of the same first-stage.

## Remaining (in order)

1. Devpost story, 3-minute video, who-did-what. No UI score. Scoring stays on `b50a95b`.

## How we know we are winning

Only exact `parent_asin` hits count. Turn 11 is a miss.

| Signal | Frozen (`cad6c1c`) |
|---|---|
| Hit Rate well above 0.125 | 0.77 |
| MRR up | 0.457 |
| MTTC down from 9.81 | 6.78 |
| Remaining misses | 46 / 200. See `docs/miss-log.md` |

## Out of scope

Chat UI. Hosted vector DB. Letting an LLM invent ASINs. Track 1.
