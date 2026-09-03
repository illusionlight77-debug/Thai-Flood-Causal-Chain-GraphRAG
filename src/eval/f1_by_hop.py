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
    hop_buckets: Iterable[int] = (2, 3, 4, 5, 6, 7),
) -> dict[int, float]:
    """group ผลตามความยาว chain แล้วเฉลี่ย F1.

    predictions: ลำดับของ (hop, pred_provinces, gold_provinces).
    คืน {2: .., 3: .., 4: .., 5: ..} (multi-hop granularity — วัด H2 ละเอียดขึ้น).
    """
    out: dict[int, float] = {}
    for bucket in hop_buckets:
        items = [(p, g) for hop, p, g in predictions if hop == bucket]
        out[bucket] = mean(f1(p, g) for p, g in items) if items else 0.0
    return out


def traceability(flags: Sequence[bool]) -> float:
    """สัดส่วนคำตอบที่ traceable (evidence ครบ)."""
    return mean(1.0 if f else 0.0 for f in flags) if flags else 0.0


def eval_one_system(retriever, eval_items) -> dict:  # noqa: ANN001
    """รัน retriever ตัวเดียวบน eval set → F1-by-hop + traceability + latency."""
    preds = []          # (hop, pred_set, gold_set)
    trace_flags = []    # answer traceable?
    latencies = []
    for it in eval_items:
        ans = retriever.answer(it.question, province=it.province)
        preds.append((it.hop, set(ans.provinces), set(it.gold_provinces)))
        trace_flags.append(ans.is_traceable)
        latencies.append(ans.latency_s)
    hop_scores = f1_by_hop(preds)
    return {
        "f1_by_hop": {str(k): round(v, 4) for k, v in hop_scores.items()},
        "f1_overall": round(mean(f1(p, g) for _, p, g in preds), 4) if preds else 0.0,
        "traceability": round(traceability(trace_flags), 4),
        "avg_latency_ms": round(1000 * mean(latencies), 2) if latencies else 0.0,
    }


def run_eval(retrievers: dict, eval_items) -> dict:  # noqa: ANN001
    """รันทั้ง 3 ระบบบน eval set เดียวกัน → ผลเทียบกัน (ตัวเลขจริง ห้าม hardcode)."""
    return {name: eval_one_system(r, eval_items) for name, r in retrievers.items()}
