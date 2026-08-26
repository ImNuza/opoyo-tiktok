# Track 4 Shopping Copilot Design

Date: 2026-08-26
Repo: `opoyo` (`https://github.com/ImNuza/opoyo.git`)
Track: TikTok TechJam 2026 Track 4, Shopping Copilot
Status: draft for team review. No kit copy and no agent code until this spec is approved.

## 1. Goal

Beat the official weak BM25 starter on the 200 public sessions by a clear margin, with a README a judge can rerun. Hidden 800-session luck is extra, not the weekend plan.

Starter numbers to beat (public set):

- Hit Rate@10: 0.125
- MRR: 0.068034
- MTTC: 9.81

Score the evaluator actually uses:

```
Efficiency = clip((11 - MTTC) / 10, 0, 1)
TechnicalScore = 0.50 * HitRate@10 + 0.30 * MRR + 0.20 * Efficiency
```

A miss is turn 11. Only exact `parent_asin` equality is a hit. Sessions that need an 11th turn score zero for that session.

One extra spike (deeper rerank or a second retrieval route) is allowed only if hybrid retrieval still looks weak on the 200.

## 2. Constraints we already locked

- Track 4 is chosen. Track 1 is out.
- Official kit is vendored into `opoyo` (option A). Catalog file is not committed.
- 48GB M4 can run BM25 plus local embeddings.
- DeepSeek API is optional spice. Key lives only in local `.env`. Empty key still runs.
- Done means a clear lift on the 200 plus a reproducible README, not maxing every point at the cost of a story we cannot explain.
- Ask vs retrieve is Policy C: a small table, not a chatty agent.
- Saturday morning scores BM25 plus policy. Then the same agent adds embeddings and optional DeepSeek.

## 3. Official protocol (do not invent around this)

The Agent implements:

```python
class Agent:
    def reset(self, session_id: str, user_profile: dict) -> None: ...
    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict: ...
```

Each `respond` returns `message`, `ask_attribute`, and `recommendations`. Optional `usage` when a model is used.

`ask_attribute` is one of: `category`, `material`, `color`, `size`, `style`, `brand`, `budget`, `feature`, `use_case`, `other`, or `null`. The simulator reads this field, not the prose.

`user_profile` is a safe aggregate only: `purchase_frequency`, `average_prior_rating`, `rating_style`, `preference_tags`, `summary`. No raw user ids, reviews, timestamps, or purchase history.

Fixed mix on public and private sets:

- 40% Buying: a hard constraint is disclosed early.
- 40% Browsing: the customer begins vague.
- 15% Intent Override: an earlier preference is replaced on turn 3 or 4. A hit before the new intent is sent does not count.
- 5% Boundary: the customer may have no preference for a requested attribute.

Catalog: 50,000 products, in memory, read-only. Scored field is `parent_asin`. Visible fields include title, features, description, price, categories, details, average_rating, rating_number, store.

Evaluator command (do not edit the evaluator or public labels):

```
python3 -m evaluator.local_evaluator
```

## 4. Architecture

One process, one catalog in RAM, one Agent instance per evaluator run. Four steps inside `respond`, always in this order:

1. Update state (slots, asked fields, override erase).
2. Policy C chooses ASK or RETRIEVE.
3. Retrieve from the frozen catalog (BM25 first, later BM25 plus local embeddings).
4. Optional DeepSeek rerank of a shortlist. Never invent ASINs.

`starter/agent.py` is a thin wrapper. Logic lives in `agent/`.

```
evaluator -> starter/agent.py -> agent/state.py
                               -> agent/slots.py
                               -> agent/policy.py
                               -> agent/retrieve.py -> agent/catalog.py
                               -> agent/rerank.py   -> DeepSeek or no-op
```

DeepSeek is never the source of IDs. The catalog index is.

## 5. Components

| Unit | Responsibility | Depends on |
|---|---|---|
| `starter/agent.py` | `reset` / `respond` contract. Always return valid keys. | all `agent/` modules |
| `agent/catalog.py` | Load `data/catalog.jsonl` once. Index by `parent_asin`. Refuse to start if the file is missing. | disk |
| `agent/state.py` | Per-session slots, asked-field set, last action, profile copy. | none |
| `agent/slots.py` | Parse message into allowed attributes. Rules first. DeepSeek only when the message is messy. Override erases the old value. | state, optional DeepSeek |
| `agent/policy.py` | Policy C table. Returns ASK plus an `ask_attribute`, or RETRIEVE. Turn 10 always RETRIEVE. | state |
| `agent/retrieve.py` | Query from slots plus latest message. BM25, later merged with local embeddings. Shortlist ~50. | catalog |
| `agent/rerank.py` | Optional DeepSeek order of the shortlist. Drop any ID not in the shortlist. No-op if key empty, error, or timeout. | retrieve output, env |
| `docs/policy-table.md` | Human-readable Policy C. SOB/SOA own this. CS codes `policy.py` from it. | none |
| `docs/miss-log.md` | After each evaluator run, 5 misses in one-liners. SOB/SOA own this. | `results.json` |

Files we do not edit: `evaluator/`, `data/public_set.jsonl`, official `docs/` from the kit except our added notes.

Gitignore already covers `.env`, venv, `__pycache__`, `results.json`, `data/catalog.jsonl`, `data/catalog.jsonl.gz`.

`.env.example` is the empty template. Real key never committed.

## 6. Policy C

SOB/SOA write this as a table CS can implement. If a row cannot be coded, it is dropped.

Default table until they replace it:

| Signal | Action |
|---|---|
| Turn == 10 | RETRIEVE. `ask_attribute` is null. |
| Buying: a hard constraint already in slots or the current message | RETRIEVE. Still return IDs. |
| Browsing: still vague (too few slots, huge candidate pool) | ASK once for the highest-value missing field, and still return IDs if any constraint exists. |
| Intent Override detected (contradiction vs an earlier slot) | Erase the old slot. Do not treat a pre-flip Top 10 as done. RETRIEVE on the new constraint if it is hard, else ASK the field that flipped. |
| Boundary: user has no preference on a field | Never ask that field again. RETRIEVE. |
| Policy cannot pick a field | `ask_attribute` is null. RETRIEVE. |

Always return catalog IDs when we have any constraint, including on ASK turns. Asking without IDs is legal. Leaving IDs out on Buying is how we waste MTTC.

Do not re-ask a field already in `asked`, except after that field was overridden.

Highest-value missing field order unless the miss log says otherwise: category, budget, brand, size, color, material, style, feature, use_case.

## 7. Retrieval and ranking

Saturday baseline (stack 2): BM25 over title, features, categories, store, description. Query is the latest message plus filled slots.

Then (stack 1): add local embeddings on the M4 (sentence-transformers MiniLM class, on the order of 100 to 500MB). Merge BM25 and embedding ranks. Keep the catalog in RAM. No hosted vector DB.

Shortlist size: about 50. Final list: 10 unique valid `parent_asin`s.

DeepSeek rerank: send shortlist titles plus the current slots and message. Model returns an order, not new IDs. If it returns an unknown ASIN, drop it and fill from local rank.

Profile tags are weak priors (boost matching brand or style), not a fake purchase history.

## 8. Data flow for one session

1. `reset(session_id, user_profile)` stores profile and empty slots.
2. Turn 1 message is parsed into slots. Policy C chooses ASK or RETRIEVE.
3. ASK still runs retrieve if any constraint exists, so Buying can hit early.
4. RETRIEVE builds the query, BM25 (later hybrid), optional rerank, returns 10 IDs.
5. Evaluator scores the first 10 unique valid IDs. Hit ends the session. Miss: merge the next message. Contradiction erases the old slot.
6. Stop at turn 10. We never send an 11th call.

## 9. Error handling

The evaluator treats exceptions, invalid output, and timeouts as misses. Fail closed. Never crash a session.

- Catalog missing or checksum fail: refuse to start. Do not half-run 200 sessions.
- Empty DeepSeek key, 401, timeout, rate limit: skip rerank and LLM slot-fill. Keep local ranking. Log once, not per turn.
- DeepSeek ASIN not in the shortlist or catalog: drop it, fill from local ranking.
- Slot parse fail: keep previous slots, retrieve on the raw message.
- Duplicate or invalid `parent_asin`: strip before return.
- Policy cannot pick `ask_attribute`: null, then retrieve.
- Turn 10: never ask.

## 10. Secrets and cost

- DeepSeek key only in `.env`. Never in git, README, traces, screenshots, or chat.
- Each teammate copies `.env.example` to `.env`.
- If `.env` is committed, rotate the key and treat the old one as burned.
- $15 is a weekend budget for rerank and messy slot-fill, not a per-turn brain.
- Token `usage` is reported when a model is used. It is a feasibility metric, not part of TechnicalScore.
- Disclose model name, approx cost, and fallback in the README.

## 11. Testing

Contract tests:

- `reset` then `respond` return required keys.
- `ask_attribute` is allowed or null.
- Recommendations are catalog ASINs only.
- After stripping, at most 10 unique valid IDs.

Policy tests:

- Buying with a hard constraint retrieves.
- Browsing vague asks once.
- Override erases the old slot.
- Boundary does not re-ask the same field.
- Turn 10 never asks.

Retrieval tests:

- A known title fragment returns that product in the shortlist.
- Fake ASINs never appear.

Rerank tests:

- No key: output equals local ranking.
- Stub LLM invents an ASIN: that ID is dropped.

Score ritual:

- Run `python3 -m evaluator.local_evaluator` on the 200.
- Freeze the BM25-plus-policy number in the README before embeddings land.
- After each change, log Hit Rate, MRR, MTTC.
- Do not edit public labels.

## 12. Who does what

CS Y4s: catalog load, BM25, embeddings, Agent wiring, tests, evaluator loop.

Dewa (IS): second-machine reproduce, one-command evaluator, score log, Devpost repo hygiene, README.

SOB Y2 and SOA Y2 (non-tech, critical only if CS wires their table):

- Before Saturday: tag about 30 of the 200 public sessions. For each: buying or browsing, which slot appeared, whether the user flipped, whether an ask would have helped.
- Turn that into `docs/policy-table.md`. Rows CS cannot code get dropped.
- After each evaluator run: pick 5 misses from `results.json`, append one line each to `docs/miss-log.md` on what the shopper meant. That tells us router vs retrieval.
- Monday: Devpost story, video voiceover, limits, who did what.
- No UI mockups. There is no UI score.

Honest limit: two CS people can ship without the business students. Labels only count if they become `policy.py`.

## 13. 72-hour shape (opinion, not the brief)

Thu 26 to Fri 28: vendor the kit into `opoyo`, download catalog, verify checksum, run the official starter, record 0.125 / 0.068 / 9.81. Workshop Fri 4:00 to 4:45pm.

Sat 12pm to Sun 12pm: BM25 plus Policy C. Freeze that score. Hard turn-10 retrieve.

Sun 12pm to Mon 12pm: local embeddings, override erase, optional DeepSeek rerank. Cut anything that does not move Hit Rate or MTTC.

Mon 12pm to Tue 12pm: freeze features Monday evening. Ablation note (policy only, BM25, full stack). README, Devpost, YouTube API walkthrough. Tuesday morning is buffer. Deadline Tue 1 Sep 12pm.

## 14. Out of scope

- Chat UI.
- Hosted vector DB.
- Letting DeepSeek invent ASINs.
- Training or full fine-tune of a foundation LLM.
- Editing the evaluator or public labels.
- Catalog mutation or fake ASINs.
- Track 1 middleware.

## 15. First implementation slice (after spec approval)

Not started in this document. The first build step is:

1. Copy the official kit into `opoyo` without clobbering `.gitignore` and `.env.example`.
2. Download `catalog.jsonl.gz`, verify SHA256, keep it untracked.
3. Run the starter evaluator and paste the baseline into the README.
4. Replace `starter/agent.py` with a wrapper that still matches the starter score, then add `agent/policy.py` and BM25.

Writing-plans comes after this spec is approved.
