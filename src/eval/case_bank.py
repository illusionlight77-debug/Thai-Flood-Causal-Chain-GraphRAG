"""Roadmap B — Case Bank: เก็บ "เคสทำนายถูก/ผิด" ของ early-warning ไว้เรียนรู้ + โชว์ track record.

หลักการกัน overfitting (ดู docs/FORECASTING_ROADMAP.md):
  • ไฟล์นี้ *ไม่* แตะโครงกราฟ/gate/lag — แค่ "บันทึกผล" ของการทำนายที่ระบบทำไปแล้ว
  • เคสมาจากผลจริงเทียบ GISTDA gold (per-event) → ป้าย TP/FP/FN/TN
  • เคส "prospective" (เตือนก่อนรู้ผลจริง เช่น สระบุรี) เก็บแยกใน case_bank_prospective.json
    เพื่อไม่ให้ rebuild ทับ — และเพื่อคง property ว่า "บันทึกก่อนรู้ผล"

Input : web/ui_data_{event}.json (per-province: is_gold + causal predicted set + hop)
Output: data/processed/case_bank.json  (เคสทั้งหมด + สรุป POD/FAR/CSI ต่อเหตุการณ์ + สะสม)

Usage:
    python -m src.eval.case_bank                    # build/refresh จากผลจริง
    python -m src.eval.case_bank --list-wrong       # โชว์เคสที่ทำนายผิด
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.config import settings

_WEB = Path(__file__).resolve().parent.parent.parent / "web"
_PROC = settings.data_processed_dir
_OUT = _PROC / "case_bank.json"
_PROSPECTIVE = _PROC / "case_bank_prospective.json"

# เหตุการณ์ที่ "ให้คะแนน" (ลุ่มเจ้าพระยา, มี negative จริง) — ne2026 เป็น generalization แยก
SCORED = ["2022", "2021", "2024", "2023"]
_LABEL = {"2022": "เจ้าพระยา 2565 (โนรู)", "2021": "เจ้าพระยา 2564 (เตี้ยนหมู่)",
          "2024": "เจ้าพระยา 2567", "2023": "เจ้าพระยา 2566", "ne2026": "โขง/อีสาน (live)"}
SYS = "causal-graphrag"


def _label(pred: bool, gold: bool) -> str:
    return {(True, True): "TP", (True, False): "FP",
            (False, True): "FN", (False, False): "TN"}[(pred, gold)]


def _cases_for_event(year: str) -> list[dict]:
    f = _WEB / f"ui_data_{year}.json"
    if not f.exists():
        return []
    d = json.loads(f.read_text("utf-8"))
    predicted = set(d["per_province"][d["provinces"][0]]["systems"][SYS]["provinces"]) \
        if d["provinces"] else set()
    out = []
    for p in d["provinces"]:
        pp = d["per_province"][p]
        pred = p in predicted
        gold = bool(pp["is_gold"])
        out.append({"event": year, "label": _LABEL.get(year, year), "province": p,
                    "hop": pp.get("hop"), "predicted": pred, "gold": gold,
                    "outcome": _label(pred, gold), "scored": year in SCORED})
    return out


def _skill(cases: list[dict]) -> dict:
    tp = sum(c["outcome"] == "TP" for c in cases)
    fp = sum(c["outcome"] == "FP" for c in cases)
    fn = sum(c["outcome"] == "FN" for c in cases)
    tn = sum(c["outcome"] == "TN" for c in cases)
    pod = tp / (tp + fn) if (tp + fn) else None      # hit rate
    far = fp / (tp + fp) if (tp + fp) else None       # false-alarm ratio
    csi = tp / (tp + fp + fn) if (tp + fp + fn) else None  # critical success index
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "pod": round(pod, 3) if pod is not None else None,
            "far": round(far, 3) if far is not None else None,
            "csi": round(csi, 3) if csi is not None else None}


def build() -> dict:
    cases: list[dict] = []
    per_event = {}
    for y in SCORED + ["ne2026"]:
        ev = _cases_for_event(y)
        if not ev:
            continue
        cases += ev
        per_event[y] = {"label": _LABEL.get(y, y), "scored": y in SCORED, **_skill(ev)}

    # prospective cases (เตือนก่อนรู้ผล — เก็บแยก ไม่ถูก rebuild ทับ)
    prospective = []
    if _PROSPECTIVE.exists():
        prospective = json.loads(_PROSPECTIVE.read_text("utf-8")).get("cases", [])

    scored_cases = [c for c in cases if c["scored"]]
    notable_correct = sorted([c for c in scored_cases if c["outcome"] == "TP"],
                             key=lambda c: -(c["hop"] or 0))[:5]
    notable_wrong = [c for c in scored_cases if c["outcome"] in ("FP", "FN")]

    return {
        "note": "เคสทำนายถูก/ผิดของ early-warning เทียบ GISTDA gold — ไม่แตะกราฟ/gate (กัน overfit)",
        "systems": SYS,
        "per_event": per_event,
        "cumulative_scored": _skill(scored_cases),
        "n_cases_scored": len(scored_cases),
        "notable_correct": notable_correct,
        "notable_wrong": notable_wrong,
        "prospective": prospective,
        "cases": cases,
    }


def add_prospective(event: str, province: str, predicted: bool, timestamp: str,
                    lead_window_h: tuple[int, int] | None = None, note: str = "",
                    gold: bool | None = None) -> None:
    """บันทึกคำเตือน 'ก่อนรู้ผล' (เช่น สระบุรี). gold=None = ยังไม่ทราบผล; เติมภายหลังได้."""
    data = json.loads(_PROSPECTIVE.read_text("utf-8")) if _PROSPECTIVE.exists() else {"cases": []}
    data["cases"] = [c for c in data["cases"]
                     if not (c["event"] == event and c["province"] == province)]
    rec = {"event": event, "province": province, "predicted": predicted,
           "timestamp": timestamp, "lead_window_h": list(lead_window_h) if lead_window_h else None,
           "note": note, "gold": gold}
    if gold is not None:
        rec["outcome"] = _label(predicted, bool(gold))
    data["cases"].append(rec)
    _PROSPECTIVE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def main() -> None:
    bank = build()
    _OUT.write_text(json.dumps(bank, ensure_ascii=False, indent=2), "utf-8")
    c = bank["cumulative_scored"]
    print(f"case_bank.json: {bank['n_cases_scored']} scored cases "
          f"(TP {c['tp']} · FP {c['fp']} · FN {c['fn']} · TN {c['tn']})  "
          f"POD {c['pod']} · FAR {c['far']} · CSI {c['csi']}")
    if "--list-wrong" in sys.argv:
        for w in bank["notable_wrong"]:
            print(f"  {w['outcome']}  {w['event']}  {w['province']} (hop {w['hop']})")


if __name__ == "__main__":
    main()
