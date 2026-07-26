"""สร้างชุดคำถาม "ทำไมจังหวัด X ท่วม" + label ด้วย GISTDA ground truth + tag hop.

แต่ละ item: {question, province, event, hop (2|4), gold_provinces}.
2-hop = เขื่อนเดียว, 4-hop = ข้ามลุ่มน้ำ. gold มาจาก GISTDA flood extent (D3) เท่านั้น.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalItem:
    question: str
    province: str
    event: str
    hop: int                       # 2 หรือ 4
    gold_provinces: set[str] = field(default_factory=set)


def build() -> list[EvalItem]:
    raise NotImplementedError("Phase 5: generate questions + label with GISTDA flood extent")


if __name__ == "__main__":
    build()
