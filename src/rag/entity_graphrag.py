"""entity-graphrag (baseline relational) — เดินกราฟแบบ entity-relation:
ไม่สนทิศการไหล (undirected), ไม่กรอง threshold, ไม่ใช้ evidence.

เป็น baseline ที่ตอบว่า "จังหวัดที่เชื่อมโยงกันในกราฟ" = มักได้จังหวัดเกินจริง
(รวมต้นน้ำ/จังหวัดที่ไม่ท่วม) → precision ต่ำ, และไม่มี evidence → traceability = 0.
ใช้เทียบว่า causal direction + evidence ได้เปรียบแค่ไหน.
"""
from __future__ import annotations

import time

from src.graph.client import Neo4jClient
from src.rag._common import resolve_province
from src.rag.base import RetrieverAnswer

# undirected *2..4 relational hop — ไม่มีลูกศร, ไม่กรอง threshold, ไม่ดู evidence
_QUERY = """
MATCH (p:Province {name_en:$province})-[*2..4]-(q:Province)
RETURN DISTINCT q.name_en AS province
"""
_ONE_PATH = """
MATCH path = (p:Province {name_en:$province})-[*2..4]-(q:Province {name_en:$other})
RETURN [n IN nodes(path) | coalesce(n.name, n.name_en)] AS chain
LIMIT 1
"""


class EntityGraphRAG:
    name = "entity-graphrag"

    def __init__(self, client: Neo4jClient | None = None):
        self.client = client or Neo4jClient()

    def answer(self, question: str, province: str | None = None, **_) -> RetrieverAnswer:
        t0 = time.perf_counter()
        asked = resolve_province(question, province)
        provinces: set[str] = set()
        if asked:
            provinces = {r["province"] for r in self.client.run(_QUERY, province=asked)}
            provinces.add(asked)  # จังหวัดที่ถามก็นับว่าเกี่ยวข้อง

        # chain แค่ตัวอย่าง relational path (ไม่ใช่ causal) — ไม่มี evidence
        chain: list[str] = []
        other = next((p for p in provinces if p != asked), None)
        if asked and other:
            rows = self.client.run(_ONE_PATH, province=asked, other=other)
            if rows:
                chain = rows[0]["chain"]

        text = (f"จังหวัดที่เชื่อมโยงกับ{asked}ในกราฟ (entity-relation, ไม่สนทิศ/หลักฐาน): "
                + ", ".join(sorted(provinces)))
        return RetrieverAnswer(
            text=text, provinces=provinces, chain=chain,
            hops=len(chain) - 1 if chain else 0, evidence=[],  # baseline: ไม่มี evidence
            latency_s=time.perf_counter() - t0, meta={"asked": asked},
        )
