# Miss log

How to fill this file after a local eval run.

1. Run:

```bash
python3 -m evaluator.local_evaluator
```

2. Open `results.json` at the repo root.
3. Pick 5 miss sessions (no hit within 10 turns, or target never in Top 10).
4. Append one line per miss below, using this shape:

`session_id | scenario (if present) | what the shopper meant | router or retrieval`

- **router**: Policy C asked the wrong field, re-asked, or retrieved too early/late.
- **retrieval**: BM25 ranked the wrong products or the query text was too thin.

Do not invent sample sessions. Only log real misses from `results.json`.

## Entries

From public 200 at Hit Rate 0.77 / MTTC 6.78 (`ed2eb11`, MiniLM on). 46 misses. Turn-1 BM25 rank is against search limit 81.

public_0015 | browsing | Shoes Mules & Clogs (Crocs Classic Clog) | retrieval: category AND shoes, gold not in BM25 81
public_0017 | buying | leather wallets (Travelambo RFID wallet) | retrieval: AND leather+wallets, gold not in BM25 81
public_0019 | browsing | Outdoor & Work Rain (Asgard rain boots) | retrieval: no category noun parsed, gold not in BM25 81
public_0020 | buying | Novelty Women / cotton (funny grandma T-shirt) | retrieval: no product noun in crumb, material-only AND
public_0022 | buying | Dresses Casual / fabric (YESNO summer dress) | retrieval: AND dresses+fabric matches gold tokens but rank > 81
public_0026 | buying | Running Trail Running / 100% Synthetic (ASICS Gel-Venture) | retrieval: BM25 rank 4 with empty slots, MiniLM knocks it out of Top 10
public_0034 | intent_override | Shoes Loafers / leather | router: gold BM25 rank 1 on turn 1, override hits do not count until the later flip
public_0074 | browsing | Athletic Walking (Skechers Go Walk) | retrieval: no category noun parsed, gold not in BM25 81

## After freeze (2026-08-30)

Dual-track + hypernym expansion (`76ef77f`) printed Hit 0.69. Bidirectional hypernym AND (`0f31b23`) also printed Hit 0.69; of the eight freeze misses above, only `public_0015` flipped. Dense title-union printed Hit 0.73 / MTTC 7.265 on scratch and was reverted. Scoring files on `main` stay at `cad6c1c` (`b50a95b`). See `docs/scoring-findings-2026-08-30.md`.

## 31 Aug 2026

Python BM25 drop-in vs FTS5, same tokens and AND/OR, worktree `scratch/bm25-custom`. Turn-1 gold-in-81: 117 vs 115, miss_enter 6, leave_hits 4. No full 200. One-way shoes hyponym: 115 vs 115. Neither merged.
