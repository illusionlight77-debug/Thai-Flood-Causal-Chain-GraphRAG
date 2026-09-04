"""#4 Probabilistic + risk layer for the early-warning output.

We do NOT build a new predictor. We WRAP each causal warning with numbers grounded in
published methods + our own measured skill:

- Probability P(flood | warned) = the causal system's *measured precision* (TP/(TP+FP) =
  0.938 pooled) — a reliability-calibrated probability, not invented. (Verification-metric
  framing: NOAA Forecast Verification Glossary; probabilistic-warning precedent: EFAS,
  HESS 13:141 2009; ensemble review Hydrol. Sci. J. 2021 doi:10.1080/02626667.2021.2023157.)
- Lead-time window = [model wave lead, model lead × basin-fill slowdown] — the fast-wave
  lower bound and the slow-fill upper bound measured in lead_validation (~5.7× on 2011).
- Confidence = from causal-hop depth + gauge confidence.
- RISK = Hazard × Exposure × Vulnerability (standard UNDRR/IPCC decomposition; flood risk-
  index precedent: 'Flood Risk Assessment Based on Flood Hazard and Vulnerability Indexes'
  2021; Nature Sci. Rep. s41598-025-13025-z):
    Hazard = probability
    Exposure = province population (NSO Thailand 2020 census, thousands)
    Vulnerability = historical flood frequency across our scored events (0.5 / 1.0)
"""
from __future__ import annotations

import json
from pathlib import Path

_WEB = Path(__file__).resolve().parent.parent.parent / "web"

P_BASE = 0.938        # pooled causal precision (measured) → P(flood | warned)
SLOWDOWN = 5.7        # measured on 2011 (lead_validation): observed / model wave time

# Exposure: province population, thousands (NSO Thailand 2020 census, approximate).
POP_K = {
    "Bangkok": 5588, "Nonthaburi": 1290, "Pathum Thani": 1190, "Ayutthaya": 817,
    "Saraburi": 640, "Lopburi": 750, "Nakhon Pathom": 920, "Suphan Buri": 848,
    "Nakhon Sawan": 1060, "Phitsanulok": 866, "Phichit": 540, "Sukhothai": 590,
    "Kamphaeng Phet": 725, "Tak": 670, "Uttaradit": 455, "Chai Nat": 331,
    "Sing Buri": 210, "Ang Thong": 283, "Uthai Thani": 330, "Phetchabun": 995,
    "Chiang Mai": 1780, "Lampang": 740, "Lamphun": 405,
}
# exposure = จำนวนประชากรที่เสี่ยง (ล้านคน) ตามนิยาม UNDRR (ไม่ normalize)


def _vulnerability() -> dict:
    """flood frequency ข้ามเหตุการณ์ที่ให้คะแนน → 0.5 (ท่วม 1 ปี) / 1.0 (ท่วมทั้ง 2 ปี)."""
    freq = {}
    n = 0
    for y in ("2022", "2021"):
        f = _WEB / f"ui_data_{y}.json"
        if not f.exists():
            continue
        n += 1
        d = json.loads(f.read_text("utf-8"))
        for p in d["provinces"]:
            if d["per_province"][p]["is_gold"]:
                freq[p] = freq.get(p, 0) + 1
    return {p: round(c / n, 2) for p, c in freq.items()} if n else {}


_VULN = _vulnerability()


def _risk_level(score: float) -> str:
    # score = prob × ประชากร(ล้าน) × vuln  →  ระดับตามจำนวนคนเสี่ยงที่ปรับด้วยโอกาส/ความเปราะบาง
    if score >= 0.8:
        return "สูงมาก"
    if score >= 0.4:
        return "สูง"
    if score >= 0.15:
        return "ปานกลาง"
    return "ต่ำ"


def annotate(warnings: list[dict]) -> list[dict]:
    """เติม probability / lead window / confidence / risk ให้แต่ละคำเตือน."""
    out = []
    for w in warnings:
        prov = w.get("province")
        lead = w.get("lead_hours")
        hops = len(w.get("chain", [])) - 1 if w.get("chain") else 0
        prob = P_BASE
        conf = "สูง" if hops and hops <= 4 else ("กลาง" if hops else "ต่ำ")
        lead_lo = lead
        lead_hi = int(round(lead * SLOWDOWN)) if lead is not None else None
        exposure_m = POP_K.get(prov, 0) / 1000.0     # ล้านคน
        vuln = _VULN.get(prov, 0.5)
        risk = round(prob * exposure_m * vuln, 3)
        w2 = dict(w)
        w2.update({"probability": round(prob, 3), "confidence": conf,
                   "lead_window_h": [lead_lo, lead_hi],
                   "exposure_pop_k": POP_K.get(prov), "vulnerability": vuln,
                   "risk_score": risk, "risk_level": _risk_level(risk)})
        out.append(w2)
    # เรียงตาม risk มาก→น้อย (สำหรับจัดลำดับความสำคัญเชิงภัยพิบัติ)
    out.sort(key=lambda x: (-x["risk_score"], x["lead_hours"] if x["lead_hours"] is not None else 1e9))
    return out
