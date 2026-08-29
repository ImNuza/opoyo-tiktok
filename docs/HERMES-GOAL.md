# Hermes goal: Track 4 retrieval pass (Opoyo)

For Dewa: pull `main`, then paste the `/goal draft` block at the bottom of this file into Hermes. Raise `goals.max_turns` to 40 if it is still 20. Add the unittest quality gate after the goal starts.

Deadline context: TikTok TechJam 2026 Track 4. Scoring agent is BM25 + Policy C + fail-closed MiniLM.
Frozen public-200 floor (`docs/opoyo_public200.json`): Hit@10 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648.
Private 800 has zero user overlap and zero target overlap. Do not overfit public labels.

You are the **orchestrator**. You do not implement the scoring path yourself.
Spawn specialists with `delegate_task` (fresh context each time). You only: plan, assign, merge, run gates, spawn the independent reviewer.

## Outcome (the only end state)

One of these two verdicts exists in `docs/hermes-verdict.md`, written by the **independent reviewer**, not by you:

- `SHIP` — allowed change landed, floor held, remaining misses are not worth another retrieval patch.
- `STOP` — no generalizing hypothesis left. Leave scoring behavior at or above the floor.

`KEEP GOING` is not a terminal verdict. If the reviewer says that, you run exactly one more named hypothesis, then spawn a **new** reviewer.

## Orchestration

Spawn, do not solo:

| Role | Job | May edit |
| --- | --- | --- |
| Miss analyst | Read `docs/miss-log.md`, `docs/method.md`, `evaluator/local_evaluator.py` (`initial_message`, `coarse_category`). Name the failure class, not the sample id. | nothing in `agent/` / `starter/` |
| Patcher A — hypernym AND | Soft-boost generic crumbs (`shoes`, `women`, `clothing`); AND only specific constraints. | `agent/retrieve.py`, tests |
| Patcher B — crumb parser | Parse `I'm looking for X` up to `.` / `but I'm still exploring`. No new clothing wordlist from public 200. | `agent/slots.py`, tests |
| Patcher C — MiniLM fusion | Do not replace BM25 order wholesale. Fuse or freeze BM25 top-3 so rank-4 gold cannot be dumped. | `agent/rerank.py`, `starter/agent.py`, tests |
| Tester | `python3 -m unittest discover -s tests -v` | tests only |
| Evaluator | `python3 -m evaluator.local_evaluator`. Park the goal on this PID (`/goal wait`). | writes `results.json` (gitignored) |
| Independent reviewer | See below. Spawned only after you believe you are finished. Empty context. | `docs/hermes-verdict.md`, `docs/miss-log.md`, `docs/method.md` only |

Rules:

1. Scoring-path patchers run **serially**. Never two writers on `starter/agent.py` or `agent/` at once.
2. Analyst and tester may run in parallel with a patcher.
3. One hypothesis per eval cycle. Revert immediately if Hit < 0.77 or MTTC > 6.83.
4. After you would have said "done", you **must** `delegate_task` a new Independent reviewer. You are not allowed to write `SHIP`/`STOP` yourself.
5. If reviewer returns `KEEP GOING`, spawn patchers again with the reviewer's single hypothesis. Then a **new** reviewer (do not reuse the previous child).
6. Max **three** eval cycles in this goal. Cycle 3 reviewer may only return `SHIP` or `STOP`.

## Independent reviewer (mandatory closer)

Spawn with **no** conversation history. Prompt the child with the following block verbatim:

```
You are an independent Track 4 judge. You did not write this patch.

Read, in order:
- docs/competition_specification.md
- docs/method.md
- docs/miss-log.md
- docs/policy-table.md
- NEXT-STEPS.md
- docs/HERMES-GOAL.md
- starter/agent.py
- agent/slots.py agent/retrieve.py agent/rerank.py agent/policy.py
- tests/ (skim)
- results.json if present (gitignored; still read it)
- git diff against the starting commit

Machine rubric (private 800 will use this):
  TechnicalScore = 0.50*Hit@10 + 0.30*MRR + 0.20*clip((11-MTTC)/10,0,1)
Floor: Hit 0.77, MRR 0.457494, MTTC 6.78, tech 0.606648.

Human rubric (do not chase): dual-track buying/browsing, question-value asking,
override, explanations, Devpost/video. Those are OUT OF SCOPE for this goal
unless a retrieval patch accidentally helps them.

Decide exactly one:
- SHIP — floor held; any lift is real and should generalize (simulator template,
  not public-set ASINs); remaining misses are gold-not-in-81 / override-before-flip
  / MiniLM noise without a cheap general fix.
- KEEP GOING — exactly one unused hypothesis from {A hypernym AND, B crumb parse,
  C MiniLM fusion, D ask-by-pool-size}. Name the file and the token-level cause.
  Forbidden as KEEP GOING: longer clothing wordlists, AND budget, widen BM25 200 /
  MiniLM 100, skip MiniLM on empty slots, preference tags in MiniLM query,
  parse running/walking as use_case, DeepSeek as scoring path.
- STOP — two cycles with no Hit lift and no MTTC drop, or the only remaining
  ideas overfit public 200, or tests/eval missing.

Write docs/hermes-verdict.md with:
  verdict: SHIP | KEEP GOING | STOP
  hit, mrr, mttc, tech (from results.json)
  what changed (files)
  why it should / should not generalize to private 800
  remaining miss classes (not sample ids)
  one sentence for Dewa: call it a day or not.

If results.json is missing, tests failed, or Hit < 0.77: you may not SHIP.
```

## Allowed work (only this)

A. Hypernym AND in `agent/retrieve.py` — measured miss class: category AND `shoes` drops clogs/mules out of BM25 81.
B. Generic first-message crumb parse in `agent/slots.py` — simulator always says `I'm looking for {coarse_category}`. Do **not** extend `_CATEGORY_WORDS` from public titles.
C. MiniLM+BM25 fusion — measured miss class: gold BM25 rank 4, MiniLM knocks it out of Top 10.
D. Optional, only if reviewer names it: if candidate_count is already small, retrieve even when Policy C wants to ask. Do not redesign FIELD_ORDER.

## Forbidden (revert if an agent does them)

- Hit@10 below 0.77 on a full public 200, or MTTC above 6.83
- AND-require budget; AND-require material if a run shows Hit drop (material AND was load-bearing; dropping it hit 0.745)
- BM25 limit 200 or MiniLM shortlist 100
- Skip MiniLM when slots empty
- Preference tags in the MiniLM query
- Parse running/walking crumbs as `use_case`
- Live DeepSeek / any LLM API on the scoring path
- Edit `evaluator/`, `data/public_set.jsonl`, or invent ASINs
- Commit `.env`, `data/catalog.jsonl`, `results.json`
- Devpost copy, video, UI, Track 1
- "Improve the wordlist from these 46 misses"

## Verification (orchestrator must run, reviewer must cite)

```bash
python3 -m unittest discover -s tests -q
python3 -m evaluator.local_evaluator
```

Evaluator writes `results.json`. Compare to `docs/opoyo_public200.json`.

Pass:

- unittest exit 0
- Hit@10 >= 0.77
- MTTC <= 6.83
- tech >= 0.606648
- `docs/hermes-verdict.md` exists with `SHIP` or `STOP` from the independent reviewer
- `docs/method.md` + `docs/miss-log.md` updated if behavior changed
- `git status` does not include `.env` / catalog / `results.json`

The `/goal` judge will only see your last ~4KB. End your final turn by pasting the verdict file contents and the metric JSON (no session dump). Say explicitly: `INDEPENDENT REVIEWER VERDICT: SHIP` or `STOP`. Do not claim done on your own say-so.

## Stop / pause (human)

- Pause if `data/catalog.jsonl` is missing, MiniLM download hangs, or Hit falls below floor after revert.
- `/goal wait <evaluator-pid>` while public 200 runs; do not busy-loop.
- Three eval cycles or 40 goal turns, then auto-pause for Dewa.
- Feature freeze remains Monday evening. This goal is retrieval only.

## Call it a day (Dewa-facing)

Call it a day when the reviewer writes `SHIP` or `STOP`.
Do **not** keep going for Devpost/video inside this goal.
Do **not** keep going for Hit 0.82 — that is not the acceptance bar.
The bar is: floor held, at most the three allowed patches, independent judge says remaining misses will not generalize.

## How Dewa starts this

1. `git pull origin main`
2. Confirm `data/catalog.jsonl` exists (gitignored; needed to eval).
3. Optional: set `goals.max_turns: 40` in Hermes config.
4. Paste the `/goal draft` block below.
5. Then: `/goal gate add python3 -m unittest discover -s tests -q`
6. Then: `/subgoal Independent reviewer child (fresh context) must write docs/hermes-verdict.md. Orchestrator self-declaration of done is insufficient.`

Do not put the full evaluator in a quality gate (first MiniLM load can exceed the gate timeout). Orchestrator runs it and parks with `/goal wait`.
