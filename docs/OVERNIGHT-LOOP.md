# Overnight loop: research then implement (8 hours)

Dewa is asleep. Do not ask him anything. Do not write Devpost or video scripts.
This loop **may edit scoring code**. It must revert any patch that loses the floor.

Floor (`docs/opoyo_public200.json`): Hit@10 **0.77**, MRR 0.457494, MTTC **6.78**, tech 0.606648.
Revert immediately if a full public-200 MiniLM eval has Hit < 0.77 or MTTC > 6.83.

Work on git branch `overnight` only. Do not commit to `main`. If you are on `main`, `git checkout -b overnight` first.

## Why this loop exists

The afternoon `/goal` already killed three ideas on this public 200:

- MiniLM fusion of BM25 ranks 1–4 → Hit 0.745 (reverted)
- Drop AND on shoes/women/clothing → enter81 no-op
- Crumb into category AND → in81 net −6 to −8

Do **not** retry those. The remaining 46 misses are mostly **gold not in BM25 81**. MiniLM cannot recover a product that never entered the shortlist. The kit explicitly allows hybrid retrieval. You still only have lexical first-stage.

## Target architecture (implement this)

BM25 (existing sqlite FTS5) **and** a local bi-encoder over the 50k catalog, fused with Reciprocal Rank Fusion, then the existing fail-closed MiniLM cross-encoder on the fused 50.

```
query → BM25 top 81
     → dense top 81 (numpy, in-memory)
     → RRF(k=60) → 50
     → MiniLM cross-encoder (already in agent/rerank.py)
```

Fail-closed: no torch / encode error → current BM25 path, Hit 0.55-class still runs.

Do not use a hosted vector DB. Do not call an LLM API. Do not add DeepSeek to scoring.

## Papers and OSS to read, then copy the idea (not the repo)

Read these, then implement the *algorithm* in this repo's style (stdlib + optional sentence-transformers):

1. ProductAgent — conversational product search with BM25 vs dense vs fusion  
   https://arxiv.org/abs/2407.00942  
   Takeaway: dense and fusion beat BM25 on product MRR; clarification is separate. You already have Policy C. Steal retrieval fusion, not their agent.
2. Cormack, Clarke, Büttcher — Reciprocal Rank Fusion (SIGIR 2009)  
   `score(d) = Σ 1 / (k + rank_i(d))` with k=60. Rank-only, no score calibration. This is **not** the failed "inject BM25 top-4 into MiniLM list".
3. sentence-transformers retrieve & rerank  
   https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
   https://github.com/huggingface/sentence-transformers  
   Bi-encoder for first-stage (`all-MiniLM-L6-v2` or `sentence-transformers/all-MiniLM-L6-v2`), cross-encoder you already have (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
4. WANDS e-commerce hybrid: BM25 + KNN + RRF beats either alone.

Do not vendor Denser Retriever, Haystack, Qdrant, FAISS-server, or Elasticsearch. 50k titles fit in numpy. `np.dot` / cosine on float32 `[50000, 384]` is enough.

## Orchestration

You are the orchestrator. Spawn `delegate_task` children:

| Role | Job |
| --- | --- |
| Researcher | Read the papers/OSS above + `docs/miss-log.md` + `agent/retrieve.py`. Write a 20-line plan into `docs/overnight-research.md` (hypothesis, files, fail-closed). No scoring edits. |
| Implementer | Code the plan. Serial with other implementers. |
| Tester | `python3 -m unittest discover -s tests -q` |
| Evaluator | `python3 -m evaluator.local_evaluator`. Park on that PID. |

One scoring-path writer at a time.

Wakeup cadence:

1. If `docs/overnight-research.md` has no implementable hybrid plan yet → researcher only.
2. Else implement **one** hypothesis, tests, then full eval.
3. Hit < 0.77 or MTTC > 6.83 → `git checkout --` the scoring files (or `git reset --hard` to last floor commit on `overnight`). Record the fail in `docs/overnight-research.md`. Do not retry it.
4. Hit ≥ 0.77 and tech ≥ 0.606648 → commit on `overnight`, update `docs/opoyo_public200.json` **only on this branch**, freeze that retrieval change.
5. Second experiment only if the first held the floor: soft price rank (budget as a *score*, never AND). Override string `Actually, ignore my earlier preference` is third, only if time.
6. End a wakeup with `LOOP_COMPLETE` when: a floor-holding hybrid is committed, or two consecutive evals failed/reverted with no new unused hypothesis, or local time is past 08:00 Asia/Singapore.

`--times 24` at 20 minutes is the hard 8-hour cap. Do not keep going after that.

## Allowed to implement

- `agent/dense.py` (new): encode catalog titles+features once, cache under `data/catalog_embeddings.npz` (gitignored). Query encode + top-k cosine.
- `agent/retrieve.py`: RRF merge of BM25 hits and dense hits. Keep existing AND/OR BM25 as one list.
- `starter/agent.py`: pass fused 50 into current `rerank()`.
- Tests for RRF, fail-closed dense, cache load.
- `docs/method.md` + `docs/miss-log.md` if behavior changes and floor holds.
- `.gitignore` entry for the embedding cache.

## Forbidden (revert if a child does them)

- Retry MiniLM top-4 fusion, clothing wordlists from public misses, AND budget, BM25 limit 200 as MiniLM shortlist 100, skip MiniLM on empty slots, preference tags in MiniLM query, running/walking as `use_case`
- LLM API / DeepSeek on the scoring path
- Hosted vector DB, FAISS server, editing `evaluator/` or `data/public_set.jsonl`
- Commit `.env`, `data/catalog.jsonl`, `results.json`, embedding cache
- Commit to `main`
- Devpost, video, UI, Track 1
- Asking the user anything

## Verification

```bash
python3 -m unittest discover -s tests -q
python3 -m evaluator.local_evaluator
```

Pass to keep a patch: unittest 0, Hit@10 ≥ 0.77, MTTC ≤ 6.83, tech ≥ 0.606648, fail-closed still imports without torch.

Cache build: first MiniLM/bi-encoder load plus 50k encode may take several minutes. Do that once. Do not re-encode every wakeup.

## Git

```bash
git checkout overnight 2>/dev/null || git checkout -b overnight
```

Commit message style: what changed + public-200 Hit/MTTC. If you revert, leave the fail in `docs/overnight-research.md` so the next wakeup does not repeat it.
