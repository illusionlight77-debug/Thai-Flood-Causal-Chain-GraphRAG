"""vector-rag (baseline) — TF-IDF over ข่าวน้ำท่วม, ดึง top-k แล้วสกัดชื่อจังหวัด.

ไม่มีโครงสร้าง chain/evidence: จังหวัดที่ตอบ = จังหวัดที่ปรากฏในข่าวที่ retrieve ได้
→ ได้เฉพาะจังหวัดที่ข่าว "รายงานถึง" (จังหวัดใหญ่เด่น, จังหวัดเล็กปลายสายมักหลุด)
และไม่มี evidence เชิงโครงสร้าง → traceability = 0. ใช้ char n-gram เพราะภาษาไทยไม่มีเว้นวรรค.
"""
from __future__ import annotations

import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.rag._common import news_corpus, provinces_mentioned, resolve_province
from src.rag.base import RetrieverAnswer


class VectorRAG:
    name = "vector-rag"

    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        self.docs = news_corpus()
        self._texts = [d["text"] for d in self.docs]
        self._vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self._matrix = self._vec.fit_transform(self._texts)

    def answer(self, question: str, province: str | None = None, **_) -> RetrieverAnswer:
        t0 = time.perf_counter()
        asked = resolve_province(question, province)
        qv = self._vec.transform([question])
        sims = cosine_similarity(qv, self._matrix)[0]
        top_idx = sims.argsort()[::-1][: self.top_k]

        provinces: set[str] = set()
        cited: list[str] = []
        for i in top_idx:
            provinces |= provinces_mentioned(self._texts[i])
            cited.append(self.docs[i]["id"])

        text = (f"จากข่าวที่เกี่ยวข้องที่สุด ({', '.join(cited)}) จังหวัดที่ถูกกล่าวถึงว่าท่วม: "
                + (", ".join(sorted(provinces)) or "—"))
        return RetrieverAnswer(
            text=text, provinces=provinces, chain=[], hops=0, evidence=[],  # ไม่มี chain/evidence
            latency_s=time.perf_counter() - t0,
            meta={"asked": asked, "retrieved_docs": cited},
        )
