"""Precompute ข้อมูลสำหรับ UI (user-friendly + research) — รันทั้ง 3 ระบบ ทุกจังหวัด
(gold + negative control) ของ event ปัจจุบัน (EVENT_ID) → web/ui_data_{year}.json.

รวม: #1 คำอธิบาย LLM (grounded), #3 negative control + confusion, #6 lead-time (lag).
ต่อ event: ตั้ง EVENT_ID แล้ว ingest→geo→load ก่อน. ต้องมี Neo4j.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config import settings
from src.eval.f1_by_hop import f1
from src.graph import queries
from src.graph.client import Neo4jClient
from src.ingest import fixtures
from src.rag import llm
from src.rag.registry import build_retrievers

WEB = Path(__file__).resolve().parent.parent.parent / "web"


def _hop_map(c: Neo4jClient) -> dict:
    return {r["province"]: r["hops"] for r in c.run(queries.HOP_PER_PROVINCE)}


def _lead_time(c: Neo4jClient, prov: str) -> int | None:
    rows = c.run(queries.LEAD_TIME_TO_PROVINCE, province=prov)
    v = rows[0]["lead_hours"] if rows else None
    return int(v) if v is not None else None


def build() -> Path:
    c = Neo4jClient()
    names = {pid: fixtures.PROVINCES[pid][3] for pid in fixtures.PROVINCES}
    gold = [names[p] for p in fixtures.GOLD_FLOODED]
    goldset = set(gold)
    negatives = [names[p] for p in fixtures.PROVINCES if p not in fixtures.GOLD_FLOODED]
    allprov = gold + negatives
    hop_map = _hop_map(c)
    rs = build_retrievers()

    per_province: dict = {}
    for prov in allprov:
        is_gold = prov in goldset
        q = f"ทำไมจังหวัด{prov}ถึงน้ำท่วมในเหตุการณ์นี้?"
        systems: dict = {}
        for sysname, r in rs.items():
            a = r.answer(q, province=prov)
            pred = set(a.provinces)
            tp = sorted(pred & goldset); fp = sorted(pred - goldset); fn = sorted(goldset - pred)
            pr = len(tp) / len(pred) if pred else 0.0
            rc = len(tp) / len(goldset) if goldset else 0.0
            systems[sysname] = {
                "provinces": sorted(pred), "chain": a.chain, "hops": a.hops,
                "evidence": [{"station_id": e.station_id, "timestamp": e.timestamp,
                              "dataset": e.dataset} for e in a.evidence],
                "traceable": a.is_traceable, "latency_ms": round(a.latency_s * 1000, 1),
                "f1": round(f1(pred, goldset), 3), "precision": round(pr, 3), "recall": round(rc, 3),
                "tp": tp, "fp": fp, "fn": fn, "text": a.text,
                "predicts_this": prov in pred,
            }
        # #6 lead time + #1 คำอธิบาย (เฉพาะ causal)
        ca = systems["causal-graphrag"]
        lead = _lead_time(c, prov) if ca["predicts_this"] else None
        ca["lead_hours"] = lead
        ca["explanation"] = llm.explain_flood(prov, ca["chain"], ca["evidence"],
                                               ca["hops"], ca["predicts_this"], lead)
        per_province[prov] = {"hop": hop_map.get(prov, 0), "question": q,
                              "is_gold": is_gold, "systems": systems}

    # #3 confusion ต่อระบบ (gold=positive, negatives=negative)
    negset = set(negatives)
    confusion: dict = {}
    for sysname in rs:
        # pred ระดับ event = union ของสิ่งที่ระบบทำนายว่าท่วม (ใช้ pred จากคำถามใดก็ได้ของระบบนั้น)
        pred = set(per_province[gold[0]]["systems"][sysname]["provinces"]) if gold else set()
        # entity/vector pred ต่างตามจังหวัดที่ถาม → ใช้ predicts_this รวม
        predicted = {p for p in allprov if per_province[p]["systems"][sysname]["predicts_this"]}
        tp = len(predicted & goldset); fp = len(predicted & negset)
        fn = len(goldset - predicted); tn = len(negset - predicted)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        spec = tn / (tn + fp) if (tn + fp) else 0.0
        acc = (tp + tn) / len(allprov) if allprov else 0.0
        confusion[sysname] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                              "precision": round(prec, 3), "recall": round(rec, 3),
                              "specificity": round(spec, 3), "accuracy": round(acc, 3)}

    yr = fixtures._YEAR
    results_path = settings.data_processed_dir / f"eval_results_{yr}.json"
    if not results_path.exists():
        results_path = settings.data_processed_dir / "eval_results.json"
    results = json.loads(results_path.read_text("utf-8")) if results_path.exists() else {}
    abl_path = settings.data_processed_dir / f"ablation_{yr}.json"
    ablation = json.loads(abl_path.read_text("utf-8")) if abl_path.exists() else {}

    out = {"event_id": fixtures.EVENT_ID, "year": yr, "period": fixtures.EVENT_PERIOD,
           "llm_provider": settings.llm_provider if llm.available() else "none",
           "gold": gold, "negatives": negatives, "provinces": allprov,
           "per_province": per_province, "confusion": confusion,
           "results": results, "ablation": ablation}
    WEB.mkdir(exist_ok=True)
    f = WEB / f"ui_data_{yr}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    c.close()
    return f


def main() -> None:
    f = build()
    print(f"เขียน UI data → {f}  (LLM={settings.llm_provider}, gold+neg รวมทุกจังหวัด)")


if __name__ == "__main__":
    main()
