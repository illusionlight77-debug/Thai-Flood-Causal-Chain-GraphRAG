"""เฟส 5 — รัน eval ครบวงจร: 3 ระบบ บน eval set เดียว → เขียนผลจริง.

ผลลัพธ์:
  data/processed/eval_results.json   ตัวเลขดิบ
  data/processed/results_table.md    ตาราง markdown (แปะ README)
"""
from __future__ import annotations

import json

from src.config import settings
from src.eval import build_eval_set
from src.eval.f1_by_hop import run_eval
from src.graph.client import Neo4jClient
from src.rag.registry import build_retrievers

SYSTEMS = ["causal-graphrag", "entity-graphrag", "vector-rag"]


def _fmt(v) -> str:
    return f"{v:.3f}" if isinstance(v, (int, float)) else str(v)


def to_markdown(results: dict) -> str:
    lines = ["### F1 by causal-hop length (Chao Phraya basin, 23-province universe)", "",
             "| System | F1@2 | F1@3 | F1@4 | F1@5 | ΔF1 (2→5) | F1 overall | Traceability | Latency (ms) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name in SYSTEMS:
        r = results[name]
        fb = r["f1_by_hop"]
        f2, f3, f4, f5 = (fb.get(str(h), 0.0) for h in (2, 3, 4, 5))
        d = f2 - f5
        lines.append(f"| {name} | {_fmt(f2)} | {_fmt(f3)} | {_fmt(f4)} | {_fmt(f5)} | {_fmt(d)} | "
                     f"{_fmt(r['f1_overall'])} | {_fmt(r['traceability'])} | {_fmt(r['avg_latency_ms'])} |")
    return "\n".join(lines)


def main() -> None:
    client = Neo4jClient()
    items = build_eval_set.build(client)
    retrievers = build_retrievers()
    results = run_eval(retrievers, items)

    (settings.data_processed_dir / "eval_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), "utf-8")
    md = to_markdown(results)
    (settings.data_processed_dir / "results_table.md").write_text(md, "utf-8")
    print(md)
    print(f"\neval items={len(items)}")
    client.close()


if __name__ == "__main__":
    main()
