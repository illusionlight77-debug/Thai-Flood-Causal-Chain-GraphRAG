"""Experiment 1 — Structure ablation: does the CAUSAL TOPOLOGY carry information,
or does the system merely have more data?

Design (information-matched): every variant sees the SAME nodes, the SAME evidence and
the SAME signal values. Only the *topology* — which river reach is wired to which
province — is changed. We permute the province->reach assignment, preserving the exact
degree structure, so the amount of information is identical and only the causal wiring
differs. Repeating the permutation gives a null distribution and a permutation-test
p-value for the causal wiring.

  Test A  fluvial topology only   : causal reach->province   vs  permuted reach->province
  Test B  full model              : (fluvial u pluvial)      vs  permuted fluvial
  Test C  pluvial locality        : true province rain       vs  permuted province rain

Baselines (entity-graphrag, vector-rag) are read from the frozen web/ui_data_*.json.

Usage: python -m src.eval.structure_ablation [--n 2000]
"""
from __future__ import annotations

import argparse
import json
import math
import random

from src.config import settings

_PROC = settings.data_processed_dir
_WEB = settings.data_processed_dir.parent.parent / "web"
EVENTS = ["2021", "2022", "2023", "2024", "2025"]
PROT = {"BANGKOK", "NONTHABURI"}


def _mcc(tp, fp, fn, tn):
    d = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / d if d else 0.0


def _f1(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def _load():
    import src.ingest.fixtures as fx
    allp = sorted(fx.PROVINCES)
    prov_reach = {}
    for r, lst in fx.REACH_INUNDATION.items():
        for pid, _ in lst:
            prov_reach.setdefault(pid, set()).add(r)
    per_event = {}
    for y in EVENTS:
        over = json.loads((_PROC / f"river_reach_overbank_{y}.json").read_text("utf-8"))["overflow"]
        lr = json.loads((_PROC / f"local_rain_{y}.json").read_text("utf-8"))["local_rain"]
        gold = set(json.loads((_PROC / f"ground_truth_{y}.json").read_text("utf-8"))["gold_flooded"])
        rain = {p: bool(v.get("over_3day") or v.get("over_30day")) for p, v in lr.items()}
        per_event[y] = {"over": over, "rain": rain, "gold": gold}
    return allp, prov_reach, per_event


def _score(allp, assign_reach, assign_rain, per_event, use_fluvial=True, use_pluvial=True):
    """assign_reach/assign_rain: province -> province whose signal it receives (identity = true)."""
    agg = [0, 0, 0, 0]
    for y in EVENTS:
        E = per_event[y]
        for pid in allp:
            if pid in PROT:
                pred = False
            else:
                f = False
                if use_fluvial:
                    src = assign_reach[pid]
                    f = any(E["over"].get(r) for r in PROV_REACH.get(src, ()))
                p = bool(E["rain"].get(assign_rain[pid])) if use_pluvial else False
                pred = f or p
            g = pid in E["gold"]
            agg[0 if (pred and g) else 1 if (pred and not g) else 2 if (not pred and g) else 3] += 1
    return agg


def run(n_perm=2000, seed=42):
    global PROV_REACH
    allp, PROV_REACH, per_event = _load()
    ident = {p: p for p in allp}
    rng = random.Random(seed)

    def perm_map():
        sh = allp[:]
        rng.shuffle(sh)
        return dict(zip(allp, sh))

    out = {"n_permutations": n_perm}
    for name, uf, up, perm_reach, perm_rain in [
            ("A_fluvial_topology", True, False, True, False),
            ("B_full_model", True, True, True, False),
            ("C_pluvial_locality", False, True, False, True)]:
        obs = _score(allp, ident, ident, per_event, uf, up)
        obs_mcc, obs_f1 = _mcc(*obs), _f1(*obs[:3])
        null = []
        for _ in range(n_perm):
            ar = perm_map() if perm_reach else ident
            an = perm_map() if perm_rain else ident
            a = _score(allp, ar, an, per_event, uf, up)
            null.append(_mcc(*a))
        null.sort()
        ge = sum(1 for v in null if v >= obs_mcc)
        out[name] = {
            "observed_mcc": round(obs_mcc, 3), "observed_f1": round(obs_f1, 3),
            "observed_confusion": {"tp": obs[0], "fp": obs[1], "fn": obs[2], "tn": obs[3]},
            "null_mean_mcc": round(sum(null) / len(null), 3),
            "null_p95_mcc": round(null[int(0.95 * (len(null) - 1))], 3),
            "null_max_mcc": round(null[-1], 3),
            "p_value": round((ge + 1) / (n_perm + 1), 4),
        }
    # frozen baselines
    base = {}
    for s in ("entity-graphrag", "vector-rag"):
        a = [0, 0, 0, 0]
        for y in EVENTS:
            cm = json.loads((_WEB / f"ui_data_{y}.json").read_text("utf-8"))["confusion"][s]
            for i, k in enumerate(("tp", "fp", "fn", "tn")):
                a[i] += cm[k]
        base[s] = {"mcc": round(_mcc(*a), 3), "f1": round(_f1(*a[:3]), 3),
                   "specificity": round(a[3] / (a[3] + a[1]), 3) if a[3] + a[1] else 0.0}
    out["frozen_baselines"] = base
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    a = ap.parse_args()
    res = run(a.n)
    (_PROC / "structure_ablation.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    print(f"permutations = {res['n_permutations']}")
    for k in ("A_fluvial_topology", "B_full_model", "C_pluvial_locality"):
        v = res[k]
        print(f"{k:22s} observed MCC={v['observed_mcc']:+.3f} | null mean={v['null_mean_mcc']:+.3f} "
              f"p95={v['null_p95_mcc']:+.3f} max={v['null_max_mcc']:+.3f} | p={v['p_value']}")
    print("frozen baselines:", res["frozen_baselines"])


if __name__ == "__main__":
    main()
