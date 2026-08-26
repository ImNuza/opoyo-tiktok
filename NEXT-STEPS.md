# Next steps: Track 4 Shopping Copilot

Last updated: 2026-08-26

This is the SMU team runbook. `main` now has the Saturday baseline: BM25 plus Policy C. It is not the finished jam entry.

Official starter to beat on the 200 public sessions:

- Hit Rate@10: 0.125
- MRR: 0.068034
- MTTC: 9.81

Deadline: Tue 1 Sep 2026, 12pm Devpost. The 72 hours start Sat 29 Aug, 12pm.

## What is already on main

- Official kit vendored (evaluator, 200 sessions, Agent contract).
- Our Agent in `starter/agent.py`, logic in `agent/`.
- Rule-based slots, Policy C (ask vs retrieve), in-memory BM25.
- DeepSeek rerank is a no-op. Empty `.env` still runs.
- 36 unit tests. Catalog is on disk at `data/catalog.jsonl` (50k rows), gitignored. Do not commit it.
- `.env` is gitignored. Copy from `.env.example`. Never paste the key in chat or git.

What is not done: local embeddings, live DeepSeek rerank, a measured score on the 200, Devpost, the video.

## One-time setup (everyone who codes)

```bash
git clone https://github.com/ImNuza/opoyo.git
cd opoyo
cp .env.example .env
# put DEEPSEEK_API_KEY in .env only if you have one. leave empty to run free.

# catalog (already present on Dewa's machine). others:
# download catalog.jsonl.gz from the participant-kit release, check SHA256, gunzip into data/catalog.jsonl
# expected SHA256: 07fd142631fd6b03e2b4d09988c3eb7d53720e9d57010c79db48eeaada50a8f8
# expected rows: 50000

python3 -m unittest discover -s tests -v
```

## CS and IS: do this next, in order

### 1. Freeze the BM25 plus policy score (today or Friday)

Do not add embeddings until this number exists.

```bash
python3 -m evaluator.local_evaluator
```

Writes `results.json` (gitignored). Paste Hit Rate / MRR / MTTC into README under `Opoyo BM25+policy`. If it is not clearly above 0.125 / 0.068 / 9.81, the next lift is retrieval, not chat text.

First run will be slow. The 50k catalog loads into RAM once.

### 2. Friday 28 Aug, 4:00 to 4:45pm workshop

https://vc-my.larkoffice.com/j/484622806

Go in with the baseline number and 5 misses from `results.json`. Ask what the hidden 800 looks like, and whether MTTC counts failed sessions.

### 3. Saturday: embeddings (the real lift)

Local MiniLM-class embeddings on Dewa's 48GB M4. Merge BM25 ranks with embedding ranks. Catalog stays in RAM. No hosted vector DB.

Cut anything that does not move Hit Rate or MTTC on the 200.

### 4. Sunday: DeepSeek as spice, then overrides

- Rerank the shortlist of ~50 only. Never let the model invent ASINs.
- Use DeepSeek for messy slot-fill (`actually not red`) if rules miss it.
- Empty key or timeout must still return local ranking.
- Intent Override is 15% of sessions. A hit before the flip on turn 3 or 4 does not count. Erase the old slot.

### 5. Monday freeze, Tuesday upload

- Freeze features Monday evening.
- Ablation note: policy only vs BM25 vs full stack.
- README, Devpost, YouTube API walkthrough (no UI).
- Tuesday morning is buffer. Deadline 12pm.

## SOB and SOA: your jobs (no Python)

You own two files. If CS does not wire them, the work does not count.

1. **Before Saturday:** open about 30 of the 200 sessions in `data/public_set.jsonl`. For each one write: buying or browsing, which constraint appeared, whether they flipped, whether an ask would have helped.
2. Turn that into `docs/policy-table.md`. A row CS cannot code gets dropped.
3. **After every evaluator run:** pick 5 misses from `results.json`, append one line each to `docs/miss-log.md` (session id, what the shopper meant, router wrong or retrieval wrong).
4. Monday: Devpost story, video voiceover, limits, who did what. No Figma. There is no UI score.

## How we know we are winning

| Signal | Meaning |
|---|---|
| Hit Rate well above 0.125 | retrieval is finding the product |
| MRR up | the product is nearer rank 1 |
| MTTC down from 9.81 | we hit earlier, not at turn 10 |
| Many sessions at turn 11 | still missing. read the miss log |

Do not trust a chat that "sounds helpful." Only exact `parent_asin` hits count. Turn 11 is a miss.

## Files to touch later (not now)

- `agent/retrieve.py` for embeddings
- `agent/rerank.py` for DeepSeek
- `agent/slots.py` if the miss log shows parser gaps
- `docs/policy-table.md` and `docs/miss-log.md` for non-tech
- `README.md` Baseline scores after the first 200-run

Do not edit `evaluator/` or `data/public_set.jsonl`.

## Out of scope

Chat UI. Hosted vector DB. Letting DeepSeek invent ASINs. Track 1.
