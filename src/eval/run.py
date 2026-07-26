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
    lines = ["### F1 by causal-hop length (on fixture: Chao Phraya 2022)", "",
             "| System | F1 @ 2-hop | F1 @ 4-hop | ΔF1 (2→4) | F1 overall | Traceability | Latency (ms) |",
             "|---|---|---|---|---|---|---|"]
    for name in SYSTEMS:
        r = results[name]
        f2 = r["f1_by_hop"].get("2", 0.0)
        f4 = r["f1_by_hop"].get("4", 0.0)
        d = f2 - f4
        lines.append(f"| {name} | {_fmt(f2)} | {_fmt(f4)} | {_fmt(d)} | "
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
