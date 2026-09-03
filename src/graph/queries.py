"""Cypher — schema constraints + variable-length causal traversal (วัด hop).

ดู skill causal-graphrag §4. hop นับจากจำนวน causal edges บน path.

หมายเหตุสำคัญ (bug จริงที่เจอ): Neo4j ไม่รับ map/dict เป็น property ของ relationship
→ เก็บ evidence เป็น JSON string ในพร็อพเดียวชื่อ `evidence` (retriever json.loads).
`evidence IS NULL` ยังใช้ตรวจ traceability ได้ตามเดิม.
"""
from __future__ import annotations

CAUSAL_RELS = "FEEDS|OVERFLOWS_TO|FLOWS_TO|INUNDATES|RUNOFF_TO"

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
MATCH path = (src)-[rels:{CAUSAL_RELS}*2..6]->(p:Province {{name_en:$province}})
WITH path, length(path) AS hops,
     [n IN nodes(path) | coalesce(n.name, n.name_en)] AS chain,
     [r IN relationships(path) | r.evidence] AS evidences
RETURN hops, chain, evidences
ORDER BY hops
"""

# ── ทำนายชุดจังหวัดที่ท่วม: จาก "ต้นเหตุ active" (เขื่อนที่ล้น/บาร์ราจ *หรือ* ฝนที่ทำ runoff) ──
#   gate 2 ชั้นด้วยข้อมูลจริง (A1 de-circularized): (1) last_reach.overflow = true (ลำน้ำหลักล้น
#   ความจุจริงจาก river-gauge) (2) จังหวัดไม่มีคันกั้นน้ำป้องกัน (p.protected=false) — แทน threshold
#   ตั้งเอง 7.0–9.5 เดิม. ดู river_gauges_*.json + PROTECTED_PROVINCES.
CAUSAL_FLOOD_PREDICT = f"""
MATCH path = (src)-[rels:{CAUSAL_RELS}*2..6]->(p:Province)
WHERE src.active = true
WITH p, path, length(path) AS hops, nodes(path) AS ns, relationships(path) AS rs
WITH p, hops,
     ns[size(ns)-2] AS last_reach,
     [r IN rs | r.evidence] AS evidences,
     [n IN ns | coalesce(n.name, n.name_en)] AS chain
WHERE last_reach.overflow = true
  AND coalesce(p.protected, false) = false
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
#   (อัปเดต 2026-09-03: เริ่มจาก RainStation ไม่ใช่ Reservoir — ลุ่มน้ำสาขาที่ไม่มีเขื่อน
#    (ยม/สะแกกรัง/ท่าจีน) วัด hop จากเขื่อนไม่ได้. hop = สายเหตุ-ผลสั้นสุดจากต้นน้ำฝน →
#    ได้ bucket 2/3/4/5-hop ครบ: 2=จังหวัดต้นน้ำในสาขา, 3=เจ้าพระยาตอนล่างผ่านป่าสัก/สะแกกรัง,
#    4=จังหวัดจุดบรรจบ (ปากน้ำโพ), 5=ท่าจีน (แยกจากเจ้าพระยา).)
HOP_PER_PROVINCE = f"""
MATCH path = (src:RainStation)-[:{CAUSAL_RELS}*2..6]->(p:Province)
RETURN p.id AS pid, p.name_en AS province, min(length(path)) AS hops
ORDER BY hops, province
"""

# ── #6 early-warning: lead time (ชม.) = ผลรวม lag_hours ตามสายเหตุ-ผลที่สั้นสุดถึงจังหวัด ──
#   ใช้ gate เดียวกับการทำนาย (reach ล้น + ไม่มีคันกั้นน้ำ) → บอก "อีกกี่ ชม. จังหวัดจะท่วม"
LEAD_TIME_TO_PROVINCE = f"""
MATCH path = (src)-[rels:{CAUSAL_RELS}*2..6]->(p:Province {{name_en:$province}})
WHERE src.active = true
WITH p, nodes(path) AS ns, reduce(s=0, r IN rels | s + coalesce(r.lag_hours,0)) AS lag
WITH p, ns[size(ns)-2] AS last_reach, lag
WHERE last_reach.overflow = true AND coalesce(p.protected, false) = false
RETURN min(lag) AS lead_hours
"""

# ── traceability guard: ต้องได้ 0 ─────────────────────────────
COUNT_EDGES_WITHOUT_EVIDENCE = "MATCH ()-[e]->() WHERE e.evidence IS NULL RETURN count(e) AS n"
