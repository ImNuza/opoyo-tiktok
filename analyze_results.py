"""Distribution analysis for hit rate / MRR / MTTC from results.json."""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
PUBLIC_SET = ROOT / "data" / "public_set.jsonl"
CATALOG = ROOT / "data" / "catalog.jsonl"
MAX_TURNS = 10
MISS_MTTC = MAX_TURNS + 1  # evaluator convention for non-hits


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def leaf_category(categories: list | None) -> str:
    if not categories:
        return "(none)"
    return str(categories[-1]) if categories else "(none)"


def category_path(categories: list | None, depth: int = 3) -> str:
    if not categories:
        return "(none)"
    parts = [str(c) for c in categories[:depth]]
    return " > ".join(parts)


def price_bucket(price) -> str:
    if price is None or price == "":
        return "unknown"
    try:
        p = float(price)
    except (TypeError, ValueError):
        return "unknown"
    if p < 15:
        return "<$15"
    if p < 30:
        return "$15-30"
    if p < 60:
        return "$30-60"
    if p < 100:
        return "$60-100"
    return "$100+"


def rating_bucket(r) -> str:
    if r is None:
        return "unknown"
    try:
        v = float(r)
    except (TypeError, ValueError):
        return "unknown"
    if v < 3.5:
        return "<3.5"
    if v < 4.0:
        return "3.5-4.0"
    if v < 4.5:
        return "4.0-4.5"
    return "4.5+"


def mttc_value(session: dict) -> int:
    t = session.get("first_hit_turn")
    return int(t) if t is not None else MISS_MTTC


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0, "hit_rate": None, "mrr": None, "mttc": None}
    hits = [int(r["hit"]) for r in rows]
    return {
        "n": len(rows),
        "hit_rate": sum(hits) / len(rows),
        "mrr": statistics.fmean(r["reciprocal_rank"] for r in rows),
        "mttc": statistics.fmean(mttc_value(r) for r in rows),
        "misses": len(rows) - sum(hits),
    }


def fmt(s: dict) -> str:
    if s["n"] == 0:
        return "n=0"
    return (
        f"n={s['n']:3d}  hit={s['hit_rate']:.3f}  "
        f"mrr={s['mrr']:.3f}  mttc={s['mttc']:.2f}  misses={s['misses']}"
    )


def print_section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def group_report(rows: list[dict], key_fn, title: str, min_n: int = 1, top: int | None = None) -> list[tuple]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[str(key_fn(r))].append(r)

    overall = summarize(rows)
    ranked = []
    for name, items in groups.items():
        s = summarize(items)
        # How much this group pulls overall hit/mrr/mttc vs leaving it out
        others = [r for r in rows if str(key_fn(r)) != name]
        without = summarize(others)
        delta_hit = (overall["hit_rate"] - without["hit_rate"]) if without["n"] else 0.0
        delta_mrr = (overall["mrr"] - without["mrr"]) if without["n"] else 0.0
        delta_mttc = (overall["mttc"] - without["mttc"]) if without["n"] else 0.0
        ranked.append((name, s, delta_hit, delta_mrr, delta_mttc))

    # Sort by hit rate ascending (worst first), then by MTTC descending
    ranked.sort(key=lambda x: (x[1]["hit_rate"], -x[1]["mttc"], -x[1]["n"]))
    if top is not None:
        show = ranked[:top]
    else:
        show = [x for x in ranked if x[1]["n"] >= min_n]

    print_section(title)
    print(f"{'group':<42} {'metrics':<48} {'Δhit':>7} {'Δmrr':>7} {'Δmttc':>7}")
    print("-" * 112)
    for name, s, dh, dm, dt in show:
        label = name if len(name) <= 42 else name[:39] + "..."
        print(f"{label:<42} {fmt(s):<48} {dh:+.3f} {dm:+.3f} {dt:+.2f}")
    print("\nΔ* = overall − overall_without_group  (negative Δhit/Δmrr => group drags metric down)")
    return ranked


def hist(values: list, bins: list[tuple[str, callable]]) -> None:
    for label, pred in bins:
        n = sum(1 for v in values if pred(v))
        bar = "#" * n
        print(f"  {label:<16} {n:3d} {bar}")


def main() -> None:
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    sessions = {s["sample_id"]: s for s in results["sessions"]}
    public = {r["sample_id"]: r for r in load_jsonl(PUBLIC_SET)}

    needed = {public[sid]["ground_truth"]["parent_asin"] for sid in sessions if sid in public}
    catalog: dict[str, dict] = {}
    with CATALOG.open(encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            asin = str(p["parent_asin"])
            if asin in needed:
                catalog[asin] = p

    rows = []
    missing_public = missing_catalog = 0
    for sid, sess in sessions.items():
        sample = public.get(sid)
        if sample is None:
            missing_public += 1
            continue
        asin = sample["ground_truth"]["parent_asin"]
        product = catalog.get(asin, {})
        if not product:
            missing_catalog += 1
        cats = product.get("categories") or []
        rows.append(
            {
                **sess,
                "difficulty": sample.get("difficulty_bucket", "?"),
                "category_bucket": sample.get("category_bucket", "?"),
                "parent_asin": asin,
                "title": (product.get("title") or "")[:80],
                "store": product.get("store") or "(none)",
                "price": product.get("price"),
                "price_bucket": price_bucket(product.get("price")),
                "avg_rating": product.get("average_rating"),
                "rating_bucket": rating_bucket(product.get("average_rating")),
                "leaf": leaf_category(cats),
                "cat_l2": category_path(cats, 2),
                "cat_l3": category_path(cats, 3),
                "categories": cats,
            }
        )

    overall = summarize(rows)
    print_section("OVERALL")
    print(f"samples joined: {len(rows)}  (missing public={missing_public}, missing catalog={missing_catalog})")
    print(f"reported: hit_rate_at_10={results['hit_rate_at_10']}  mrr={results['mrr']}  mttc={results['mttc']}")
    print(f"recomputed: {fmt(overall)}")

    # --- Distributions ---
    print_section("HIT / MISS")
    hits = [r for r in rows if r["hit"]]
    misses = [r for r in rows if not r["hit"]]
    print(f"hits={len(hits)}  misses={len(misses)}  hit_rate={len(hits)/len(rows):.3f}")

    print_section("MRR DISTRIBUTION (reciprocal_rank)")
    rr = [r["reciprocal_rank"] for r in rows]
    print(f"mean={statistics.fmean(rr):.4f}  median={statistics.median(rr):.4f}")
    print("by best_rank / RR bucket:")
    hist(
        rows,
        [
            ("miss (rr=0)", lambda r: not r["hit"]),
            ("rank 1 (1.0)", lambda r: r.get("best_rank") == 1),
            ("rank 2 (0.5)", lambda r: r.get("best_rank") == 2),
            ("rank 3-5", lambda r: r.get("best_rank") in {3, 4, 5}),
            ("rank 6-10", lambda r: isinstance(r.get("best_rank"), int) and 6 <= r["best_rank"] <= 10),
        ],
    )

    print_section("MTTC DISTRIBUTION (first_hit_turn; miss=11)")
    turns = [mttc_value(r) for r in rows]
    print(f"mean={statistics.fmean(turns):.3f}  median={statistics.median(turns):.1f}")
    counts = Counter(turns)
    for t in range(1, MISS_MTTC + 1):
        n = counts.get(t, 0)
        label = f"turn {t}" if t <= MAX_TURNS else "miss (=11)"
        print(f"  {label:<12} {n:3d} {'#' * n}")

    # Late hits also inflate MTTC even when hit=True
    late = [r for r in rows if r["hit"] and mttc_value(r) >= 8]
    print(f"\nlate hits (first_hit_turn >= 8): {len(late)}  — these inflate MTTC without hurting hit rate")

    # --- Breakdowns ---
    group_report(rows, lambda r: r["scenario_type"], "BY SCENARIO_TYPE")
    group_report(rows, lambda r: r["difficulty"], "BY DIFFICULTY_BUCKET")
    group_report(rows, lambda r: r["price_bucket"], "BY PRICE BUCKET")
    group_report(rows, lambda r: r["rating_bucket"], "BY AVG RATING BUCKET")
    group_report(rows, lambda r: r["cat_l2"], "BY CATALOG CATEGORY (depth 2)", min_n=3)
    group_report(rows, lambda r: r["cat_l3"], "BY CATALOG CATEGORY (depth 3)", min_n=3)
    group_report(rows, lambda r: r["leaf"], "BY LEAF CATEGORY (n>=3)", min_n=3)
    group_report(rows, lambda r: r["store"], "BY STORE (n>=3)", min_n=3)

    # Scenario × difficulty
    group_report(
        rows,
        lambda r: f"{r['scenario_type']} × {r['difficulty']}",
        "BY SCENARIO × DIFFICULTY",
    )

    # Worst leaf categories by drag on hit rate (n>=3)
    print_section("TOP DRAG GROUPS ON HIT RATE (leaf category, n>=3)")
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["leaf"]].append(r)
    drag = []
    for name, items in groups.items():
        if len(items) < 3:
            continue
        s = summarize(items)
        without = summarize([r for r in rows if r["leaf"] != name])
        drag.append((overall["hit_rate"] - without["hit_rate"], name, s))
    drag.sort(key=lambda x: x[0])  # most negative first
    print(f"{'Δhit':>7}  {'leaf':<40}  metrics")
    for dh, name, s in drag[:15]:
        print(f"{dh:+.3f}  {name[:40]:<40}  {fmt(s)}")

    print_section("MISSES — SAMPLE LIST (with product context)")
    print(f"{'sample_id':<14} {'scenario':<16} {'diff':<8} {'leaf':<28} title")
    for r in sorted(misses, key=lambda x: (x["scenario_type"], x["leaf"], x["sample_id"])):
        print(
            f"{r['sample_id']:<14} {r['scenario_type']:<16} {r['difficulty']:<8} "
            f"{r['leaf'][:28]:<28} {r['title'][:50]}"
        )

    print_section("LATE HITS (turn>=8) — inflate MTTC")
    print(f"{'sample_id':<14} {'turn':>4} {'rank':>4} {'scenario':<16} {'leaf':<28} title")
    for r in sorted(late, key=lambda x: (-mttc_value(x), x["sample_id"])):
        print(
            f"{r['sample_id']:<14} {mttc_value(r):4d} {r.get('best_rank') or '-':>4} "
            f"{r['scenario_type']:<16} {r['leaf'][:28]:<28} {r['title'][:45]}"
        )

    # Pattern summary: miss leaf concentration
    print_section("MISS CONCENTRATION")
    miss_leaves = Counter(r["leaf"] for r in misses)
    print("leaf categories with most misses:")
    for leaf, n in miss_leaves.most_common(15):
        total_leaf = sum(1 for r in rows if r["leaf"] == leaf)
        print(f"  {n:2d}/{total_leaf:<3d} miss rate={n/total_leaf:.2f}  {leaf}")

    miss_scen = Counter(r["scenario_type"] for r in misses)
    print("\nmisses by scenario:")
    for k, n in miss_scen.most_common():
        total = sum(1 for r in rows if r["scenario_type"] == k)
        print(f"  {k:<16} {n:2d}/{total} ({n/total:.1%})")

    miss_diff = Counter(r["difficulty"] for r in misses)
    print("\nmisses by difficulty:")
    for k, n in miss_diff.most_common():
        total = sum(1 for r in rows if r["difficulty"] == k)
        print(f"  {k:<16} {n:2d}/{total} ({n/total:.1%})")


if __name__ == "__main__":
    main()
