"""Precompute ข้อมูลสำหรับหน้า UI ใหม่ (FastAPI) — รันทั้ง 3 ระบบ ทุกจังหวัด gold ของ event
ปัจจุบัน (EVENT_ID) → web/ui_data_{year}.json. รันต่อ event: ตั้ง EVENT_ID แล้ว ingest→geo→load ก่อน.

โครง JSON: {event_id, year, period, gold[], per_province:{prov:{hop, systems:{sys:{...รายละเอียด...}}}}, results}
รายละเอียดต่อระบบ: provinces, chain, hops, evidence[], traceable, latency_ms, f1, precision, recall, tp/fp/fn, text
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config import settings
from src.eval import build_eval_set
from src.eval.f1_by_hop import f1
from src.ingest import fixtures
from src.rag.registry import build_retrievers

WEB = Path(__file__).resolve().parent.parent.parent / "web"


def build() -> Path:
    names = {pid: fixtures.PROVINCES[pid][3] for pid in fixtures.PROVINCES}
    gold = [names[p] for p in fixtures.GOLD_FLOODED]
    goldset = set(gold)
    items = build_eval_set.build()
    rs = build_retrievers()

    per_province: dict = {}
    for it in items:
        systems: dict = {}
        for sysname, r in rs.items():
            a = r.answer(it.question, province=it.province)
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
            }
        per_province[it.province] = {"hop": it.hop, "question": it.question, "systems": systems}

    results_path = settings.data_processed_dir / f"eval_results_{fixtures._YEAR}.json"
    if not results_path.exists():
        results_path = settings.data_processed_dir / "eval_results.json"
    results = json.loads(results_path.read_text("utf-8")) if results_path.exists() else {}

    out = {"event_id": fixtures.EVENT_ID, "year": fixtures._YEAR, "period": fixtures.EVENT_PERIOD,
           "gold": gold, "provinces": gold, "per_province": per_province, "results": results}
    WEB.mkdir(exist_ok=True)
    f = WEB / f"ui_data_{fixtures._YEAR}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    return f


def main() -> None:
    f = build()
    print(f"เขียน UI data → {f}  (event={fixtures.EVENT_ID}, gold={len(fixtures.GOLD_FLOODED)} จังหวัด)")


if __name__ == "__main__":
    main()
