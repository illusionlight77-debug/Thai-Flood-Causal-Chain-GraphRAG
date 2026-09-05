"""Roadmap B — Probabilistic warning verification (ทำ B ให้แข็งพอเป็นเล่มเดี่ยว).

ยกระดับการประเมินคำเตือนจาก "Brier ดิบ" → มาตรฐานการ verify พยากรณ์ความน่าจะเป็นเต็มรูป:
  • Brier + Murphy (1973) decomposition: reliability − resolution + uncertainty
  • Brier Skill Score (BSS) เทียบ climatology (Pappenberger et al. 2015 — benchmark)
  • Expected Calibration Error (ECE) + reliability diagram bins (Guo 2017 / Naeini 2015)
  • sharpness (Gneiting et al. 2007) — sharp เท่าที่ยัง calibrated
  • เทียบ calibrator หลายแบบ **แบบ leave-one-event-out (prequential, กัน overfit):**
      const · climatology · empirical-by-hop · Platt (logistic) · isotonic
    หมายเหตุ (survey): ข้อมูลน้อย (~64 คำเตือน) → **isotonic เสี่ยง overfit, Platt ปลอดภัยกว่า**
    (Niculescu-Mizil & Caruana 2005) → รายงานทั้งคู่ ให้เห็นตรง ๆ
  • bootstrap 95% CI ของ Brier/BSS · drift monitor (CSI ตามลำดับเวลา)

*ไม่แตะกราฟ/gate* — ปรับเฉพาะชั้นความน่าจะเป็น (กติกากัน overfit, ดู FORECASTING_ROADMAP.md).

Input : data/processed/case_bank.json
Output: data/processed/warning_verification.json

Usage:  python -m src.eval.warning_verification
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from statistics import pstdev

from src.config import settings

_PROC = settings.data_processed_dir
_BANK = _PROC / "case_bank.json"
_OUT = _PROC / "warning_verification.json"
P_CONST = 0.938
_YEAR_ORDER = ["2021", "2022", "2023", "2024", "2025"]   # chronological (+2568 GISTDA)
random.seed(20260905)


# ---------- metrics ----------
def _brier(ps, gs):
    return sum((p - g) ** 2 for p, g in zip(ps, gs)) / len(ps)


def _decomp(ps, gs, nbins=10):
    """Murphy 1973: BS = reliability - resolution + uncertainty (bin by forecast prob)."""
    obar = sum(gs) / len(gs)
    unc = obar * (1 - obar)
    # group by rounded prob (ข้อมูลมีค่าไม่ต่อเนื่องมาก) — ใช้ค่า distinct เป็น bin
    groups: dict[float, list[int]] = {}
    for p, g in zip(ps, gs):
        groups.setdefault(round(p, 3), []).append(g)
    rel = res = 0.0
    N = len(ps)
    for pk, gk in groups.items():
        nk = len(gk); ok = sum(gk) / nk
        rel += nk / N * (pk - ok) ** 2
        res += nk / N * (ok - obar) ** 2
    bss = (res - rel) / unc if unc else 0.0
    return {"reliability": round(rel, 4), "resolution": round(res, 4),
            "uncertainty": round(unc, 4), "bss_vs_climatology": round(bss, 3)}


def _ece(ps, gs, bins=(0, .7, .85, .95, 1.01)):
    N = len(ps); e = 0.0; diag = []
    for lo, hi in zip(bins, bins[1:]):
        idx = [i for i, p in enumerate(ps) if lo <= p < hi]
        if not idx:
            continue
        conf = sum(ps[i] for i in idx) / len(idx)
        acc = sum(gs[i] for i in idx) / len(idx)
        e += len(idx) / N * abs(conf - acc)
        diag.append({"bin": f"{lo:.2f}-{hi:.2f}", "n": len(idx),
                     "mean_pred": round(conf, 3), "obs_freq": round(acc, 3)})
    return round(e, 4), diag


def _all_metrics(ps, gs):
    d = _decomp(ps, gs)
    ece, diag = _ece(ps, gs)
    return {"brier": round(_brier(ps, gs), 4), "ece": ece,
            "sharpness_sd": round(pstdev(ps), 4) if len(ps) > 1 else 0.0,
            "mean_prob": round(sum(ps) / len(ps), 4), **d, "reliability_bins": diag}


# ---------- calibrators (leave-one-event-out) ----------
def _loeo_predict(cases, method):
    """คืน prob ต่อ warned-case โดยใช้ 'เหตุการณ์อื่น' ฝึก (prequential)."""
    ps = []
    for c in cases:
        others = [x for x in cases if x["event"] != c["event"]]
        og = [x["gold"] for x in others]
        base = sum(og) / len(og) if og else P_CONST
        if method == "const":
            ps.append(P_CONST)
        elif method == "climatology":
            ps.append(base)
        elif method == "by_hop":
            strat = [x["gold"] for x in others if x["hop"] == c["hop"]]
            ps.append(sum(strat) / len(strat) if len(strat) >= 3 else base)
        elif method in ("platt", "isotonic"):
            ps.append(_fit_predict(others, c, method, base))
    return ps


def _fit_predict(others, c, method, base):
    try:
        X = [[float(x["hop"] or 0)] for x in others]
        y = [int(x["gold"]) for x in others]
        if len(set(y)) < 2:
            return base
        if method == "platt":
            from sklearn.linear_model import LogisticRegression
            m = LogisticRegression(C=1.0, solver="lbfgs").fit(X, y)
            return float(m.predict_proba([[float(c["hop"] or 0)]])[0][1])
        from sklearn.isotonic import IsotonicRegression
        xs = [r[0] for r in X]
        m = IsotonicRegression(out_of_bounds="clip").fit(xs, y)
        return float(m.predict([float(c["hop"] or 0)])[0])
    except Exception:  # noqa: BLE001
        return base


def _bootstrap_ci(cases, method, B=2000):
    """CI ของ Brier + BSS (resample warned cases)."""
    ps = _loeo_predict(cases, method)
    gs = [c["gold"] for c in cases]
    obar = sum(gs) / len(gs); unc = obar * (1 - obar)
    briers, bsss = [], []
    n = len(cases)
    for _ in range(B):
        idx = [random.randrange(n) for _ in range(n)]
        bp = [ps[i] for i in idx]; bg = [gs[i] for i in idx]
        b = _brier(bp, bg); briers.append(b)
        ob = sum(bg) / len(bg); u = ob * (1 - ob)
        bsss.append((u - b) / u if u else 0.0)
    briers.sort(); bsss.sort()
    q = lambda a, lo: a[int(lo * len(a))]
    return {"brier_ci95": [round(q(briers, .025), 4), round(q(briers, .975), 4)],
            "bss_ci95": [round(q(bsss, .025), 3), round(q(bsss, .975), 3)]}


def _event_bootstrap(cases, method, B=3000):
    """CI แบบ cluster/event-level: resample 'ทั้งเหตุการณ์' (ถูกต้องกว่าเมื่อ province-cases
    ภายในเหตุการณ์เดียวกัน correlated) — Davison & Hinkley 1997 cluster bootstrap. มักได้ CI *กว้างกว่า*
    case-level = ซื่อสัตย์กว่าสำหรับ N เหตุการณ์น้อย."""
    by_ev: dict[str, list] = {}
    for c in cases:
        by_ev.setdefault(c["event"], []).append(c)
    evs = list(by_ev)
    briers, bsss = [], []
    for _ in range(B):
        pick = [by_ev[evs[random.randrange(len(evs))]] for _ in range(len(evs))]
        pool = [c for grp in pick for c in grp]
        ps = _loeo_predict(pool, method)
        gs = [c["gold"] for c in pool]
        b = _brier(ps, gs); briers.append(b)
        ob = sum(gs) / len(gs); u = ob * (1 - ob)
        bsss.append((u - b) / u if u else 0.0)
    briers.sort(); bsss.sort()
    q = lambda a, lo: a[min(len(a) - 1, int(lo * len(a)))]
    return {"brier_ci95": [round(q(briers, .025), 4), round(q(briers, .975), 4)],
            "bss_ci95": [round(q(bsss, .025), 3), round(q(bsss, .975), 3)],
            "n_events": len(evs), "method": "event-level cluster bootstrap"}


def _per_event_loeo(cases, method="by_hop"):
    """สกิลของแต่ละเหตุการณ์เมื่อ calibrate ด้วย 'อีก 3 เหตุการณ์' (แสดงความคงเส้นคงวา)."""
    rows = []
    for y in _YEAR_ORDER:
        ev = [c for c in cases if c["event"] == y and c["predicted"]]
        if not ev:
            continue
        ps = _loeo_predict([c for c in cases if c["predicted"]], method)
        # map เฉพาะ case ของ event นี้
        idx = [i for i, c in enumerate([c for c in cases if c["predicted"]]) if c["event"] == y]
        pe = [ps[i] for i in idx]; ge = [ev[k]["gold"] for k in range(len(ev))]
        ob = sum(ge) / len(ge); u = ob * (1 - ob)
        rows.append({"event": y, "n_warned": len(ev), "brier": round(_brier(pe, ge), 4),
                     "obs_rate": round(ob, 3),
                     "bss": round((u - _brier(pe, ge)) / u, 3) if u else None})
    return rows


def _drift(cases):
    """CSI ต่อเหตุการณ์ตามลำดับเวลา (จากทุก scored case ไม่ใช่แค่ warned)."""
    out = []
    for y in _YEAR_ORDER:
        ev = [c for c in cases if c["event"] == y]
        tp = sum(c["outcome"] == "TP" for c in ev)
        fp = sum(c["outcome"] == "FP" for c in ev)
        fn = sum(c["outcome"] == "FN" for c in ev)
        csi = tp / (tp + fp + fn) if (tp + fp + fn) else None
        out.append({"event": y, "csi": round(csi, 3) if csi is not None else None,
                    "alarm": (csi is not None and csi < 0.6)})
    return out


def run() -> dict:
    bank = json.loads(_BANK.read_text("utf-8"))
    scored = [c for c in bank["cases"] if c["scored"]]
    warned = [c for c in scored if c["predicted"]]
    gs = [c["gold"] for c in warned]

    methods = ["const", "climatology", "by_hop", "platt", "isotonic"]
    models = {}
    for m in methods:
        ps = _loeo_predict(warned, m)
        models[m] = _all_metrics(ps, gs)
    # best = สูงสุดตาม BSS (ยกเว้น climatology ที่เป็น reference)
    cand = {k: v for k, v in models.items() if k != "climatology"}
    best = max(cand, key=lambda k: cand[k]["bss_vs_climatology"])

    return {
        "note": "verify คำเตือนความน่าจะเป็น (Brier decomp + BSS + ECE) · calibrate LOEO (กัน overfit) · ไม่แตะกราฟ/gate",
        "n_warned": len(warned), "base_rate": round(sum(gs) / len(gs), 3),
        "models": models, "best_by_bss": best,
        "best_ci_case_level": _bootstrap_ci(warned, best),
        "best_ci_event_level": _event_bootstrap(warned, best),
        "per_event_loeo": _per_event_loeo(scored, best),
        "drift_csi_by_event": _drift(scored),
        "ci_note": ("รายงาน CI สองแบบ: case-level (แคบเกินจริงเพราะ province-cases correlated) และ "
                    "event-level cluster bootstrap (ถูกต้องกว่า, กว้างกว่า) — ใช้ event-level เป็นหลัก"),
        "caveat": ("ข้อมูลน้อย (%d คำเตือน / %d เหตุการณ์) → CI ยังกว้าง; ทางแก้ที่ซื่อสัตย์คือ 'เพิ่มเหตุการณ์' "
                   "(ผ่าน prospective log) ไม่ใช่จูน. isotonic เสี่ยง overfit → empirical/Platt ปลอดภัยกว่า "
                   "(Niculescu-Mizil 2005)" % (len(warned), len({c["event"] for c in scored}))),
    }


def main() -> None:
    r = run()
    _OUT.write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8")
    print(f"warning_verification.json: n_warned={r['n_warned']} base_rate={r['base_rate']}")
    print(f"{'model':13s} {'Brier':>7s} {'BSS':>6s} {'ECE':>6s} {'sharp':>6s} {'rel':>6s} {'res':>6s}")
    for k, m in r["models"].items():
        print(f"{k:13s} {m['brier']:>7.4f} {m['bss_vs_climatology']:>6.3f} {m['ece']:>6.3f} "
              f"{m['sharpness_sd']:>6.3f} {m['reliability']:>6.4f} {m['resolution']:>6.4f}")
    print(f"best_by_bss={r['best_by_bss']}")
    print(f"  BSS CI95 case-level  = {r['best_ci_case_level']['bss_ci95']}")
    print(f"  BSS CI95 event-level = {r['best_ci_event_level']['bss_ci95']}  (ใช้เป็นหลัก)")
    print("  per-event LOEO:", [(x["event"], x["bss"]) for x in r["per_event_loeo"]])
    print("  drift CSI:", [(d["event"], d["csi"]) for d in r["drift_csi_by_event"]])


if __name__ == "__main__":
    main()
