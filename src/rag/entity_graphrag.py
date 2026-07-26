"""entity-graphrag (baseline relational) — เดินกราฟแบบ entity-relation hop
ไม่ยึด causal direction/evidence. ใช้เทียบว่า causal chain ได้เปรียบไหม.
"""
from __future__ import annotations

from src.rag.base import RetrieverAnswer


class EntityGraphRAG:
    name = "entity-graphrag"

    def answer(self, question: str, **kwargs) -> RetrieverAnswer:
        raise NotImplementedError("Phase 4: entity-relation traversal (no causal evidence)")
