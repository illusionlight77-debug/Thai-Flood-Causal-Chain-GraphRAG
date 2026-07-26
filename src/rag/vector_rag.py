"""vector-rag (baseline) — FAISS/Chroma บนข่าวน้ำท่วม. ไม่มี chain/evidence เชิงโครงสร้าง."""
from __future__ import annotations

from src.rag.base import RetrieverAnswer


class VectorRAG:
    name = "vector-rag"

    def answer(self, question: str, **kwargs) -> RetrieverAnswer:
        raise NotImplementedError("Phase 4: FAISS/Chroma retrieval over flood news")
