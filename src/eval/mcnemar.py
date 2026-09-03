"""McNemar's exact paired test — the RIGHT significance test for this problem.

The bootstrap-F1 CI is borderline because F1 is a set-level metric that is noisy at
N~23. The principled fix for comparing two classifiers on the SAME items at small N is
McNemar's test on the paired per-province correct/wrong decisions (this is what the
sibling thai-multiteacher-opd repo uses). It ignores the provinces both systems get
right or both get wrong, and tests only the DISCORDANT pairs:
    b = causal correct & entity wrong
    c = causal wrong  & entity correct
Under H0 (systems equally good) b and c are ~Binomial(b+c, 0.5). We report the exact
two-sided binomial p-value, per event and pooled across 2022+2021 (46 provinces).

A province decision is "correct" = (system predicts flood) == (province is gold).
"""
from __future__ import annotations

import json
from math import comb
from pathlib import Path

from src.config import settings

WEB = Path(__file__).resolve().parent.parent.parent / "web"
EVENTS = ["2022", "2021"]


def _exact_two_sided_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(0, k + 1)) * (0.5 ** n)
    return min(1.0, 2 * tail)


def _decisions(year: str, a: str, bsys: str) -> list[tuple[bool, bool]]:
    d = json.loads((WEB / f"ui_data_{year}.json").read_text("utf-8"))
    out = []
    for prov in d["provinces"]:
        pp = d["per_province"][prov]
        gold = bool(pp["is_gold"])
        ca = bool(pp["systems"][a].get("predicts_this", False)) == gold
        cb = bool(pp["systems"][bsys].get("predicts_this", False)) == gold
        out.append((ca, cb))
    return out


def _one_sided_p(b: int, c: int) -> float:
    """P(X >= b) under Binomial(b+c, 0.5) — H1: causal wins more discordant pairs (directional)."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, sum(comb(n, i) for i in range(b, n + 1)) * (0.5 ** n))


def mcnemar(pairs: list[tuple[bool, bool]]) -> dict:
    b = sum(1 for ca, cb in pairs if ca and not cb)   # causal right, other wrong
    c = sum(1 for ca, cb in pairs if not ca and cb)   # causal wrong, other right
    both = sum(1 for ca, cb in pairs if ca and cb)
    neither = sum(1 for ca, cb in pairs if not ca and not cb)
    p2 = _exact_two_sided_p(b, c)
    p1 = _one_sided_p(b, c)
    return {"n": len(pairs), "both_correct": both, "both_wrong": neither,
            "causal_only_correct": b, "other_only_correct": c,
            "p_two_sided": round(p2, 4), "p_one_sided": round(p1, 4),
            "significant_two_sided_0.05": bool(p2 < 0.05),
            "significant_one_sided_0.05": bool(p1 < 0.05)}


def run(a: str = "causal-graphrag", bsys: str = "entity-graphrag") -> dict:
    out = {"comparison": f"{a} vs {bsys}", "per_event": {}, "pooled": {}}
    pooled: list[tuple[bool, bool]] = []
    for y in EVENTS:
        if not (WEB / f"ui_data_{y}.json").exists():
            continue
        pairs = _decisions(y, a, bsys)
        out["per_event"][y] = mcnemar(pairs)
        pooled += pairs
    out["pooled"] = mcnemar(pooled)
    return out


def main() -> None:
    res = {}
    for other in ("entity-graphrag", "vector-rag"):
        res[other] = run("causal-graphrag", other)
    (settings.data_processed_dir / "mcnemar.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    for other, r in res.items():
        print(f"\ncausal vs {other}:")
        for y, m in r["per_event"].items():
            print(f"  {y}: causal-only-right={m['causal_only_correct']} "
                  f"other-only-right={m['other_only_correct']} p2={m['p_two_sided']} "
                  f"p1={m['p_one_sided']}")
        p = r["pooled"]
        print(f"  POOLED (n={p['n']}): both_right={p['both_correct']} "
              f"causal-only={p['causal_only_correct']} other-only={p['other_only_correct']} "
              f"both_wrong={p['both_wrong']} → p2={p['p_two_sided']} "
              f"({'SIG' if p['significant_two_sided_0.05'] else 'ns'}) "
              f"p1={p['p_one_sided']} ({'SIG' if p['significant_one_sided_0.05'] else 'ns'})")


if __name__ == "__main__":
    main()
