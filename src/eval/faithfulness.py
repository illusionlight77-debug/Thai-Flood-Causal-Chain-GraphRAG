"""Deterministic faithfulness scorer for the causal-graphrag LLM explanations.

The causal explanation is generated *grounded* on the chain + evidence. This checks —
without another LLM, so it is reproducible — whether the explanation stays within that
grounding: every province or river it names must be the asked province, appear in the
causal chain, or otherwise be supported. A name that is neither (e.g. a cross-basin river
like "แม่น้ำโขง" in a Chao Phraya answer, or an unrelated province) is an unsupported
mention = a hallucination.

This catches exactly the failure that made us drop gpt-oss-120b (it invented "แม่น้ำโขง"
in a Chao Phraya explanation). vector-rag / entity-graphrag have no grounded explanation,
so faithfulness applies to the causal system's explanations.

score = supported_geo_mentions / (supported + unsupported); 1.0 if it names no geography
beyond its grounding. faithful = (no unsupported mention).
"""
from __future__ import annotations

from typing import Iterable, Sequence

# rivers NOT in the Chao Phraya causal system — naming one in a CP explanation = hallucination
CHAO_PHRAYA_BLOCKLIST = ("โขง", "ชี", "มูล", "สาละวิน", "แม่กลอง", "บางปะกง", "ตาปี", "สงคราม")


def score_explanation(text: str, chain: Sequence[str], asked_th: str,
                      all_province_th: Iterable[str],
                      blocklist_rivers: Sequence[str] = CHAO_PHRAYA_BLOCKLIST) -> dict:
    if not text:
        return {"score": None, "faithful": None, "unsupported": [], "n_geo": 0}
    chain_text = " ".join(chain or [])
    supported, unsup = 0, []
    for th in all_province_th:
        if th and th in text:
            if th == asked_th or th in chain_text:
                supported += 1
            else:
                unsup.append(th)
    for r in blocklist_rivers:
        if r in text and r not in chain_text:
            unsup.append(r)
    total = supported + len(unsup)
    score = 1.0 if total == 0 else round(supported / total, 3)
    return {"score": score, "faithful": len(unsup) == 0, "unsupported": unsup, "n_geo": total}


def aggregate(per_province: dict, sys_key: str = "causal-graphrag") -> dict:
    """รวม faithfulness ของทุกจังหวัดที่ causal ทำนาย (มีคำอธิบาย)."""
    scores, faithful = [], []
    for p, x in per_province.items():
        fa = x["systems"].get(sys_key, {}).get("faithfulness")
        if fa and fa.get("score") is not None:
            scores.append(fa["score"])
            faithful.append(1.0 if fa["faithful"] else 0.0)
    if not scores:
        return {"n": 0, "mean_score": None, "pct_fully_faithful": None}
    return {"n": len(scores),
            "mean_score": round(sum(scores) / len(scores), 3),
            "pct_fully_faithful": round(100 * sum(faithful) / len(faithful), 1)}
