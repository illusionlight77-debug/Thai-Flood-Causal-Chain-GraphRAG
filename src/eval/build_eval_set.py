"""เฟส 5 — สร้างชุดคำถาม "ทำไมจังหวัด X ท่วม" + label ด้วย GISTDA gold + tag hop.

- ถามเฉพาะจังหวัดที่อยู่ใน gold (ท่วมจริงตาม GISTDA extent) → คำตอบที่ถูกคือ footprint ทั้งชุด.
- hop ของแต่ละคำถาม = ระยะ causal ต่ำสุดจากเขื่อน active ไปจังหวัดนั้น (จาก Neo4j HOP_PER_PROVINCE):
  2-hop = เขื่อนเดียว (ที่ราบลุ่มล่าง), 4-hop = ข้ามลุ่มน้ำผ่านจุดบรรจบ.
- คำถามเป็นภาษาไทย (ใช้ชื่อทางการ) เพื่อให้ vector-rag ค้นบนคลังข่าวไทยได้ยุติธรรม.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from src.config import settings
from src.graph import queries
from src.graph.client import Neo4jClient
from src.ingest import fixtures


@dataclass
class EvalItem:
    question: str
    province: str            # name_en ของจังหวัดที่ถาม
    event: str
    hop: int                 # 2 หรือ 4
    gold_provinces: list[str] = field(default_factory=list)  # name_en (GISTDA gold)


def _hop_map(client: Neo4jClient) -> dict[str, int]:
    return {r["province"]: r["hops"] for r in client.run(queries.HOP_PER_PROVINCE)}


def build(client: Neo4jClient | None = None) -> list[EvalItem]:
    client = client or Neo4jClient()
    names = {pid: fixtures.PROVINCES[pid][3] for pid in fixtures.PROVINCES}      # id→en
    names_th = {pid: fixtures.PROVINCES[pid][2] for pid in fixtures.PROVINCES}   # id→th
    gold_en = sorted(names[p] for p in fixtures.GOLD_FLOODED)
    hop_map = _hop_map(client)

    items: list[EvalItem] = []
    for pid in fixtures.GOLD_FLOODED:
        en, th = names[pid], names_th[pid]
        items.append(EvalItem(
            question=f"ทำไมจังหวัด{th}ถึงน้ำท่วมในเหตุการณ์ลุ่มเจ้าพระยาปี 2565?",
            province=en, event=fixtures.EVENT_ID,
            hop=hop_map.get(en, 2), gold_provinces=gold_en,
        ))
    return items


def main() -> None:
    items = build()
    out = settings.data_processed_dir / "eval_set.json"
    out.write_text(json.dumps([asdict(i) for i in items], ensure_ascii=False, indent=2), "utf-8")
    by_hop = {}
    for i in items:
        by_hop.setdefault(i.hop, []).append(i.province)
    print(f"eval items={len(items)}  " + "  ".join(f"{h}-hop:{len(v)}" for h, v in sorted(by_hop.items())))
    print(f"→ {out}")


if __name__ == "__main__":
    main()
