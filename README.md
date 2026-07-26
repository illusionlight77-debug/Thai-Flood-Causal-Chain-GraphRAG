# Thai Flood Causal-Chain GraphRAG 🌊

**"ทำไมจังหวัดนี้ถึงน้ำท่วม?" / "Why did this province flood?"**

ระบบตอบคำถามน้ำท่วมโดยเดินกราฟตาม *สายเหตุ-ผลจริง* (ฝน → เขื่อน → แม่น้ำ → จังหวัด) แล้ววัดว่าให้คำอธิบายที่ **ตรวจสอบย้อนกลับได้ (traceable)** ดีกว่าการค้นข่าวด้วย vector search แค่ไหน — วัดด้วย **F1 แยกตามความยาว causal chain**.

> A flood-explanation system that walks a *real causal chain* and measures how much more verifiable its answers are than vector search over news, scored by **F1 per causal-hop length**.

---

## 📑 สารบัญ / Table of Contents
1. [System Tour](#-system-tour)
2. [System — All Links](#-system--all-links)
3. [Test UI (หน้าทดสอบใช้งาน)](#-test-ui-หน้าทดสอบใช้งาน)
4. [Results (ผลลัพธ์)](#-results-ผลลัพธ์)
5. [Bugs & Fixes (บั๊คที่เจอ)](#-bugs--fixes-บั๊คที่เจอ)
6. [Research Conclusions (ข้อสรุปงานวิจัย)](#-research-conclusions-ข้อสรุปงานวิจัย)
7. [Aha Moments](#-aha-moments)
8. [Quickstart](#-quickstart)

---

## 🗺️ System Tour

ไล่จากข้อมูลดิบ → กราฟเหตุผล → 3 ระบบตอบคำถาม → การวัดผล → หน้าเว็บ.

```
                         ┌─────────────────────────────────────────────┐
  D1 data.go.th ─┐       │  INGEST (src/ingest)                         │
  D2 thaiwater ──┼──────▶│  ดึงฝน/ระดับน้ำ/เขื่อน + flood extent        │
  D3 GISTDA STAC ┤       │  → nodes + edges (แนบ evidence ทุกเส้น)      │
  D4 basin/prov ─┘       └───────────────┬─────────────────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────┐
                    │  GEO (src/geo)  GeoPandas point-in-polygon │
                    │  ลุ่มน้ำ → จังหวัดท้ายน้ำ                  │
                    └────────────────────┬─────────────────────┘
                                         │
                        ┌────────────────▼────────────────┐
                        │  Neo4j causal graph              │
                        │  Rain→Reservoir→River→Province   │
                        └───┬───────────┬───────────┬──────┘
                            │           │           │
              ┌─────────────▼──┐ ┌──────▼───────┐ ┌─▼────────────┐
              │ causal-graphrag│ │entity-graphrag│ │  vector-rag  │
              │  (ของเรา)      │ │  (baseline)   │ │  (baseline)  │
              └─────────────┬──┘ └──────┬───────┘ └─┬────────────┘
                            └───────────┼───────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │  EVAL (src/eval)              │
                        │  F1-by-hop (2-hop vs 4-hop)  │
                        │  Traceability score          │
                        │  ground truth = GISTDA D3    │
                        └───────────────┬───────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │  Streamlit UI (ui/)          │
                        │  "ทำไมจังหวัดนี้ถึงน้ำท่วม"    │
                        └───────────────────────────────┘
```

**เดินระบบทีละสถานี / walk the pipeline:**
1. **Ingest** — ดึง D1–D4, สร้าง node/edge. กติกา: ทุก edge ต้องมี `evidence` (station id + timestamp + dataset).
2. **Geo** — GeoPandas จับคู่ลุ่มน้ำ↔จังหวัดท้ายน้ำ (point-in-polygon) → สร้าง `INUNDATES` edges.
3. **Graph** — โหลดเข้า Neo4j; ใช้ Cypher `-[:*2..4]->` วัด hop.
4. **Retrievers** — 3 ตัวใช้ eval set เดียวกัน.
5. **Eval** — F1 แยกตาม chain length + traceability, เทียบ ground truth GISTDA.
6. **UI** — Streamlit ถามตอบ + แสดง chain + evidence.

---

## 🔗 System — All Links

### แหล่งข้อมูล / Data sources
| Source | Link | ใช้ทำอะไร |
|---|---|---|
| data.go.th (ระดับน้ำ 313 สถานี, สสน./HII) | https://data.go.th | ระดับน้ำโทรมาตร (D1) |
| thaiwater.net | https://www.thaiwater.net | ฝน/ระดับน้ำ/เขื่อน real-time (D2) |
| thaiwater API portal | https://api.thaiwater.net | REST endpoints (D2) |
| GISTDA flood portal | https://disaster.gistda.or.th/flood/ | flood extent maps (D3) |
| GISTDA STAC API | https://disaster.gistda.or.th/flood/ *(STAC root — ยืนยัน path ตอน ingest)* | flood extent เป็น ground truth (D3) |
| ขอบเขตลุ่มน้ำ/จังหวัด | data.go.th (ค้น "ลุ่มน้ำ", "ขอบเขตจังหวัด") | shapefile/GeoJSON (D4) |

### เครื่องมือ / Tooling
| Tool | Link |
|---|---|
| Neo4j (Docker) | http://localhost:7476 (Browser) · `bolt://localhost:7689` |
| Streamlit UI | http://localhost:8501 |

> **พอร์ต host เลือกเลี่ยงการชนกับ container อื่นในเครื่องนี้** (สำรวจด้วย `docker ps` ตอนเฟส 0):
> Neo4j default `7474/7475/7687/7688` ถูกจองแล้ว → โปรเจกต์นี้ใช้ **HTTP 7476 · Bolt 7689 · Streamlit 8501**.
> ค่าเหล่านี้ตั้งใน `.env` (`NEO4J_HTTP_PORT` / `NEO4J_BOLT_PORT` / `STREAMLIT_PORT`) และ `docker-compose.yml` อ่านต่อ.
| LlamaIndex PropertyGraph | https://docs.llamaindex.ai |
| GeoPandas | https://geopandas.org |
| ragas (eval) | https://docs.ragas.io |

### ภายใน repo / Internal
| ไฟล์ | หน้าที่ |
|---|---|
| `CLAUDE.md` | บริบทถาวร + schema + workflow |
| `KICKOFF.md` | prompt แรกสำหรับ Claude Code |
| `.claude/skills/causal-graphrag/SKILL.md` | สร้าง/query causal graph + F1-by-hop |
| `.claude/skills/geo-basin-to-province/SKILL.md` | point-in-polygon ลุ่มน้ำ→จังหวัด |
| `docker-compose.yml` | Neo4j |
| `.env.example` | ตัวแปรแวดล้อม + API keys |

> ⚠️ ยืนยัน endpoint ที่แน่นอนของ STAC/CKAN ตอน ingest จริง (โครงสร้าง API อาจเปลี่ยน) แล้วอัปเดตตารางนี้.

---

## 🖥️ Test UI (หน้าทดสอบใช้งาน)

**Streamlit** `ui/app.py` → `streamlit run ui/app.py` → http://localhost:8501

องค์ประกอบหน้าจอที่ต้องมี:
- **เลือกจังหวัด + ช่วงเวลา** ของเหตุการณ์น้ำท่วม.
- **ปุ่มถาม:** "ทำไมจังหวัดนี้ถึงน้ำท่วม?"
- **แผง 3 คอลัมน์เทียบกัน:** `causal-graphrag` / `entity-graphrag` / `vector-rag` — คำตอบ + เวลาที่ใช้.
- **Causal chain viewer:** วาด path ฝน→เขื่อน→แม่น้ำ→จังหวัด พร้อม hop count.
- **Evidence panel:** คลิก edge แล้วเห็น source record (station id, timestamp, dataset) → พิสูจน์ traceability.
- **แผนที่:** overlay flood extent จริงจาก GISTDA เทียบคำตอบ.
- **ตัวชี้วัดสด:** hop length, F1 (ถ้าอยู่ใน eval set), traceability ✓/✗.

*(เก็บ screenshot ใส่ `docs/ui-*.png` แล้วลิงก์ที่นี่เมื่อทำเสร็จ)*

---

## 📊 Results (ผลลัพธ์)

> กรอกด้วยตัวเลขจริงจาก `src/eval` — **ห้าม hardcode**. ตารางด้านล่างเป็น template.

### F1 by causal-hop length
| System | F1 @ 2-hop (เขื่อนเดียว) | F1 @ 4-hop (ข้ามลุ่มน้ำ) | ΔF1 (ลดลง) |
|---|---|---|---|
| causal-graphrag (ours) | _TBD_ | _TBD_ | _TBD_ |
| entity-graphrag | _TBD_ | _TBD_ | _TBD_ |
| vector-rag | _TBD_ | _TBD_ | _TBD_ |

### Traceability (% คำตอบที่ชี้ evidence กลับ source ได้)
| System | Traceability % |
|---|---|
| causal-graphrag | _TBD_ |
| entity-graphrag | _TBD_ |
| vector-rag | _TBD_ |

### เหตุการณ์ที่ทดสอบ / Test events
| Event | ลุ่มน้ำ | ช่วงเวลา | #จังหวัด | ground truth |
|---|---|---|---|---|
| _เช่น เจ้าพระยา 2565_ | _TBD_ | _TBD_ | _TBD_ | GISTDA D3 |

---

## 🐞 Bugs & Fixes (บั๊คที่เจอ)

> บันทึกทันทีที่เจอ — วันที่ / อาการ / สาเหตุ / วิธีแก้ / กระทบข้อสรุปไหม.

| วันที่ | Bug (อาการ) | Root cause | Fix | กระทบผลวิจัย? |
|---|---|---|---|---|
| 2026-07-26 | Neo4j default port `7474/7687` เปิดไม่ได้ | มี container อื่น (`thaigraphragbenchmark…neo4j`, `thai-legal-neo4j`) จองพอร์ต Neo4j default + รอง (7475/7688) ไปแล้ว | ตั้ง host port เป็น 7476/7689 (Streamlit 8501) ใน `.env` + `docker-compose.yml`; ในคอนเทนเนอร์ยังใช้ 7474/7687 ตามปกติ | ไม่ |

**Known-risk checklist (เฝ้าระวัง):**
- Timestamp/timezone ของ D1–D3 ไม่ตรงกัน → lag_hours เพี้ยน.
- CRS ของ shapefile ไม่ตรง → point-in-polygon จับจังหวัดผิด (บังคับ reproject เป็น EPSG เดียว).
- STAC/CKAN pagination ทำข้อมูลขาด.
- Reservoir ไม่มี spillway_level → OVERFLOWS_TO threshold ผิด.

---

## 🧾 Research Conclusions (ข้อสรุปงานวิจัย)

> เขียนหลัง eval เสร็จ อ้างตัวเลขจาก Results เท่านั้น.

- **H1 (traceability):** _สรุป — causal-graphrag traceable กว่า vector-rag กี่ %_ …
- **H2 (ทน hop):** _F1 ของกราฟลดลงช้ากว่า vector เมื่อ chain ยาวขึ้นจริงหรือไม่_ …
- **causal vs relational hop:** _causal hop ยากขึ้นในอัตราเดียวกับ entity-relation hop หรือไม่_ …
- **Limitations:** _ข้อจำกัดข้อมูล real-time, ความครบของ flood extent, จำนวนเหตุการณ์_ …
- **ต่อยอด:** early-warning system, dashboard ความเสี่ยงสะสม (climate-resilience / NECTEC).

---

## 💡 Aha Moments

> ช่วงที่ "อ๋อ!" — insight ที่ไม่คาดคิดระหว่างทำ. บันทึกสั้น ๆ แต่บันทึกทุกอัน.

| วันที่ | Aha | ทำไมสำคัญ |
|---|---|---|
| 2026-07-26 | ยก stack ทั้งชุด (Neo4j + app/UI) ด้วย `docker compose up` ครั้งเดียว โดย `app` รอ Neo4j `service_healthy` ก่อน | ลด setup เหลือคำสั่งเดียว, ไม่ต้อง pip/streamlit บนเครื่อง host, ทำซ้ำได้ทุกเครื่อง |
| 2026-07-26 | บังคับ `Evidence` เป็น dataclass ที่มี `.is_complete` ตั้งแต่ contract → `RetrieverAnswer.is_traceable` คำนวณ traceability ได้ฟรีทั้ง 3 ระบบ | H1 (traceability) วัดได้จากโครง contract เดียว ไม่ต้องเขียน logic ซ้ำต่อ retriever |

---

## 🚀 Quickstart

```bash
# 1) env (ตั้งพอร์ต + API keys; พอร์ต default เลี่ยงชนแล้ว)
cp .env.example .env

# 2) ยกทั้ง stack (Neo4j + app/UI) ด้วยคำสั่งเดียว — app รอ Neo4j healthy เอง
docker compose up -d --build
#    Neo4j Browser → http://localhost:7476   (bolt://localhost:7689)
#    Streamlit UI  → http://localhost:8501
```

รัน pipeline (จากในคอนเทนเนอร์ app หรือ venv บนเครื่องก็ได้):

```bash
python -m src.ingest.run           # D1–D4 → nodes/edges (+evidence)   [เฟส 1]
python -m src.geo.basin_to_province # ลุ่มน้ำ→จังหวัด → INUNDATES        [เฟส 2]
python -m src.graph.load            # โหลดเข้า Neo4j                      [เฟส 3]
python -m src.eval.build_eval_set   # คำถาม + GISTDA gold + hop tag      [เฟส 5]
python -m src.eval.f1_by_hop        # → Results                          [เฟส 5]
```

รัน test: `pytest`  ·  แก้โค้ดใน `src/` `ui/` แล้ว Streamlit reload อัตโนมัติ (mount ไว้ใน compose).

เริ่มงานจริงใน Claude Code: เปิด `KICKOFF.md` แล้ว copy prompt ไปวาง.
