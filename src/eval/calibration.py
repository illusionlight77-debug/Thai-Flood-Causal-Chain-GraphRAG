"""Roadmap B — Calibration: ปรับ "ความน่าจะเป็นของคำเตือน" จากผลจริง โดยกัน overfitting.

หลักการ (ดู docs/FORECASTING_ROADMAP.md):
  • *ไม่* แตะกราฟ/gate — ปรับเฉพาะ "ความน่าจะเป็น" ของคำเตือนที่ระบบออกไปแล้ว
  • ใช้ leave-one-event-out (LOEO) = prequential: ประเมินเหตุการณ์หนึ่งด้วย hit-rate ของ
    "เหตุการณ์อื่นเท่านั้น" → ไม่มี leakage, กัน overfit (ไม่ fit บนชุดเดียวกับที่วัด)
  • baseline = ความน่าจะเป็นคงที่ (precision รวม 0.938 จาก risk_warning.py)
  • วัด Brier (ยิ่งต่ำยิ่งดี) + reliability + sharpness (ตาม Gneiting et al. 2007)

รายงานตรง: ถ้า calibration ไม่ช่วย (Brier ไม่ลด) ก็รายงานตามจริง — ไม่ดันตัวเลขให้สวย.

Input : data/processed/case_bank.json  (จาก src.eval.case_bank)
Output: data/processed/calibration.json

Usage:  python -m src.eval.calibration
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import pstdev

from src.config import settings

_PROC = settings.data_processed_dir
_BANK = _PROC / "case_bank.json"
_OUT = _PROC / "calibration.json"

P_BASE = 0.938   # baseline: pooled causal precision (risk_warning.py) — คงที่ทุกคำเตือน
_MIN = 3         # ต่ำกว่านี้ต่อ stratum → fallback ไป LOEO-overall (กัน estimate จาก n น้อย)


def _hitrate(cases: list[dict]) -> float | None:
    """P(flood | warned) = TP / (TP+FP) ของเคสที่ 'เตือน' (predicted=True)."""
    warned = [c for c in cases if c["predicted"]]
    if not warned:
        return None
    return sum(c["gold"] for c in warned) / len(warned)


def _brier(probs: list[float], golds: list[int]) -> float:
    return sum((p - g) ** 2 for p, g in zip(probs, golds)) / len(probs)


def run() -> dict:
    bank = json.loads(_BANK.read_text("utf-8"))
    scored = [c for c in bank["cases"] if c["scored"]]
    events = sorted({c["event"] for c in scored})
    warned = [c for c in scored if c["predicted"]]
    golds = [int(c["gold"]) for c in warned]

    # --- baseline: ความน่าจะเป็นคงที่ ---
    p_base = [P_BASE] * len(warned)

    # --- LOEO-overall: hit-rate ของ "เหตุการณ์อื่น" ---
    p_loeo, p_hop = [], []
    for c in warned:
        others = [x for x in scored if x["event"] != c["event"]]
        p_loeo.append(_hitrate(others) or P_BASE)
        # LOEO stratified by hop (ถ้าตัวอย่างพอ) — เพิ่ม resolution
        strat = [x for x in others if x["predicted"] and x["hop"] == c["hop"]]
        p_hop.append((sum(s["gold"] for s in strat) / len(strat)) if len(strat) >= _MIN
                     else (_hitrate(others) or P_BASE))

    models = {
        "baseline_const": {"probs": p_base, "desc": "ความน่าจะเป็นคงที่ 0.938"},
        "loeo_overall": {"probs": p_loeo, "desc": "LOEO hit-rate (prequential)"},
        "loeo_by_hop": {"probs": p_hop, "desc": "LOEO hit-rate แยกตาม hop"},
    }
    for m in models.values():
        pr = m.pop("probs")
        m["brier"] = round(_brier(pr, golds), 4)
        m["sharpness_sd"] = round(pstdev(pr), 4) if len(pr) > 1 else 0.0
        m["mean_prob"] = round(sum(pr) / len(pr), 4)

    # --- reliability ของ LOEO-by-hop (bin ตามค่าที่ทำนาย) ---
    bins = [(0.0, 0.7), (0.7, 0.85), (0.85, 0.95), (0.95, 1.01)]
    reliability = []
    for lo, hi in bins:
        idx = [i for i, p in enumerate(p_hop) if lo <= p < hi]
        if not idx:
            continue
        reliability.append({"bin": f"{lo:.2f}-{hi:.2f}", "n": len(idx),
                            "mean_pred": round(sum(p_hop[i] for i in idx) / len(idx), 3),
                            "obs_freq": round(sum(golds[i] for i in idx) / len(idx), 3)})

    base_b = models["baseline_const"]["brier"]
    best = min(models, key=lambda k: models[k]["brier"])
    return {
        "note": "calibrate ความน่าจะเป็นของคำเตือนแบบ leave-one-event-out (กัน overfit) — ไม่แตะกราฟ/gate",
        "n_warned": len(warned), "events": events, "observed_base_rate": round(sum(golds) / len(golds), 3),
        "models": models, "best_by_brier": best,
        "brier_improvement_vs_const": round(base_b - models[best]["brier"], 4),
        "reliability_loeo_by_hop": reliability,
        "interpret": ("calibrated ดีขึ้น (Brier ลด + sharp ขึ้น)" if models[best]["brier"] < base_b
                      else "calibration ไม่ช่วยลด Brier บนข้อมูลนี้ (รายงานตรง) — const ก็ใกล้ base-rate อยู่แล้ว"),
    }


def main() -> None:
    r = run()
    _OUT.write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8")
    print(f"calibration.json: n_warned={r['n_warned']} base_rate={r['observed_base_rate']}")
    for k, m in r["models"].items():
        print(f"  {k:16s} Brier={m['brier']}  sharp(sd)={m['sharpness_sd']}  mean={m['mean_prob']}")
    print(f"  best={r['best_by_brier']}  Δvs_const={r['brier_improvement_vs_const']}")
    print(f"  → {r['interpret']}")


if __name__ == "__main__":
    main()
