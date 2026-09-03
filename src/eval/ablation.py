"""#2 Ablation study — ปิด/เปิดทีละกลไกของ causal-graphrag แล้ววัด F1 ที่เปลี่ยน
เพื่อพิสูจน์ว่า *อะไร* คือสิ่งที่ทำให้ causal ทำงาน (ทิศการไหล / gate ระดับน้ำล้น /
คันกั้นน้ำ / runoff path). รันบน event ปัจจุบัน (EVENT_ID) — ต้องโหลดกราฟแล้ว.

เทียบกับ full model:
  full     = directed + overflow-gate + protect-gate + runoff-path
  −runoff  = เอา RUNOFF_TO ออก (ฝนเข้าลำน้ำตรงไม่ได้)
  −overflow= ไม่กรองด้วย reach.overflow (ลำน้ำหลักล้นจริง)
  −protect = ไม่สนคันกั้นน้ำ (กทม./นนทบุรี)
  −direction = เดินกราฟไม่สนทิศ (undirected) = เหมือน entity
"""
from __future__ import annotations

import json

from src.eval.f1_by_hop import f1
from src.graph.client import Neo4jClient
from src.ingest import fixtures

RELS_ALL = "FEEDS|OVERFLOWS_TO|FLOWS_TO|INUNDATES|RUNOFF_TO"
RELS_NO_RUNOFF = "FEEDS|OVERFLOWS_TO|FLOWS_TO|INUNDATES"


def _q(rels: str, directed: bool, gate_overflow: bool, gate_protect: bool) -> str:
    arrow = f"-[rels:{rels}*2..6]->" if directed else f"-[rels:{rels}*2..6]-"
    conds = ["last_reach:RiverReach"]
    if gate_overflow:
        conds.append("last_reach.overflow = true")
    if gate_protect:
        conds.append("coalesce(p.protected, false) = false")
    where = " AND ".join(conds)
    return f"""
MATCH path = (src){arrow}(p:Province)
WHERE src.active = true
WITH p, nodes(path) AS ns
WITH p, ns[size(ns)-2] AS last_reach
WHERE {where}
RETURN DISTINCT p.name_en AS province
"""


def _pred(c: Neo4jClient, **kw) -> set[str]:
    return {r["province"] for r in c.run(_q(**kw))}


def run(c: Neo4jClient | None = None) -> dict:
    c = c or Neo4jClient()
    gold = {fixtures.PROVINCES[p][3] for p in fixtures.GOLD_FLOODED}
    variants = {
        "full (ครบทุกกลไก)":     dict(rels=RELS_ALL, directed=True, gate_overflow=True, gate_protect=True),
        "−runoff":               dict(rels=RELS_NO_RUNOFF, directed=True, gate_overflow=True, gate_protect=True),
        "−overflow gate":        dict(rels=RELS_ALL, directed=True, gate_overflow=False, gate_protect=True),
        "−protection":           dict(rels=RELS_ALL, directed=True, gate_overflow=True, gate_protect=False),
        "−direction (undirected)": dict(rels=RELS_ALL, directed=False, gate_overflow=True, gate_protect=True),
    }
    out = {}
    for name, kw in variants.items():
        pred = _pred(c, **kw)
        out[name] = {"f1": round(f1(pred, gold), 3), "n_pred": len(pred),
                     "pred": sorted(pred)}
    return {"event": fixtures.EVENT_ID, "gold": sorted(gold), "variants": out}


def main() -> None:
    res = run()
    print(f"=== Ablation ({res['event']}) · gold={len(res['gold'])} ===")
    base = res["variants"]["full (ครบทุกกลไก)"]["f1"]
    for name, v in res["variants"].items():
        d = v["f1"] - base
        tag = "" if name.startswith("full") else f"  (ΔF1 {d:+.3f})"
        print(f"  {name:26s} F1={v['f1']:.3f}  ทำนาย {v['n_pred']} จว.{tag}")
    from src.config import settings
    (settings.data_processed_dir / f"ablation_{fixtures._YEAR}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
