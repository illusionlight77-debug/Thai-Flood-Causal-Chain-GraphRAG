"""Cypher — schema constraints + variable-length causal traversal (วัด hop).

ดู skill causal-graphrag §4. hop นับจากจำนวน causal edges บน path.
"""
from __future__ import annotations

# ── constraints (เรียกตอน load) ────────────────────────────────
CONSTRAINTS = [
    "CREATE CONSTRAINT rainstation_id IF NOT EXISTS FOR (n:RainStation) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT reservoir_id  IF NOT EXISTS FOR (n:Reservoir)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT riverreach_id IF NOT EXISTS FOR (n:RiverReach)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT confluence_id IF NOT EXISTS FOR (n:Confluence)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT province_id   IF NOT EXISTS FOR (n:Province)    REQUIRE n.id IS UNIQUE",
]

# ── causal chain 2..4 hop → Province ───────────────────────────
CAUSAL_CHAIN = """
MATCH path = (src)-[:FEEDS|OVERFLOWS_TO|FLOWS_TO|INUNDATES*2..4]->(p:Province {name_en:$province})
WITH path, length(path) AS hops,
     [rel IN relationships(path) | rel.evidence] AS evidences
RETURN hops,
       [n IN nodes(path) | coalesce(n.name, n.name_en)] AS chain,
       evidences
ORDER BY hops
"""

# ── ตรวจ traceability: ต้องได้ 0 ───────────────────────────────
COUNT_EDGES_WITHOUT_EVIDENCE = """
MATCH ()-[e]->() WHERE e.evidence IS NULL RETURN count(e) AS n
"""
