"""Ingest orchestrator — เรียก connector D1–D4 แล้วรวมเป็น nodes/edges (+evidence).

เฟส 1 จะ implement:
  D1 data.go.th (CKAN) → RainStation / RiverReach water levels
  D2 thaiwater        → Reservoir levels, spillway
  D3 GISTDA STAC      → flood extent (ground truth, ไม่ใช่ edge)
  D4 basin/province   → geometry สำหรับ geo phase
กติกา: ทุก edge แนบ Evidence(station_id, timestamp, dataset) — ห้าม edge ลอย.
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError("Phase 1: implement D1–D4 connectors → nodes/edges + evidence")


if __name__ == "__main__":
    main()
