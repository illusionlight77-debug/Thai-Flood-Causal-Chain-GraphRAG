"""When does causal-graphrag actually beat the over-predicting entity baseline?

This formalizes a finding that came out of trying to add the 2011 mega-flood as a third
event: the causal advantage depends on the event being DISCRIMINATING — i.e. having real
'did-not-flood' provinces (negatives). On a near-universal flood (2011: essentially every
in-basin province flooded, defenses overwhelmed) a 'predict-everything' baseline is nearly
correct, so causal and entity converge. On partial floods (2022/2021: 6–7 negatives out of
23) causal's selectivity wins.

Reads the per-event ui_data and reports, per event: #negatives, causal vs entity F1 and
specificity. 2011 is included as a documented extreme (0 in-basin negatives, from the ERIA
GISTDA table — see gistda_flood_2011_eria.json) but is not a scored event.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config import settings

WEB = Path(__file__).resolve().parent.parent.parent / "web"
EVENTS = [("2022","เจ้าพระยา 2565"),("2021","เจ้าพระยา 2564"),("2024","เจ้าพระยา 2567"),("2023","เจ้าพระยา 2566"),("ne2026","โขง/อีสาน")]


def run() -> dict:
    rows = []
    for y, label in EVENTS:
        f = WEB / f"ui_data_{y}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text("utf-8"))
        n = len(d["provinces"])
        n_gold = sum(1 for p in d["provinces"] if d["per_province"][p]["is_gold"])
        n_neg = n - n_gold
        cf = d["results"]["causal-graphrag"]["f1_overall"]
        ef = d["results"]["entity-graphrag"]["f1_overall"]
        cs = d["confusion"]["causal-graphrag"]["specificity"]
        es = d["confusion"]["entity-graphrag"]["specificity"]
        rows.append({"event": label, "n_total": n, "n_neg": n_neg,
                     "neg_frac": round(n_neg / n, 2), "causal_f1": cf, "entity_f1": ef,
                     "causal_minus_entity": round(cf - ef, 3),
                     "causal_spec": cs, "entity_spec": es})
    # 2011 documented extreme (not scored)
    rows.append({"event": "มหาอุทกภัย 2554 (ไม่ให้คะแนน)", "n_total": 23, "n_neg": 0,
                 "neg_frac": 0.0, "causal_f1": None, "entity_f1": None,
                 "causal_minus_entity": None, "causal_spec": None, "entity_spec": None,
                 "note": "GISTDA (ERIA) แสดงทุกจังหวัดในลุ่มท่วม > cutoff → 0 negative → predict-all เกือบถูก → causal≈entity (ไม่ discriminate)"})
    finding = ("(1) causal SPECIFICITY ชนะ (0.67–0.86 vs entity 0) ทุกเหตุการณ์ที่มี negative จริง "
               "— entity เดาท่วมหมด specificity=0 เสมอ. (2) causal F1 ชนะเพิ่ม *เมื่อกราฟโมเดล "
               "เส้นทางน้ำได้ดี* (เจ้าพระยา 2565/2564: +0.31/+0.35) แต่แพ้เมื่อ recall ต่ำ (โขง/อีสาน "
               "โมเดลจับแค่ริมโขง พลาด inland → −0.16). (3) เหตุการณ์ที่ท่วมเกือบทั้งลุ่ม (2554, 0 "
               "negative) ไม่มีอะไรให้ปฏิเสธ → causal≈entity. สรุป: จุดขาย causal (specificity + "
               "traceability) มีค่าเฉพาะบนเหตุการณ์ discriminating — ซึ่งคือเหตุการณ์น้ำท่วมส่วนใหญ่จริง "
               "(บางส่วน ไม่ใช่ทั้งประเทศ).")
    return {"rows": rows, "finding": finding}


def main() -> None:
    res = run()
    print(f"{'event':28s} {'neg':>4} {'neg%':>5} {'causalF1':>9} {'entF1':>7} {'Δ':>7} {'cSpec':>6} {'eSpec':>6}")
    for r in res["rows"]:
        f = lambda v: f"{v:.3f}" if isinstance(v, (int, float)) else "  –  "
        print(f"{r['event']:28s} {r['n_neg']:>4} {r['neg_frac']:>5} "
              f"{f(r['causal_f1']):>9} {f(r['entity_f1']):>7} {f(r['causal_minus_entity']):>7} "
              f"{f(r['causal_spec']):>6} {f(r['entity_spec']):>6}")
    print("\nFINDING:", res["finding"])
    (settings.data_processed_dir / "discrimination.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
