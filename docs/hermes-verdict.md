# Hermes verdict (Track 4 retrieval)

verdict: STOP

## Metrics (`results.json`, public 200)

| metric | value | floor |
| --- | --- | --- |
| hit (`hit_rate_at_10`) | 0.77 | 0.77 |
| mrr | 0.457494 | 0.457494 |
| mttc | 6.78 | 6.78 |
| tech (`recommended_technical_score`) | 0.606648 | 0.606648 |

Recomputed: `0.50*0.77 + 0.30*0.457494 + 0.20*clip((11-6.78)/10,0,1) = 0.606648`.
46 misses / 200. Scenario hits: buying 0.775, browsing 0.775, intent_override 0.733, boundary 0.8.

Quality gate: `python3 -m unittest discover -s tests -q` → 44 tests, OK.

## What changed (files)

Nothing on the scoring path.

- Starting commit / HEAD: `30cd001`. Matches `origin/main`.
- `git diff 30cd001` is empty. Working tree clean.
- `starter/agent.py`, `agent/slots.py`, `agent/retrieve.py`, `agent/rerank.py`, `agent/policy.py`, `tests/` are unmodified.
- Cycle 1 (C MiniLM+BM25 fusion: inject BM25 ranks 1-4 into fused top 10) scored Hit 0.745, MRR 0.447214, MTTC 7.0, tech 0.586664. Reverted.
- Cycle 2 measured A (drop AND on shoes/women/clothing) as enter81=0 / leave81=0 no-op, and B (crumb into category AND) as in81 net -6 to -8. Neither was patched.
- After revert, MiniLM public 200 reprinted the floor above.

SHIP requires an allowed change that held the floor. None landed.

## Why this should not be another retrieval cycle (private 800)

Floor held because the tree is the frozen BM25 + Policy C + fail-closed MiniLM of 50, not because a patch generalized.

Private 800 has zero user overlap and zero target overlap. Remaining allowed ideas do not have a cheap general fix:

- **A hypernym AND** (`agent/retrieve.py`): already measured no-op on enter81/leave81. Not unused, not a lift.
- **B crumb parse** (`agent/slots.py`): already measured in81 net -6 to -8. Would overfit the public 200 crumb strings.
- **C MiniLM fusion** (`agent/rerank.py`): already tried; Hit dropped below floor. Forbidden as KEEP GOING.
- **D ask-by-pool-size** (`agent/policy.py`): unused, but the miss log has no token-level cause for it. Policy C already retrieves when a hard slot is set and `candidate_count <= 80`. Early retrieve on empty/weak slots is the browsing path; skipping MiniLM on empty slots already hurt browsing. No KEEP GOING on D.

Two cycles with no Hit lift and no MTTC drop. That is the STOP rule.

## Remaining miss classes (not sample ids)

1. **Gold not in BM25 81** — hypernym AND (`shoes` vs mules/clogs), missing product noun in the simulator crumb, material-only AND, or every AND token matches and rank is still > 81.
2. **Override-before-flip** — gold can be BM25 rank 1 on turn 1; the simulator refuses conversion until the later intent is sent.
3. **MiniLM noise** — gold inside BM25 top 5, cross-encoder dumps it out of Top 10. Fusion already failed as a general fix.

These are the SHIP leftover classes, but with no landed lift they do not justify SHIP.

## For Dewa

Call it a day on retrieval; leave scoring at the floor and spend the remaining hours on Devpost and the video, not another BM25/MiniLM patch.
