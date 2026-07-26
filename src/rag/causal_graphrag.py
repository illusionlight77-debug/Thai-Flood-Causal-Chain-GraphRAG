"""causal-graphrag (ของเรา) — เดิน causal chain บน Neo4j + กรอง threshold + evidence.

flow (skill causal-graphrag §5):
  (a) resolve จังหวัดที่ถาม
  (b) รัน Cypher CAUSAL_FLOOD_PREDICT → ชุดจังหวัดท่วม (threshold-filtered) + chain + evidence
  (c) ประกอบคำอธิบายจาก chain (deterministic; ต่อ Claude ได้ถ้ามี key — ปิดเป็น default
      เพื่อให้ eval reproducible)
  (d) แนบ evidence[] ของ chain จังหวัดที่ถามกลับมาเสมอ → traceable
chain มาจาก Cypher เท่านั้น (ไม่ให้ LLM เดา).
"""
from __future__ import annotations

import json
import time

from src.graph.client import Neo4jClient
from src.graph import queries
from src.rag._common import resolve_province
from src.rag.base import Evidence, RetrieverAnswer


def _parse_evidence(raw_list) -> list[Evidence]:
    out = []
    for raw in raw_list or []:
        try:
            d = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except (json.JSONDecodeError, TypeError):
            d = {}
        out.append(Evidence(d.get("station_id"), d.get("timestamp"), d.get("dataset")))
    return out


class CausalGraphRAG:
    name = "causal-graphrag"

    def __init__(self, client: Neo4jClient | None = None):
        self.client = client or Neo4jClient()

    def _predict(self) -> dict[str, dict]:
        """{name_en: {hops, chain, evidences}} ของจังหวัดที่ท่วม (threshold-filtered)."""
        rows = self.client.run(queries.CAUSAL_FLOOD_PREDICT)
        return {r["province"]: {"hops": r["hops"], "chain": r["chain"],
                                "evidences": r["evidences"]} for r in rows}

    def answer(self, question: str, province: str | None = None, **_) -> RetrieverAnswer:
        t0 = time.perf_counter()
        asked = resolve_province(question, province)
        pred = self._predict()
        provinces = set(pred.keys())

        row = pred.get(asked) if asked else None
        if row:
            chain = row["chain"]
            hops = row["hops"]
            evidence = _parse_evidence(row["evidences"])
            text = (f"จังหวัด{asked}ท่วมจากสายเหตุ-ผล {hops}-hop: "
                    + " → ".join(chain)
                    + f". ยืนยันด้วยหลักฐาน {len(evidence)} จุด (ระดับน้ำ ≥ threshold).")
        else:
            chain, hops, evidence = [], 0, []
            text = (f"causal graph ไม่พบสายเหตุ-ผลที่ทำให้{asked or 'จังหวัดนี้'}ท่วม "
                    f"(ระดับน้ำไม่ถึง threshold).")

        return RetrieverAnswer(
            text=text, provinces=provinces, chain=chain, hops=hops, evidence=evidence,
            latency_s=time.perf_counter() - t0,
            meta={"asked": asked, "predicted_count": len(provinces)},
        )
