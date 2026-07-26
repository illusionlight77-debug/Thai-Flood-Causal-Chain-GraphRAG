"""causal-graphrag (ของเรา) — LlamaIndex PropertyGraphIndex บน Neo4j causal graph.

flow: resolve จังหวัด+ช่วงเวลา → รัน Cypher CAUSAL_CHAIN ดึง chain+evidence →
ส่ง chain เป็น context ให้ Claude generate → แนบ evidence[] กลับมาเสมอ.
chain ต้องมาจาก Cypher เท่านั้น (ห้ามให้ LLM เดา). ดู skill causal-graphrag §5.
"""
from __future__ import annotations

from src.rag.base import RetrieverAnswer


class CausalGraphRAG:
    name = "causal-graphrag"

    def answer(self, question: str, **kwargs) -> RetrieverAnswer:
        raise NotImplementedError("Phase 4: PropertyGraphIndex + Cypher chain retrieval")
