"""Plan A re-scope (A) — DISTRICT-level evaluation.

At province level the flood base rate is 0.73, so almost everything floods and there is
nothing to discriminate: a trivial 'predict all except dike-protected' rule beats the
causal gate (see attribution_audit). Moving to district (amphoe) resolution drops the
base rate to ~0.20-0.26, which restores a meaningful classification problem.

Gold  : tambon-level GISTDA flooded area (thaiwater YearlyReport) aggregated to amphoe,
        same fixed cutoff of >= 10,000 rai as the province evaluation.
Signals (de-circularized, unchanged in spirit):
  fluvial : the reach(es) of the district's province over-top (inherited from the
            province-level reach gate - districts share their province's river signal)
  pluvial : the DISTRICT's own peak 3-day or 30-day rainfall exceeds the district's own
            10-year Gumbel return level (ERA5-Land at the district centroid)
Controls: trivial baselines + an information-matched permutation test that rewires which
district receives which rainfall signal.

Usage: python -m src.eval.district_eval [--n 2000]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random

from src.config import settings

_PROC = settings.data_processed_dir
EVENTS = ["2023", "2024"]
CUTOFF_RAI = 10000
PROT = {"BANGKOK", "NONTHABURI"}


def _mcc(tp, fp, fn, tn):
    d = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / d if d else 0.0


def _f1(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def _stats(a):
    tp, fp, fn, tn = a
    return {"mcc": round(_mcc(*a), 3), "f1": round(_f1(tp, fp, fn), 3),
            "recall": round(tp / (tp + fn), 3) if tp + fn else 0.0,
            "specificity": round(tn / (tn + fp), 3) if tn + fp else 0.0,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def _load():
    import src.ingest.fixtures as fx
    prov_reach = {}
    for r, lst in fx.REACH_INUNDATION.items():
        for pid, _ in lst:
            prov_reach.setdefault(pid, set()).add(r)
    rain = json.loads((_PROC / "district_rain.json").read_text("utf-8"))
    gold = {}
    with open(_PROC / "district_flood_all.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = f"{row['pid']}|{row['dnorm']}"
            if key in rain:
                gold.setdefault(row["year"], {})[key] = float(row["rai"])
    over = {y: json.loads((_PROC / f"river_reach_overbank_{y}.json").read_text("utf-8"))["overflow"]
            for y in EVENTS}
    districts = sorted(k for k in rain if all(k in gold[y] for y in EVENTS))
    return districts, prov_reach, rain, gold, over


def _pluvial(rain, key, y):
    r = rain[key]
    for n in ("3", "30"):
        t = r[n].get("t10")
        if t and r[n].get(y, 0.0) >= t:
            return True
    return False


def run(n_perm=2000, seed=42):
    districts, prov_reach, rain, gold, over = _load()

    def fluvial(key, y):
        pid = key.split("|")[0]
        return any(over[y].get(r) for r in prov_reach.get(pid, ()))

    def is_gold(key, y):
        return gold[y][key] >= CUTOFF_RAI

    def ev(predfn, rain_assign=None):
        a = [0, 0, 0, 0]
        for y in EVENTS:
            for k in districts:
                pr = predfn(k, y, rain_assign)
                g = is_gold(k, y)
                a[0 if (pr and g) else 1 if (pr and not g) else 2 if (not pr and g) else 3] += 1
        return a

    def causal(k, y, assign=None):
        if k.split("|")[0] in PROT:
            return False
        src = assign[k] if assign else k
        return fluvial(k, y) or _pluvial(rain, src, y)

    variants = {
        "causal_fluvial_plus_pluvial": causal,
        "fluvial_only": lambda k, y, a=None: (k.split("|")[0] not in PROT) and fluvial(k, y),
        "pluvial_only": lambda k, y, a=None: (k.split("|")[0] not in PROT) and _pluvial(rain, k, y),
        "trivial_predict_all": lambda k, y, a=None: True,
        "trivial_all_except_protected": lambda k, y, a=None: k.split("|")[0] not in PROT,
    }
    results = {name: _stats(ev(fn)) for name, fn in variants.items()}

    # permutation test: rewire which district receives which rainfall signal
    rng = random.Random(seed)
    obs = _mcc(*ev(causal))
    null = []
    for _ in range(n_perm):
        sh = districts[:]
        rng.shuffle(sh)
        null.append(_mcc(*ev(causal, dict(zip(districts, sh)))))
    null.sort()
    ge = sum(1 for v in null if v >= obs)

    n_cases = len(districts) * len(EVENTS)
    n_gold = sum(1 for y in EVENTS for k in districts if is_gold(k, y))
    return {
        "note": "District-level evaluation (Plan A re-scope). Gold = tambon GISTDA aggregated to "
                "amphoe, cutoff >= 10,000 rai (same as province).",
        "n_districts": len(districts), "n_events": len(EVENTS), "n_cases": n_cases,
        "base_rate": round(n_gold / n_cases, 3),
        "variants": results,
        "permutation_test_pluvial_locality": {
            "observed_mcc": round(obs, 3), "null_mean": round(sum(null) / len(null), 3),
            "null_p95": round(null[int(0.95 * (len(null) - 1))], 3),
            "p_value": round((ge + 1) / (n_perm + 1), 4), "n_permutations": n_perm},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    a = ap.parse_args()
    res = run(a.n)
    (_PROC / "district_eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    print(f"districts={res['n_districts']} events={res['n_events']} cases={res['n_cases']} "
          f"base_rate={res['base_rate']}")
    print(f"{'variant':34s} {'MCC':>7s} {'F1':>6s} {'recall':>7s} {'spec':>6s}")
    for k, v in res["variants"].items():
        print(f"{k:34s} {v['mcc']:+7.3f} {v['f1']:6.3f} {v['recall']:7.3f} {v['specificity']:6.3f}")
    p = res["permutation_test_pluvial_locality"]
    print(f"permutation (rain locality): observed={p['observed_mcc']:+.3f} "
          f"null mean={p['null_mean']:+.3f} p95={p['null_p95']:+.3f} p={p['p_value']}")


if __name__ == "__main__":
    main()
