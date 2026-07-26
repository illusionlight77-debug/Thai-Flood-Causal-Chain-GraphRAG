"""เฟส 3 — โหลด nodes/edges เข้า Neo4j ตาม schema. ทุก edge มี evidence (JSON string).

รัน: python -m src.graph.load   (ต้องมี Neo4j ขึ้นอยู่ที่ bolt://localhost:7689)
ก่อนรัน ต้องมี fixture (เฟส 1) + inundates_edges.json (เฟส 2).
"""
from __future__ import annotations

import json

from src.config import settings
from src.graph import queries
from src.graph.client import Neo4jClient

_PROCESSED = settings.data_processed_dir


def _load_json(name: str):
    return json.loads((_PROCESSED / name).read_text("utf-8"))


def load(client: Neo4jClient | None = None) -> dict:
    client = client or Neo4jClient()
    nodes = _load_json("graph_nodes.json")
    edges = _load_json("graph_edges.json") + _load_json("inundates_edges.json")

    with client.session() as s:
        # constraints
        for c in queries.CONSTRAINTS:
            s.run(c)
        # ล้างของเดิม (idempotent reload)
        s.run("MATCH (n) DETACH DELETE n")

        # nodes — MERGE by label+id, set props ที่เหลือ
        for n in nodes:
            label = n["label"]
            props = {k: v for k, v in n.items() if k != "label"}
            s.run(f"MERGE (x:{label} {{id:$id}}) SET x += $props", id=n["id"], props=props)

        # edges — evidence เป็น map → serialize เป็น JSON string (Neo4j ไม่รับ map prop)
        for e in edges:
            props = {k: v for k, v in e.items() if k not in ("type", "src", "dst")}
            if isinstance(props.get("evidence"), dict):
                props["evidence"] = json.dumps(props["evidence"], ensure_ascii=False)
            s.run(
                f"MATCH (a {{id:$src}}), (b {{id:$dst}}) "
                f"MERGE (a)-[r:{e['type']}]->(b) SET r += $props",
                src=e["src"], dst=e["dst"], props=props,
            )

        counts = {
            "nodes": s.run("MATCH (n) RETURN count(n) AS n").single()["n"],
            "edges": s.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"],
            "edges_without_evidence": s.run(queries.COUNT_EDGES_WITHOUT_EVIDENCE).single()["n"],
        }
    return counts


def main() -> None:
    counts = load()
    print(f"loaded → nodes={counts['nodes']} edges={counts['edges']}")
    assert counts["edges_without_evidence"] == 0, "พบ edge ที่ไม่มี evidence — traceability พัง!"
    print("evidence ครบทุก edge ✔ (edges_without_evidence=0)")


if __name__ == "__main__":
    main()
