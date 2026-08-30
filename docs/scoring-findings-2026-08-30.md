# Scoring findings, 30 Aug 2026

Live scoring on `main` is still the `cad6c1c` freeze at `b50a95b`: BM25 + Policy C + fail-closed MiniLM of 50.

Interpreter for every MiniLM-on number below: `/Users/dewa/.hermes/hermes-agent/venv/bin/python3.11` (torch 2.13.0, sentence-transformers 6.0.0). PATH `python3` is 3.14.2 with no torch (fail-closed Hit 0.55). Tests green before each eval. `results.json` not committed.

Floor: Hit 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648. Revert if Hit < 0.77 or MTTC > 6.83.

## Freeze reprint

After restoring scoring files to `cad6c1c` (`b50a95b`), MiniLM public-200 reprinted:

| Metric | Value |
|---|---|
| Hit Rate@10 | 0.77 |
| MRR | 0.457494 |
| MTTC | 6.78 |
| tech | 0.606648 |

| scenario | n | hit | mrr | mttc |
|---|---:|---:|---:|---:|
| boundary | 10 | 0.8 | 0.377778 | 5.0 |
| browsing | 80 | 0.775 | 0.526052 | 7.1875 |
| buying | 80 | 0.775 | 0.409092 | 6.4625 |
| intent_override | 30 | 0.733333 | 0.430317 | 7.133333 |

Tests: 44 OK.

## Turn-1 BM25-81 probe (no MiniLM 200)

Against freeze `results.json` (Hit 0.77). Window is `Retriever.search(..., limit=81)`.

| bucket | n | meaning |
|---|---:|---|
| hit_in81 | 102 | hit, gold already in turn-1 BM25 81 |
| hit_out81 | 52 | hit, gold missing at turn 1, recovered later |
| miss_out81 | 33 | miss, gold never in turn-1 BM25 81 |
| miss_in81 | 13 | miss, gold in 81 and still miss |

miss_out81 by scenario: browsing 16, buying 11, intent_override 4, boundary 2.
miss_in81 by scenario: buying 7, intent_override 4, browsing 2.

Eight freeze-log sessions: `public_0015` / `0017` / `0019` / `0020` / `0022` / `0074` are miss_out81. `public_0026` is miss_in81 at BM25 rank 4. `public_0034` is miss_in81 at BM25 rank 1 (override hits do not count until the flip).

JSON: `.night-loop/gold_in_81.json` (gitignored).

## Measured fails this day (do not retry)

All MiniLM-on public-200. Scoring files restored after each drop. No keep on `main` except the freeze restore.

### Dual-track + hypernym expansion

Commits `abc26c2` through `4e64b82`. Scored on `76ef77f` after the AND revert.

Hit 0.69, MRR 0.437931, MTTC 6.135, tech 0.573679.

Scenario: boundary 0.7 / 5.5, browsing 0.75 / 5.5125, buying 0.7125 / 5.7875, intent_override 0.466667 / 8.933333.

Restored `agent/`, `starter/`, `tests/` to `cad6c1c`. Removed `agent/router.py`. Landed as `b50a95b`.

### Bidirectional hypernym AND on browsing

`0f31b23`. Hit 0.69, MRR 0.433944, MTTC 6.13, tech 0.572583.

Hit-neutral vs dual-track without AND (AND +1 browsing, -1 buying). Of the eight freeze misses, only `public_0015` flipped. Reverted as `76ef77f`.

### Dense title-union (not RRF)

Scratch worktree `.worktrees/scratch` on `scratch/isolated`. Not merged.

First-stage = BM25 81 union bi-encoder title cosine 81 (`all-MiniLM-L6-v2`, title only). MiniLM reranked the union. Policy C unchanged.

Cheap probe: `miss_enter=3` (`public_0097` / `0124` / `0188`), `leave_hits=0`. BM25-first `union[:50]` was a no-op (`miss_enter=0`).

Full MiniLM: Hit **0.73**, MRR 0.457063, MTTC **7.265**, tech 0.576819. Tests 52 OK before eval.

Scenario Hit: boundary 0.8, browsing 0.7375, buying 0.7625, intent_override 0.6.

Reverted on the worktree. Do not retry title-union, MiniLM-on-full-union width, or RRF of the same first-stage. Dense BM25+RRF already failed earlier at Hit 0.74.

## What this means

First-stage recoveries that widen MiniLM's pool (dual-track, hypernym AND, RRF, title-union) have all dropped Hit or MTTC. The 33 miss_out81 golds are still the miss class. The 13 miss_in81 cases are MiniLM dump or override-before-flip, not a missing first-stage row.

`main` stays on the freeze. Remaining jam work is Devpost / 3-minute video, not another retrieve patch.
