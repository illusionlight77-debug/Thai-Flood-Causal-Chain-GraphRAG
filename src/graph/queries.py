"""Cypher — schema constraints + variable-length causal traversal (วัด hop).

ดู skill causal-graphrag §4. hop นับจากจำนวน causal edges บน path.

หมายเหตุสำคัญ (bug จริงที่เจอ): Neo4j ไม่รับ map/dict เป็น property ของ relationship
→ เก็บ evidence เป็น JSON string ในพร็อพเดียวชื่อ `evidence` (retriever json.loads).
`evidence IS NULL` ยังใช้ตรวจ traceability ได้ตามเดิม.
"""
from __future__ import annotations

CAUSAL_RELS = "FEEDS|OVERFLOWS_TO|FLOWS_TO|INUNDATES"

# ── constraints ────────────────────────────────────────────────
CONSTRAINTS = [
    "CREATE CONSTRAINT rainstation_id IF NOT EXISTS FOR (n:RainStation) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT reservoir_id  IF NOT EXISTS FOR (n:Reservoir)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT riverreach_id IF NOT EXISTS FOR (n:RiverReach)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT confluence_id IF NOT EXISTS FOR (n:Confluence)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT province_id   IF NOT EXISTS FOR (n:Province)    REQUIRE n.id IS UNIQUE",
]

# ── causal chain 2..4 hop → Province ที่ระบุ (ใช้อธิบายจังหวัดเดียว) ──
CAUSAL_CHAIN_TO_PROVINCE = f"""
MATCH path = (src)-[rels:{CAUSAL_RELS}*2..4]->(p:Province {{name_en:$province}})
WITH path, length(path) AS hops,
     [n IN nodes(path) | coalesce(n.name, n.name_en)] AS chain,
     [r IN relationships(path) | r.evidence] AS evidences
RETURN hops, chain, evidences
ORDER BY hops
"""

# ── ทำนายชุดจังหวัดที่ท่วม: จากเขื่อนที่ active เดินตาม chain + กรองด้วย threshold ──
#   last_reach.level >= INUNDATES.threshold → จังหวัดนั้นท่วมจริง (ใช้ evidence เชิงกายภาพ)
CAUSAL_FLOOD_PREDICT = f"""
MATCH path = (src:Reservoir {{active:true}})-[rels:{CAUSAL_RELS}*2..4]->(p:Province)
WITH p, path, length(path) AS hops, nodes(path) AS ns, relationships(path) AS rs
WITH p, hops,
     ns[size(ns)-2] AS last_reach,
     last(rs) AS inun,
     [r IN rs | r.evidence] AS evidences,
     [n IN ns | coalesce(n.name, n.name_en)] AS chain
WHERE inun.threshold IS NULL OR last_reach.level >= inun.threshold
RETURN p.id AS pid, p.name_en AS province,
       min(hops) AS hops,
       head(collect(chain)) AS chain,
       head(collect(evidences)) AS evidences
ORDER BY hops, province
"""

# ── hop ต่ำสุดจากเขื่อน "ใดก็ได้" ไปแต่ละจังหวัด — ใช้ tag hop ให้ eval ──
#   ⚠️ ต้องไม่กรอง active! hop = ความยาวสายเหตุ-ผลเชิงโครงสร้าง (2-hop เขื่อนเดียว /
#   4-hop ข้ามลุ่มน้ำผ่านจุดบรรจบ) — เป็นสมบัติของภูมิศาสตร์ ไม่ใช่ของเหตุการณ์.
#   (แก้ correctness bug 2026-07-27: เดิมกรอง active:true ทำให้ hop-tag เลื่อนตามว่าเขื่อนไหน
#    active ในเหตุการณ์นั้น → bucket 2/4-hop ของ eval set ไม่คงที่ ดู README.)
HOP_PER_PROVINCE = f"""
MATCH path = (src:Reservoir)-[:{CAUSAL_RELS}*2..4]->(p:Province)
RETURN p.id AS pid, p.name_en AS province, min(length(path)) AS hops
ORDER BY hops, province
"""

# ── traceability guard: ต้องได้ 0 ─────────────────────────────
COUNT_EDGES_WITHOUT_EVIDENCE = "MATCH ()-[e]->() WHERE e.evidence IS NULL RETURN count(e) AS n"
