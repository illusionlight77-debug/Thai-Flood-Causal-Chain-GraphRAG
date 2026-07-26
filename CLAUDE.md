# CLAUDE.md — Thai Flood Causal-Chain GraphRAG

> โปรเจกต์วิจัย: **"ทำไมจังหวัดนี้ถึงน้ำท่วม?"** — วัดว่า GraphRAG ที่เดินตาม *สายเหตุ-ผลจริง* (causal chain) ให้คำอธิบายที่ verify ได้ดีกว่า vector search แค่ไหน
> Research project: **"Why did this province flood?"** — measuring whether GraphRAG traversing a *real causal chain* produces more verifiable explanations than vector search over news reports.

ไฟล์นี้เป็นบริบทถาวรสำหรับ Claude Code อ่านทุกครั้งที่เปิด repo นี้ / This file is persistent context Claude Code should read on every session in this repo.

---

## 1. คำถามวิจัย / Research Question

**TH:** โครงงาน GraphRAG ทั่วไปวัด "hop count" แบบ *entity-relation* (เช่น มัสยิด → จังหวัด → ที่พัก) แต่ยังไม่มีใครวัดว่า hop count ที่เป็น **causal chain จริง**

```
ฝนต้นน้ำ → ระดับน้ำเขื่อน → น้ำล้นสปิลเวย์ → ระดับน้ำแม่น้ำท้ายน้ำ → น้ำท่วมจังหวัดปลายน้ำ
rain(upstream) → reservoir level → spillway overflow → downstream river level → downstream province flood
```

ยากขึ้นสำหรับ GraphRAG ในอัตราเดียวกับ hop แบบ entity-relation หรือไม่ — เป็นมิติใหม่ (causal ไม่ใช่แค่ relational).

**Hypothesis (H1):** การเดินกราฟตามสายเหตุ-ผลจริงให้คำอธิบายที่ traceable/verify ได้มากกว่าการสรุปจากรายงานข่าวน้ำท่วมด้วย vector search.

**Hypothesis (H2):** F1 ของ GraphRAG จะ *ไม่* ลดลงตามความยาว causal chain เร็วเท่ากับ F1 ของ vector-RAG (กราฟทน hop ได้ดีกว่า).

**Metric หลัก:** F1 แยกตามความยาวสายเหตุ-ผล
- **2-hop** = เขื่อนเดียว (rain → 1 reservoir → province)
- **4-hop** = ข้ามลุ่มน้ำ (rain → reservoir → river → confluence → downstream province)

เปรียบเทียบ 3 ระบบ: `causal-graphrag` (ของเรา) vs `entity-graphrag` (baseline relational) vs `vector-rag` (baseline).

---

## 2. Tech Stack

| Layer | Choice | หมายเหตุ |
|---|---|---|
| Graph DB | **Neo4j 5.x** (Docker) | เก็บ causal graph + spatial props; ใช้ Cypher variable-length paths วัด hop |
| Orchestration | **Python 3.11** | |
| RAG framework | **LlamaIndex** (`PropertyGraphIndex`) + fallback LangChain `GraphCypherQAChain` | เลือก LlamaIndex เป็นหลักเพราะ property-graph retriever ดีกว่าสำหรับงานนี้ |
| Geo | **GeoPandas** + Shapely | point-in-polygon: ลุ่มน้ำ → จังหวัดท้ายน้ำ (ทักษะที่มีอยู่แล้ว ไม่ต้องเรียนใหม่) |
| Embeddings/LLM | Claude (via API) สำหรับ generation; embedding model แยก (ระบุใน `.env`) | |
| Vector baseline | FAISS หรือ Chroma | |
| Eval | `ragas` + custom F1 ตาม causal-hop | |
| Test UI | **Streamlit** | หน้า "ทำไมจังหวัดนี้ถึงน้ำท่วม" + เทียบ 3 ระบบ side-by-side |

> ยึด stack นี้เว้นแต่ผู้ใช้สั่งเปลี่ยน / Stick to this stack unless the user says otherwise.

---

## 3. แหล่งข้อมูลจริง / Real Data Sources

| # | Source | Data | Access |
|---|---|---|---|
| D1 | **data.go.th** | ระดับน้ำสถานีโทรมาตร 313 สถานี (สสน./HII) | Dataset download / CKAN API |
| D2 | **thaiwater.net** | ระดับน้ำ/ฝน real-time, ระดับน้ำเขื่อน | Public API |
| D3 | **GISTDA** `disaster.gistda.or.th/flood/` | flood extent maps (พื้นที่น้ำท่วมจริง) | **STAC API** |
| D4 | ขอบเขตลุ่มน้ำ + ขอบเขตจังหวัด (shapefile/GeoJSON) | สำหรับ point-in-polygon | data.go.th / GISTDA |

**Ground truth ของ eval** = flood extent จริงจาก GISTDA (D3) — ใช้ตัดสินว่าคำตอบ "จังหวัด X ท่วม" ถูกหรือไม่.

รายละเอียด endpoint + วิธีเชื่อมต่อ ดู `README.md` → System All Links.

---

## 4. โครงสร้างกราฟ / Causal Graph Schema (Neo4j)

**Node labels:**
- `(:RainStation {id, name, lat, lon, basin})`
- `(:Reservoir {id, name, capacity, spillway_level, lat, lon, basin})`
- `(:RiverReach {id, name, basin, order})` — ช่วงลำน้ำ
- `(:Confluence {id, name})` — จุดบรรจบข้ามลุ่มน้ำ
- `(:Province {id, name_th, name_en, geometry})`

**Causal relationships (มีทิศทาง = ทิศการไหล):**
- `(:RainStation)-[:FEEDS {lag_hours}]->(:Reservoir)`
- `(:Reservoir)-[:OVERFLOWS_TO {spillway}]->(:RiverReach)`
- `(:RiverReach)-[:FLOWS_TO {lag_hours}]->(:RiverReach|:Confluence)`
- `(:RiverReach)-[:INUNDATES {threshold}]->(:Province)`

**กติกาสำคัญ:** ทุก relationship ต้องมี property `evidence` = pointer กลับไป source record (สถานี/timestamp/dataset id) เพื่อให้คำตอบ **traceable**. นี่คือหัวใจของ H1.

**hop counting:** ใช้ Cypher variable-length `-[:*2..4]->` แล้ว group ผลตาม path length เพื่อทำ F1-by-hop.

---

## 5. โครงสร้างโฟลเดอร์ / Repo Layout (เป้าหมาย)

```
Thai Flood Causal-Chain GraphRAG/
├── CLAUDE.md                ← ไฟล์นี้ (บริบทถาวร)
├── README.md                ← system tour, all links, UI, results, bugs, aha
├── KICKOFF.md               ← prompt แรกที่วางใน Claude Code
├── .claude/skills/          ← skills เฉพาะโปรเจกต์
│   ├── causal-graphrag/SKILL.md
│   └── geo-basin-to-province/SKILL.md
├── .env.example
├── docker-compose.yml       ← Neo4j
├── data/                    ← raw + processed (gitignored raw)
├── src/
│   ├── ingest/              ← ดึง D1–D4, สร้าง nodes/edges + evidence
│   ├── graph/               ← Neo4j client, schema, cypher queries
│   ├── geo/                 ← GeoPandas basin→province
│   ├── rag/                 ← causal_graphrag.py, entity_graphrag.py, vector_rag.py
│   └── eval/                ← f1_by_hop.py, build_eval_set.py
├── ui/                      ← Streamlit app
└── notebooks/               ← สำรวจข้อมูล
```

---

## 6. Workflow สำหรับ Claude Code

1. **อ่านก่อน:** `CLAUDE.md` (นี่) → `KICKOFF.md` → skills ที่เกี่ยว.
2. **ทำเป็นขั้น:** ingest → graph build → geo mapping → 3 retrievers → eval set → F1-by-hop → UI. อย่าข้าม eval set.
3. **ทุกครั้งที่สร้าง edge** ต้องแนบ `evidence` — ห้ามมี edge ลอย.
4. **Log ทุก aha / bug** ลง `README.md` (มี section ให้แล้ว) ทันทีที่เจอ ไม่ต้องรอจบ.
5. **Commit เล็ก ๆ** ต่อขั้นตอน; เขียน test สำหรับ f1_by_hop และ geo point-in-polygon.
6. **อย่า hardcode** ข้อสรุปงานวิจัย — ต้องมาจาก eval จริงเทียบ GISTDA ground truth.

---

## 7. Definition of Done (research)

- [ ] Causal graph โหลดจากข้อมูลจริง ≥1 เหตุการณ์น้ำท่วม (เช่น ลุ่มเจ้าพระยา)
- [ ] 3 retrievers รันได้บน eval set เดียวกัน
- [ ] F1-by-hop chart (2-hop vs 4-hop) สำหรับทั้ง 3 ระบบ
- [ ] Traceability score: % ของคำตอบที่ชี้ evidence กลับ source ได้
- [ ] Streamlit UI ตอบ "ทำไมจังหวัดนี้ถึงน้ำท่วม" + แสดง chain + evidence
- [ ] README มีผลลัพธ์จริง, บั๊ค, และ aha moments กรอกครบ

---

## 8. Guardrails

- Social-good / climate-resilience framing (สอดคล้อง NECTEC agenda) — เขียนให้ต่อยอด early-warning ได้.
- อย่ากล่าวอ้างเกินข้อมูล; ระบุ limitation ของข้อมูล real-time.
- เก็บ API key ใน `.env` เท่านั้น (ดู `.env.example`).
