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

