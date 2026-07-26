"""F1-by-causal-hop + traceability — metric หลักของงานวิจัย.

f1() implement เต็มแล้ว (มี test). ส่วน run_eval() ยัง stub รอ retriever + eval set
จากเฟส 4/5. ห้าม hardcode ตัวเลขผลลง README — ต้องมาจาก run_eval() จริง.
"""
from __future__ import annotations

from statistics import mean
from typing import Iterable, Sequence


def f1(pred: set[str], gold: set[str]) -> float:
    """F1 ของเซตจังหวัด. pred = ระบบทำนายท่วม, gold = GISTDA flood extent."""
    if not pred or not gold:
        return 0.0
    tp = len(pred & gold)
    if tp == 0:
        return 0.0
    precision = tp / len(pred)
    recall = tp / len(gold)
    return 2 * precision * recall / (precision + recall)


def f1_by_hop(
    predictions: Sequence[tuple[int, set[str], set[str]]],
    hop_buckets: Iterable[int] = (2, 4),
) -> dict[int, float]:
    """group ผลตามความยาว chain แล้วเฉลี่ย F1.

    predictions: ลำดับของ (hop, pred_provinces, gold_provinces).
    คืน {2: mean_f1, 4: mean_f1}.
    """
    out: dict[int, float] = {}
    for bucket in hop_buckets:
        items = [(p, g) for hop, p, g in predictions if hop == bucket]
        out[bucket] = mean(f1(p, g) for p, g in items) if items else 0.0
    return out


def traceability(flags: Sequence[bool]) -> float:
    """สัดส่วนคำตอบที่ traceable (evidence ครบ)."""
    return mean(1.0 if f else 0.0 for f in flags) if flags else 0.0


def run_eval(retriever, eval_set) -> dict:  # noqa: ANN001 — types มาเฟส 4/5
    """รัน retriever บน eval set → F1-by-hop + traceability. (stub เฟส 5)"""
    raise NotImplementedError("Phase 5: wire retriever + GISTDA-labeled eval set")
