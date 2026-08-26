# Policy C table

Human-readable ask vs retrieve rules for Policy C. SOB/SOA can edit this table. Rows CS cannot code get dropped.

Source of truth in code: `agent/policy.py` (`decide`). Field ask order: category, budget, brand, size, color, material, style, feature, use_case.

Hard constraints: category, brand, budget, size, material, color.

Weak-only keys (do not count as hard): style, feature, use_case, other.

| Priority | Condition | Action | Attribute |
| --- | --- | --- | --- |
| 1 | Turn is 10 or higher | retrieve | none |
| 2 | Slots already hold a hard constraint, and candidate pool is not huge (missing or `candidate_count` <= 80) | retrieve | none |
| 3 | Slots hold a hard constraint, candidate pool is huge (`candidate_count` is an int and > 80), and a field in FIELD_ORDER is still missing (not in `asked`, not in `slots`) | ask | next missing field in FIELD_ORDER |
| 4 | Slots empty or weak-only, and a field in FIELD_ORDER is still missing | ask | next missing field (vague start: category first, then budget, then the rest of FIELD_ORDER) |
| 5 | Slots empty or weak-only, and nothing left to ask in FIELD_ORDER | retrieve | none |
| 6 | Any other residual slot shape with a missing FIELD_ORDER field | ask | next missing field |
| 7 | Nothing left to ask | retrieve | none |

## Rule notes (match Task 4 tests)

- Turn 10 always retrieves. No more questions.
- Buying path with a hard constraint (for example color already filled) retrieves on the next decision, unless the pool is huge.
- Vague / browsing start with empty slots asks `category`, then `budget` if category was already asked or filled.
- Never re-ask a field that is already in `asked` or already present in `slots`. Intent override can clear a field from `asked` so Policy C may ask it again.
- Huge pool (hard constraint present and `candidate_count` > 80) asks the next missing field instead of retrieving.

## Editing this table

1. Add or change a row in plain language here first.
2. If CS cannot implement the row in `agent/policy.py` without breaking the contract or the evaluator, drop that row and note why under the table.
3. Keep priority order stable: turn cap, hard retrieve, huge-pool ask, vague ask, residual ask, else retrieve.
