"""Pooled bootstrap significance across events — increases statistical power by
resampling the UNION of (event, province) cases from both clean Chao Phraya events
(2022 + 2021) instead of one event's ~23 provinces. This is the honest way to raise N
for the significance test: 2 events x 23 provinces = 46 cases, same universe, same rule.

Why pooling and not adding 2011: the GISTDA 2011 satellite product is published only as
regional aggregates + top-3 per region on the reachable pages (HII/thaiwater), not a full
per-province table with the >=10,000-rai cutoff. Building a 2011 gold would require
hand-assigning province labels, which METHODOLOGY.md forbids. Logged as a data limitation
in README (Bugs) rather than faked.

Reads web/ui_data_{2022,2021}.json (which already hold per-province predicts_this + is_gold
for all 3 systems), reconstructs per-case labels, and runs a paired bootstrap.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from src.config import settings

WEB = Path(__file__).resolve().parent.parent.parent / "web"
EVENTS = ["2022", "2021"]
SYSTEMS = ["causal-graphrag", "entity-graphrag", "vector-rag"]


def _cases() -> list[dict]:
    """แต่ละ case = (event, province) พร้อม gold + predict ของ 3 ระบบ."""
    cases = []
    for y in EVENTS:
        f = WEB / f"ui_data_{y}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text("utf-8"))
        for prov in d["provinces"]:
            pp = d["per_province"][prov]
            cases.append({
                "event": y, "prov": prov, "gold": bool(pp["is_gold"]),
                **{s: bool(pp["systems"][s].get("predicts_this", False)) for s in SYSTEMS},
            })
    return cases


def _f1_on(sample: list[dict], s: str) -> float:
    tp = sum(1 for c in sample if c[s] and c["gold"])
    pc = sum(1 for c in sample if c[s])
    gc = sum(1 for c in sample if c["gold"])
    prec = tp / pc if pc else 0.0
    rec = tp / gc if gc else 0.0
    return 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0


def run(n: int = 5000, seed: int = 0) -> dict:
    cases = _cases()
    N = len(cases)
    rng = random.Random(seed)
    dist = {s: [] for s in SYSTEMS}
    diffs = []
    for _ in range(n):
        smp = [cases[rng.randrange(N)] for _ in range(N)]
        f = {s: _f1_on(smp, s) for s in SYSTEMS}
        for s in SYSTEMS:
            dist[s].append(f[s])
        diffs.append(f["causal-graphrag"] - f["entity-graphrag"])
    out = {"n_cases": N, "events": EVENTS, "bootstrap_n": n, "systems": {}}
    for s in SYSTEMS:
        xs = sorted(dist[s])
        out["systems"][s] = {"f1_mean": round(sum(xs) / n, 3),
                             "ci95": [round(xs[int(0.025 * n)], 3), round(xs[int(0.975 * n)], 3)]}
    ds = sorted(diffs)
    out["paired_causal_vs_entity"] = {
        "mean_diff": round(sum(diffs) / n, 3),
        "ci95": [round(ds[int(0.025 * n)], 3), round(ds[int(0.975 * n)], 3)],
        "prob_causal_better": round(sum(1 for d in diffs if d > 0) / n, 3),
        "significant_95": bool(ds[int(0.025 * n)] > 0),  # lower CI bound > 0
    }
    return out


def main() -> None:
    res = run()
    p = settings.data_processed_dir / "pooled_significance.json"
    p.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    print(f"pooled over {res['n_cases']} (event,province) cases from {res['events']}:")
    for s, v in res["systems"].items():
        print(f"  {s:16s} F1 {v['f1_mean']} CI{v['ci95']}")
    pc = res["paired_causal_vs_entity"]
    print(f"  paired causal-entity: diff {pc['mean_diff']} CI{pc['ci95']} "
          f"P={pc['prob_causal_better']} significant95={pc['significant_95']}")
    print(f"-> {p}")


if __name__ == "__main__":
    main()
