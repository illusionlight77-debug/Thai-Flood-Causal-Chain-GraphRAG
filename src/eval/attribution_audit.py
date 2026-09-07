"""Experiment 2 + decisive controls — is the causal gate doing any work?

(a) TRIVIAL-BASELINE CONTROL. Compares the causal gate against spatially-blind rules on
    the same universe. The critical one is 'predict-all except dike-protected provinces',
    which uses no causal graph at all.
(b) MECHANISM AGREEMENT. For every true positive, records which mechanisms fired and by
    what margin (value/threshold - 1). A TP resting on a single, barely-exceeded,
    non-specific signal is a weak attribution: 'right for the wrong reason'.

Usage: python -m src.eval.attribution_audit
"""
from __future__ import annotations

import json
import math

from src.config import settings

_PROC = settings.data_processed_dir
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
    prov_reach = {}
    for r, lst in fx.REACH_INUNDATION.items():
        for pid, _ in lst:
            prov_reach.setdefault(pid, set()).add(r)
    E = {}
    for y in EVENTS:
        rb = json.loads((_PROC / f"river_reach_overbank_{y}.json").read_text("utf-8"))
        E[y] = {"ro": rb["reach_overbank"], "over": rb["overflow"],
                "lr": json.loads((_PROC / f"local_rain_{y}.json").read_text("utf-8"))["local_rain"],
                "gold": set(json.loads((_PROC / f"ground_truth_{y}.json").read_text("utf-8"))["gold_flooded"])}
    return sorted(fx.PROVINCES), prov_reach, E


def _margins(pid, y, prov_reach, E):
    d = E[y]
    out = {}
    for r in prov_reach.get(pid, ()):
        if d["over"].get(r):
            best = 0.0
            for s in d["ro"].get(r, {}).get("stations", []):
                ps, th = s.get("peak_stage"), s.get("threshold_2yr_stage")
                if s.get("over_bank") and ps and th:
                    best = max(best, ps / th - 1)
            out["fluvial"] = max(out.get("fluvial", 0.0), best)
    v = d["lr"].get(pid, {})
    for key, pk, tk in (("pluvial3", "event_max_3day_mm", "threshold_3day_T10_mm"),
                        ("pluvial30", "event_max_30day_mm", "threshold_30day_T10_mm")):
        flag = "over_3day" if key == "pluvial3" else "over_30day"
        if v.get(flag) and v.get(tk):
            out[key] = v[pk] / v[tk] - 1
    return out


def run():
    allp, prov_reach, E = _load()
    nonprot = [p for p in allp if p not in PROT]

    def causal(pid, y):
        return False if pid in PROT else bool(_margins(pid, y, prov_reach, E))

    def ev(predfn, universe):
        a = [0, 0, 0, 0]
        for y in EVENTS:
            for pid in universe:
                pr, g = predfn(pid, y), pid in E[y]["gold"]
                a[0 if (pr and g) else 1 if (pr and not g) else 2 if (not pr and g) else 3] += 1
        return a

    variants = {
        "causal_gate_23prov": (causal, allp),
        "predict_all_minus_protected_23prov": (lambda p, y: p not in PROT, allp),
        "predict_all_23prov": (lambda p, y: True, allp),
        "causal_gate_21nonprotected": (causal, nonprot),
        "predict_all_21nonprotected": (lambda p, y: True, nonprot),
    }
    baselines = {}
    for name, (fn, uni) in variants.items():
        a = ev(fn, uni)
        baselines[name] = {"mcc": round(_mcc(*a), 3), "f1": round(_f1(*a[:3]), 3),
                           "tp": a[0], "fp": a[1], "fn": a[2], "tn": a[3]}

    # (a2) warning-skill view of the same control (Plan B)
    def _warn(a):
        tp, fp, fn_, tn = a
        return {"pod": round(tp / (tp + fn_), 3) if tp + fn_ else 0.0,
                "far": round(fp / (tp + fp), 3) if tp + fp else 0.0,
                "csi": round(tp / (tp + fp + fn_), 3) if tp + fp + fn_ else 0.0}
    warning = {
        "causal_gate": _warn(ev(causal, allp)),
        "trivial_warn_all_except_protected": _warn(ev(lambda p, y: p not in PROT, allp)),
        "trivial_warn_everything": _warn(ev(lambda p, y: True, allp)),
    }

    tps = []
    for y in EVENTS:
        for pid in nonprot:
            m = _margins(pid, y, prov_reach, E)
            if m and pid in E[y]["gold"]:
                tps.append({"event": y, "province": pid,
                            "mechanisms": {k: round(v, 3) for k, v in m.items()},
                            "n_mech": len(m), "max_margin": round(max(m.values()), 3)})
    n = len(tps)
    multi = [t for t in tps if t["n_mech"] >= 2]
    only30 = [t for t in tps if list(t["mechanisms"]) == ["pluvial30"]]
    weak = [t for t in tps if t["n_mech"] == 1 and t["max_margin"] < 0.20]
    mech = {
        "n_true_positives": n,
        "corroborated_ge2_mechanisms": {"n": len(multi), "pct": round(len(multi) / n, 3)},
        "single_mechanism": {"n": n - len(multi), "pct": round((n - len(multi)) / n, 3)},
        "only_nonspecific_30day": {"n": len(only30), "pct": round(len(only30) / n, 3),
                                   "cases": [f"{t['event']} {t['province']} (margin {t['max_margin']})"
                                             for t in only30]},
        "single_and_thin_margin_lt20pct": {"n": len(weak), "pct": round(len(weak) / n, 3)},
        "saraburi_by_year": {y: {"gold": "SARABURI" in E[y]["gold"],
                                 "mechanisms": {k: round(v, 3)
                                                for k, v in _margins("SARABURI", y, prov_reach, E).items()}}
                             for y in EVENTS},
    }
    return {"note": "Trivial-baseline control + mechanism-agreement audit of the causal gate.",
            "trivial_baselines": baselines, "warning_skill_control": warning,
            "mechanism_agreement": mech}


def main():
    res = run()
    (_PROC / "attribution_audit.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    print("=== (a) trivial-baseline control ===")
    for k, v in res["trivial_baselines"].items():
        print(f"  {k:38s} MCC={v['mcc']:+.3f} F1={v['f1']:.3f}  tp{v['tp']}/fp{v['fp']}/fn{v['fn']}/tn{v['tn']}")
    print("=== (a2) warning-skill control (Plan B) ===")
    for k, v in res["warning_skill_control"].items():
        print(f"  {k:38s} POD={v['pod']:.3f} FAR={v['far']:.3f} CSI={v['csi']:.3f}")
    m = res["mechanism_agreement"]
    print("=== (b) mechanism agreement ===")
    print(f"  TPs={m['n_true_positives']} | corroborated {m['corroborated_ge2_mechanisms']['pct']:.0%}"
          f" | single {m['single_mechanism']['pct']:.0%}"
          f" | only-30day {m['only_nonspecific_30day']['pct']:.0%}"
          f" | single+thin {m['single_and_thin_margin_lt20pct']['pct']:.0%}")
    for y, v in m["saraburi_by_year"].items():
        print(f"    Saraburi {y}: gold={v['gold']} mech={v['mechanisms']}")


if __name__ == "__main__":
    main()
