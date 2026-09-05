"""เพิ่มเหตุการณ์จริง #5 — เจ้าพระยา 2568 (2025) จาก GISTDA satellite (real, cited).

ทำไม *ไม่ใช่การปั้น*:
  • gold (จังหวัดท่วม) = รายชื่อทางการจาก GISTDA (ผ่าน Nation Thailand, 12 พ.ย. 2568, ภาพ 11 พ.ย.)
    — เหตุการณ์จริง 2,441,484 ไร่ · 17 จังหวัดภาคกลาง. บทความไม่ให้ไร่รายจังหวัด → gold = "รายชื่อจังหวัด
    ที่ GISTDA รายงานว่าท่วม" (บันทึกความต่างจาก cutoff ≥10k ไร่ ของปีก่อน — เป็น gold ที่หยาบกว่าเล็กน้อย)
  • prediction ของ causal = ใช้ **gate ตายตัวจาก 2022** (out-of-sample) — *โปรโตคอลเดียวกับ 2023/2024*
    (ดู river_reach_overbank_2023/2024 = held FIXED from 2022). ไม่ refit กับผล 2025 → blind ยังจริง.
    (verified: predicted set 2022==2023==2024 เหมือนกันเป๊ะ 16 จังหวัด)

Source: https://www.nationthailand.com/news/general/40058106 (GISTDA, 2025-11-12)

Usage: python -m src.ingest.add_gistda_2025
"""
from __future__ import annotations

import json

from src.config import settings

PROC = settings.data_processed_dir
WEB = settings.data_processed_dir.parent.parent / "web"
SRC = "https://www.nationthailand.com/news/general/40058106"

# 17 จังหวัดที่ GISTDA รายงานว่าท่วม (2025-11-11) — map เป็นชื่อใน universe 23 จังหวัด
GOLD_2025 = {
    "Ayutthaya", "Nakhon Sawan", "Suphan Buri", "Phichit", "Sukhothai", "Phitsanulok",
    "Lopburi", "Nakhon Pathom", "Chai Nat", "Ang Thong", "Sing Buri", "Uthai Thani",
    "Kamphaeng Phet", "Uttaradit", "Nonthaburi", "Phetchabun", "Pathum Thani",
}


def main() -> None:
    base = json.loads((WEB / "ui_data_2022.json").read_text("utf-8"))
    universe = base["provinces"]
    # ตรวจว่า gold ทุกชื่ออยู่ใน universe (กันพิมพ์ผิด)
    unknown = GOLD_2025 - set(universe)
    if unknown:
        raise SystemExit(f"gold names not in universe: {unknown}")

    predicted = set(base["per_province"][universe[0]]["systems"]["causal-graphrag"]["provinces"])
    # confusion (causal) สำหรับ 2025
    tp = len(predicted & GOLD_2025 & set(universe))
    fp = len([p for p in predicted if p in universe and p not in GOLD_2025])
    fn = len([p for p in universe if p in GOLD_2025 and p not in predicted])
    tn = len([p for p in universe if p not in GOLD_2025 and p not in predicted])

    # ---- ui_data_2025.json (โครงที่ case_bank ใช้; prediction ตายตัวจาก 2022, gold = 2025) ----
    ev = {
        "event_id": "chao_phraya_2025", "year": "2025",
        "period": "2025 (ภาพดาวเทียม 11 พ.ย. 2568)",
        "_meta": {"gold_source": SRC, "gold_rule": "GISTDA official flooded-province list "
                  "(per-province rai not published) — coarser than the >=10k-rai cutoff of prior years",
                  "gate": "FIXED from 2022 RID SWOC pattern (out-of-sample, same protocol as 2023/2024)"},
        "provinces": universe, "per_province": {},
        # บล็อกสถิติของ 2022 ไม่ยกมา (จะทำให้เข้าใจผิด) — ตั้ง null
        "gold": sorted(GOLD_2025), "negatives": sorted(set(universe) - GOLD_2025),
        "confusion": {"causal-graphrag": {"tp": tp, "fp": fp, "fn": fn, "tn": tn}},
        "significance": None, "faithfulness": None, "ablation": None, "results": None,
    }
    for p in universe:
        pp = base["per_province"][p]
        ev["per_province"][p] = {"hop": pp.get("hop"),
                                 "is_gold": p in GOLD_2025,
                                 "systems": pp["systems"]}  # prediction ตายตัว (fixed gate)
    (WEB / "ui_data_2025.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2), "utf-8")

    # ---- ไฟล์ provenance (real data, cited) ----
    (PROC / "gistda_flood_2025_all_provinces.json").write_text(json.dumps({
        "_meta": {"description": "GISTDA satellite flood — Chao Phraya 2025 event (2,441,484 rai, "
                  "17 provinces). Per-province rai not published in source.",
                  "source": SRC, "satellite_date": "2025-11-11", "total_rai": 2441484},
        "flooded_provinces": sorted(GOLD_2025),
    }, ensure_ascii=False, indent=2), "utf-8")
    (PROC / "ground_truth_2025.json").write_text(json.dumps({
        "_meta": {"source": SRC, "rule": "GISTDA official flooded-province list (in-basin)",
                  "note": "per-province rai unavailable → list-based gold"},
        "gold_provinces": sorted(GOLD_2025),
    }, ensure_ascii=False, indent=2), "utf-8")
    ob22 = json.loads((PROC / "river_reach_overbank_2022.json").read_text("utf-8"))
    ob22["_meta"] = {"description": "Sub-basin over-bank gate for 2025 — held FIXED from the 2022 RID "
                     "SWOC pattern, NOT refit to 2025 (same out-of-sample protocol as 2023/2024)."}
    (PROC / "river_reach_overbank_2025.json").write_text(json.dumps(ob22, ensure_ascii=False, indent=2), "utf-8")

    print(f"2025 added: gold={len(GOLD_2025)} negatives={len(set(universe)-GOLD_2025)} "
          f"predicted={len(predicted)} → TP {tp} · FP {fp} · FN {fn} · TN {tn}  "
          f"(POD {tp/(tp+fn):.3f} · FAR {fp/(tp+fp):.3f} · CSI {tp/(tp+fp+fn):.3f})")


if __name__ == "__main__":
    main()
