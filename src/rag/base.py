"""Shared retriever contract — 3 ระบบต้อง implement เหมือนกันเป๊ะเพื่อเทียบกันได้.

causal_graphrag / entity_graphrag / vector_rag ทุกตัวรับ `answer(question)`
แล้วคืน `RetrieverAnswer` หน้าตาเดียวกัน → eval วัดด้วย harness เดียว.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class Evidence:
    """pointer กลับไป source record — หัวใจของ traceability (H1)."""

    station_id: str | None = None
    timestamp: str | None = None
    dataset: str | None = None

    @property
    def is_complete(self) -> bool:
        return all(v is not None for v in (self.station_id, self.timestamp, self.dataset))


@dataclass
class RetrieverAnswer:
    """ผลลัพธ์มาตรฐานจากทั้ง 3 retriever."""

    text: str                                  # คำอธิบายภาษาธรรมชาติ
    provinces: set[str] = field(default_factory=set)  # จังหวัดที่ระบบบอกว่าท่วม → เทียบ gold
    chain: list[str] = field(default_factory=list)    # ลำดับ node บน causal path
    hops: int = 0                              # ความยาว chain (นับจาก causal edges)
    evidence: list[Evidence] = field(default_factory=list)
    latency_s: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def is_traceable(self) -> bool:
        """traceable = มี evidence และทุกชิ้น complete."""
        return bool(self.evidence) and all(e.is_complete for e in self.evidence)


@runtime_checkable
class Retriever(Protocol):
    """อินเทอร์เฟซร่วมของทั้ง 3 ระบบ."""

    name: str

    def answer(self, question: str, **kwargs: Any) -> RetrieverAnswer:
        ...
