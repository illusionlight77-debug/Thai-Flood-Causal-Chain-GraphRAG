"""Ingest orchestrator (เฟส 1).

1) probe endpoint จริง D1–D4 → รายงาน provenance
2) เขียน fixture ลุ่มเจ้าพระยา 2022 (nodes + causal edges + geo + gold + news)
กติกาเหล็ก: causal edge ทุกเส้นมี evidence (station_id + timestamp + dataset).
INUNDATES สร้างต่อในเฟส 2 (geo point-in-polygon).
"""
from __future__ import annotations

import json

from src.config import settings
from src.ingest import connectors, fixtures


def main() -> None:
    print("── Phase 1: Ingest ──")
    print("\n[1] ยืนยัน endpoint จริง (provenance):")
    report = connectors.probe_sources()
    for k, v in report.items():
        mark = "✔" if v["ok"] else "✗"
        print(f"  {mark} {k}: {v['detail']}")

    print("\n[2] เขียน fixture → data/processed/")
    out = fixtures.write_all()
    nodes = json.loads((out / "graph_nodes.json").read_text("utf-8"))
    edges = json.loads((out / "graph_edges.json").read_text("utf-8"))

    # ตรวจกติกาเหล็ก: causal edge ต้องมี evidence ครบ
    missing = [e for e in edges if not e.get("evidence") or
               not all(e["evidence"].get(k) for k in ("station_id", "timestamp", "dataset"))]
    assert not missing, f"edge ไม่มี evidence ครบ: {missing}"

    print(f"  nodes={len(nodes)}  causal_edges={len(edges)}  (evidence ครบทุกเส้น ✔)")
    (settings.data_processed_dir / "provenance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(f"\nเสร็จ → {out}")


if __name__ == "__main__":
    main()
