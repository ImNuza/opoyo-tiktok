# Policy C table

Human-readable ask vs retrieve rules for Policy C. Dual-track router
(`agent/router.py`) feeds `track` into `decide`. Rows CS cannot code get dropped.

Source of truth in code: `agent/policy.py` (`decide`). Field ask order (simulator-answerable only): material, color, use_case, feature, style, size, budget. Never ask `category` or `brand` — the official simulator cannot answer them.

Hard constraints: category, brand, budget, size, material, color.

Weak-only keys (do not count as hard): style, feature, use_case, other.

On browsing, a category crumb alone is not treated as a buying constraint.

When `pool_attrs` is present, ask the missing field with the most distinct values on the current candidate pool (need ≥2). Fallback is FIELD_ORDER.

| Priority | Condition | Action | Attribute |
| --- | --- | --- | --- |
| 1 | Turn is 10 or higher | retrieve | none |
| 2 | Slots already hold a hard constraint (not browsing-category-only), and candidate pool is not huge (missing or `candidate_count` <= 80) | retrieve | none |
| 3 | Hard constraint, candidate pool is huge (`candidate_count` is an int and > 80), and a field in FIELD_ORDER is still missing | ask | highest-entropy missing field, else next FIELD_ORDER |
| 4 | Slots empty, weak-only, or browsing with only a category crumb, and a field in FIELD_ORDER is still missing | ask | highest-entropy missing field, else next FIELD_ORDER (material first) |
| 5 | Slots empty or weak-only, and nothing left to ask in FIELD_ORDER | retrieve | none |
| 6 | Any other residual slot shape with a missing FIELD_ORDER field | ask | next missing field |
| 7 | Nothing left to ask | retrieve | none |

## Rule notes (match Task 4 tests)

- Turn 10 always retrieves. No more questions.
- Buying path with a hard constraint (for example color already filled) retrieves on the next decision, unless the pool is huge.
- Vague / browsing start asks `material`, then `color`, then the rest of FIELD_ORDER. Never `category` or `brand`.
- Browsing template with only a parsed category crumb still asks; the crumb is OR-query, not AND.
- Never re-ask a field that is already in `asked` or already present in `slots`. Intent override wipes slots so Policy C may ask again.
- Huge pool (hard constraint present and `candidate_count` > 80) asks the next missing field instead of retrieving.

## Editing this table

1. Add or change a row in plain language here first.
2. If CS cannot implement the row in `agent/policy.py` without breaking the contract or the evaluator, drop that row and note why under the table.
3. Keep priority order stable: turn cap, hard retrieve, huge-pool ask, vague ask, residual ask, else retrieve.
