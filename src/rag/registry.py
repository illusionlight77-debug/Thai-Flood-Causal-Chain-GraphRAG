"""สร้าง retriever ทั้ง 3 ด้วยอินเทอร์เฟซเดียวกัน (สำหรับ eval + UI)."""
from __future__ import annotations

from src.rag.base import Retriever


def build_retrievers() -> dict[str, Retriever]:
    from src.graph.client import Neo4jClient
    from src.rag.causal_graphrag import CausalGraphRAG
    from src.rag.entity_graphrag import EntityGraphRAG
    from src.rag.vector_rag import VectorRAG

    client = Neo4jClient()  # ใช้ร่วมกันสำหรับสองตัวที่พึ่งกราฟ
    return {
        "causal-graphrag": CausalGraphRAG(client),
        "entity-graphrag": EntityGraphRAG(client),
        "vector-rag": VectorRAG(),
    }
