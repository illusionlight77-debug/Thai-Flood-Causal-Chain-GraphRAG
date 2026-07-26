---
name: causal-graphrag
description: >
  Build and query the Thai flood CAUSAL graph in Neo4j (rain → reservoir →
  spillway → river reach → downstream province) and score retrieval with
  F1-by-causal-hop. Use whenever adding causal nodes/edges, writing Cypher
  variable-length traversals, wiring the causal-graphrag retriever, or computing
  F1/traceability by chain length (2-hop vs 4-hop). Every edge MUST carry an
  `evidence` property. Not for pure GIS point-in-polygon (use geo-basin-to-province).
---

# Skill: causal-graphrag

หัวใจของงานวิจัย: กราฟเดินตาม *สายเหตุ-ผลจริง* + วัด F1 แยกตามความยาว chain.
Core of the study: traverse a *real causal chain* and score F1 by chain length.

> ℹ️ ให้ Claude Code เห็น skill นี้อัตโนมัติ: ย้าย/symlink โฟลเดอร์นี้ไป `.claude/skills/`
> (session นี้เขียน `.claude/` ไม่ได้จึงวางไว้ที่ `skills/` ก่อน).

## 1. กติกาเหล็ก / Hard rules
1. **ทุก relationship ต้องมี `evidence`** = `{station_id, timestamp, dataset}` ชี้กลับ source. ถ้าไม่มี evidence ห้ามสร้าง edge — traceability ทั้งงานพึ่งข้อนี้.
2. ทิศทางของ relationship = ทิศการไหลของน้ำเสมอ.
3. hop นับจาก **จำนวน causal edges** บน path ไม่ใช่จำนวน node type.

## 2. Schema (ย่อ — ฉบับเต็มใน CLAUDE.md §4)
```
(:RainStation)-[:FEEDS {lag_hours, evidence}]->(:Reservoir)
(:Reservoir)-[:OVERFLOWS_TO {spillway, evidence}]->(:RiverReach)
(:RiverReach)-[:FLOWS_TO {lag_hours, evidence}]->(:RiverReach|:Confluence)
(:RiverReach)-[:INUNDATES {threshold, evidence}]->(:Province)
```

## 3. สร้าง edge พร้อม evidence (Cypher pattern)
```cypher
MATCH (r:Reservoir {id:$res}), (rr:RiverReach {id:$reach})
MERGE (r)-[e:OVERFLOWS_TO]->(rr)
SET e.spillway = $spillway,
    e.evidence = { station_id:$sid, timestamp:$ts, dataset:$ds };
```

## 4. เดินกราฟตาม causal chain + นับ hop
2-hop (เขื่อนเดียว) → 4-hop (ข้ามลุ่มน้ำ):
```cypher
MATCH path = (src:RainStation)-[:FEEDS|OVERFLOWS_TO|FLOWS_TO|INUNDATES*2..4]->(p:Province {name_en:$prov})
WITH path, length(path) AS hops,
     [rel IN relationships(path) | rel.evidence] AS evidences
RETURN hops, [n IN nodes(path) | coalesce(n.name, n.name_en)] AS chain, evidences
ORDER BY hops;
```
- `hops` → ใช้ bucket 2-hop vs 4-hop.
- `evidences` → ต้องไม่มี null ทุกตัว = คำตอบ traceable.

## 5. causal-graphrag retriever (LlamaIndex)
- ใช้ `PropertyGraphIndex` ต่อ Neo4j (`Neo4jPropertyGraphStore`).
- retriever step: (a) resolve จังหวัด+ช่วงเวลาเป็น node, (b) รัน Cypher §4 ดึง chain+evidence, (c) ส่ง chain เป็น context ให้ LLM generate คำอธิบาย, (d) แนบ evidence list กลับมาด้วยเสมอ.
- อินเทอร์เฟซให้ตรงกับ `entity_graphrag` และ `vector_rag`: `answer(question) -> {text, chain, hops, evidence[]}`.

## 6. F1-by-hop + traceability (src/eval/f1_by_hop.py)
```python
# predicted = จังหวัดที่ระบบบอกว่าท่วม ; gold = จาก GISTDA flood extent
def f1(pred:set, gold:set):
    tp=len(pred&gold)
    if not pred or not gold: return 0.0
    p=tp/len(pred); r=tp/len(gold)
    return 0.0 if p+r==0 else 2*p*r/(p+r)

# bucket ตามความยาว chain ของแต่ละคำถาม
for hop_bucket in (2, 4):
    items=[q for q in eval_set if q.hop==hop_bucket]
    score=mean(f1(sys.answer(q).provinces, q.gold) for q in items)

# traceability = สัดส่วนคำตอบที่ evidence ครบ (ไม่มี null) และ resolve source ได้
trace = mean(all(e is not None for e in sys.answer(q).evidence) for q in items)
```
กรอกผลลง README → Results (ห้าม hardcode).

## 7. Checklist ก่อนปิดงาน causal graph
- [ ] ไม่มี edge ที่ `evidence IS NULL` (`MATCH ()-[e]->() WHERE e.evidence IS NULL RETURN count(e)` = 0)
- [ ] path 2-hop และ 4-hop ดึงได้จริงจาก event ทดสอบ
- [ ] retriever คืน `evidence[]` ครบทุกคำตอบ
- [ ] F1-by-hop + traceability เขียนลง README

## Anti-patterns
- ❌ สร้าง edge โดยไม่มี evidence.
- ❌ นับ hop จาก node types แทน causal edges.
- ❌ ให้ LLM เดา chain เอง — chain ต้องมาจาก Cypher เท่านั้น.
