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

### 🖥️ หน้าจอทั้งหมด / UI windows tour

เดินครบทุกหน้าต่างของ Test UI (`http://localhost:8501`) — ข้อมูลด้านล่างจับจากหน้าจริง
(คำถามตัวอย่าง: *"ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วมในเหตุการณ์ลุ่มเจ้าพระยาปี 2565?"*).

#### ① Layout ทั้งหน้า
```
┌──────────────┬──────────────────────────────────────────────────────────────┐
│  SIDEBAR     │  🌊 ทำไมจังหวัดนี้ถึงน้ำท่วม?                                  │
│  ⚙️ ตั้งค่า   │  คำถาม: ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม…ปี 2565?                 │
│              ├───────────────┬───────────────┬──────────────────────────────┤
│ • เลือกจังหวัด│ causal-graphrag│ entity-graphrag│ vector-rag                   │  ② เทียบ 3 ระบบ
│ • Neo4j uri  │  hop4 F1 1.00 ✓│ hop3 F1 0.75 ✗ │ hop0 F1 0.25 ✗               │
│ • gold set   ├───────────────┴───────────────┴──────────────────────────────┤
│              │  🔗 Causal chain viewer        │  🧾 Evidence panel            │  ③ chain + ④ evidence
│              ├───────────────────────────────┴──────────────────────────────┤
│              │  🗺️ Overlay flood extent (GISTDA) 🔵 จริง · 🔴 ที่ทำนาย        │  ⑤ แผนที่
└──────────────┴──────────────────────────────────────────────────────────────┘
```

#### ② หน้าต่างเทียบ 3 ระบบ side-by-side (ตัวชี้วัดสด hop / F1 / traceability)
```
┌─ causal-graphrag ─────────┐ ┌─ entity-graphrag ─────────┐ ┌─ vector-rag ──────────────┐
│ ของเรา—เดินเหตุ-ผล+evidence│ │ baseline—ไม่สนทิศ/หลักฐาน  │ │ baseline—ค้นข่าวด้วย vector│
│  hop:4   F1:1.00  trace:✓ │ │  hop:3   F1:0.75  trace:✗ │ │  hop:0   F1:0.25  trace:✗ │
│  ⏱686ms · ทำนาย 6 จังหวัด │ │  ⏱348ms · ทำนาย 10 จังหวัด│ │  ⏱5ms · ทำนาย 2 จังหวัด   │
│ ✅ ถูก: ครบ 6 จังหวัด      │ │ ✅ ถูก: 6                  │ │ ✅ ถูก: Nakhon Sawan       │
│ (ไม่มีเกิน/ตกหล่น)         │ │ ❌ เกิน: Bangkok, Nontha-  │ │ ❌ เกิน: Bangkok           │
│                           │ │    buri, Phitsanulok, Tak │ │ ⚠️ ตกหล่น: อีก 5 จังหวัด   │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```
> แต่ละคอลัมน์ลงสีจังหวัด **ถูก(∈gold)/เกิน(∉gold)/ตกหล่น** เทียบ ground truth ให้เห็นทันที.

#### ③ Causal chain viewer (เฉพาะ causal-graphrag — chain มาจาก Cypher เท่านั้น)
```
เขื่อนภูมิพล ─▶ ปิงท้ายเขื่อนภูมิพล ─▶ ปากน้ำโพ ─▶ เจ้าพระยาตอนบน ─▶ Nakhon Sawan
(Bhumibol)                         (Confluence)   (ปากน้ำโพ–ชัยนาท)
              ความยาวสายเหตุ-ผล = 4-hop (ข้ามลุ่มน้ำผ่านจุดบรรจบ)
```

#### ④ Evidence panel (คลิก expander เห็น source record → พิสูจน์ traceability / H1)
```
▸ ✅ evidence #1: D2/thaiwater dam_daily      station_id=RES-BHUMIBOL  ts=2022-10-10
▸ ✅ evidence #2: D1/data.go.th river gauge   station_id=RR-PING       ts=2022-10-10
▸ ✅ evidence #3: D1/data.go.th river gauge   station_id=CONF-PAKNAMPHO ts=2022-10-10
▸ ✅ evidence #4: D4/basin+province PIP + D3/GISTDA extent  station_id=RR-CP-UPPER
```

#### ⑤ แผนที่ overlay flood extent (GISTDA)
```
🔵 พื้นที่น้ำท่วมจริง (GISTDA D3)      🔴 จังหวัดที่ causal-graphrag ทำนายว่าท่วม
   → เคสนี้ 🔴 ทับ 🔵 พอดีทั้ง 6 จังหวัด (F1 = 1.00)   [pydeck GeoJsonLayer]
```

#### ⑥ Neo4j Browser (ดูกราฟดิบ) — `http://localhost:7476`  (user `neo4j` / pass `floodgraph123`)
```
ลองรัน Cypher นับ hop:
  MATCH p=(:Reservoir {active:true})-[:FEEDS|OVERFLOWS_TO|FLOWS_TO|INUNDATES*2..4]
          ->(:Province) RETURN p
→ เห็นเส้นทาง 2-hop (เขื่อนเจ้าพระยา→ลุ่มล่าง) และ 4-hop (ภูมิพล/สิริกิติ์→ปากน้ำโพ→…)
```

📄 ผลจริงเต็ม ๆ ของ ①–⑤: [docs/ui-sample-output.md](docs/ui-sample-output.md)

---

## 🔗 System — All Links

### แหล่งข้อมูล / Data sources
> สถานะ endpoint ยืนยันเมื่อ **2026-07-26** (ดู `data/processed/provenance.json` ที่ ingest เขียน).

| Source | Link | สถานะ (2026-07-26) | ใช้ทำอะไร |
|---|---|---|---|
| data.go.th CKAN | `https://data.go.th/api/3/action/package_search` | ✅ **200** (พบ 12 dataset) | ค้น/ดึงระดับน้ำโทรมาตร (D1) |
| thaiwater dam_daily | `https://www.thaiwater.net/api/v1/thaiwater/public/dam_daily` | ⚠️ 200 แต่ body ไม่ใช่ JSON สะอาด → fixture | ระดับน้ำ/ระบายเขื่อน (D2) |
| thaiwater (path เดิม) | `https://api.thaiwater.net/v1/...` | ❌ **404** (ย้าย host) | — |
| GISTDA flood portal | https://disaster.gistda.or.th/flood/ | ℹ️ เว็บ 200 | flood extent maps (D3) |
| GISTDA STAC API | `https://disaster.gistda.or.th/api/stac/search` | ❌ **ต่อไม่ติด (000)** → fixture fallback | flood extent = ground truth (D3) |
| ขอบเขตลุ่มน้ำ/จังหวัด | data.go.th (ค้น "ลุ่มน้ำ", "ขอบเขตจังหวัด") | ⚙️ fixture geojson (เฟส 2 PIP) | shapefile/GeoJSON (D4) |

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
| `.claude/skills/causal-graphrag/SKILL.md` | สร้าง/query causal graph + F1-by-hop |
| `.claude/skills/geo-basin-to-province/SKILL.md` | point-in-polygon ลุ่มน้ำ→จังหวัด |
| `docker-compose.yml` · `Dockerfile` | ยก Neo4j + app/UI ครั้งเดียว |
| `.env.example` | ตัวแปรแวดล้อม + API keys + พอร์ต |
| `src/config.py` | จุดเดียวอ่าน port/creds/endpoints |
| `src/ingest/{fixtures,connectors,run}.py` | D1–D4 + fixture ลุ่มเจ้าพระยา 2565 (+evidence) |
| `src/geo/basin_to_province.py` | GeoPandas PIP → INUNDATES + gold |
| `src/graph/{queries,load,client}.py` | schema + variable-length hop cypher + loader |
| `src/rag/{base,causal_graphrag,entity_graphrag,vector_rag,registry}.py` | 3 retrievers อินเทอร์เฟซเดียว |
| `src/eval/{build_eval_set,f1_by_hop,run}.py` | eval set + F1-by-hop + traceability |
| `ui/app.py` | Streamlit UI เทียบ 3 ระบบ |
| `data/processed/*.json,*.geojson` | fixture + ผล eval (`eval_results.json`) |

> ⚠️ ยืนยัน endpoint ที่แน่นอนของ STAC/CKAN ตอน ingest จริง (โครงสร้าง API อาจเปลี่ยน) แล้วอัปเดตตารางนี้.

---

## 🖥️ Test UI (หน้าทดสอบใช้งาน)

**Streamlit** `ui/app.py` — มากับ stack (`docker compose up`) ที่ http://localhost:8501
(หรือรันเอง: `streamlit run ui/app.py`).

📄 **ตัวอย่างผลจริงจากหน้าจอ:** [docs/ui-sample-output.md](docs/ui-sample-output.md)
(จับจากหน้าจริง — เปิด http://localhost:8501 แล้ว save เป็น `docs/ui-why-flood.png` ได้)

องค์ประกอบหน้าจอ (ทำแล้ว):
- **เลือกจังหวัด** (จากจังหวัดที่ท่วมจริงตาม GISTDA) — คำถามประกอบอัตโนมัติ.
- **แผง 3 คอลัมน์เทียบกัน:** `causal-graphrag` / `entity-graphrag` / `vector-rag` — คำตอบ + ตัวชี้วัดสด (**hop / F1 / traceability ✓✗** + latency) + แยกสีจังหวัด ถูก/เกิน/ตกหล่น เทียบ gold.
- **Causal chain viewer:** แสดง path เขื่อน→ลำน้ำ→(จุดบรรจบ)→จังหวัด พร้อม hop count (2-hop เขื่อนเดียว / 4-hop ข้ามลุ่มน้ำ).
- **Evidence panel:** คลิก expander เห็น source record (station_id, timestamp, dataset) → พิสูจน์ traceability (H1).
- **แผนที่ (pydeck):** overlay flood extent GISTDA (🔵) เทียบจังหวัดที่ causal ทำนาย (🔴).

---

## 📊 Results (ผลลัพธ์)

> ตัวเลขด้านล่าง **คำนวณจริง** จาก `python -m src.eval.run` (ไม่ hardcode) บน dataset
> เหตุการณ์ลุ่มเจ้าพระยา 2565 (**fixture** — GISTDA STAC ต่อไม่ติด, ดู Bugs). รันซ้ำได้ทุกครั้ง;
> ผลเขียนลง `data/processed/eval_results.json` + `results_table.md`.
> eval set = 6 คำถาม (2-hop: 4 จังหวัด, 4-hop: 2 จังหวัด), gold = flood extent 6 จังหวัด.

### F1 by causal-hop length (on fixture: Chao Phraya 2022)
| System | F1 @ 2-hop (เขื่อนเดียว) | F1 @ 4-hop (ข้ามลุ่มน้ำ) | ΔF1 (2→4) | Traceability | Latency (ms) |
|---|---|---|---|---|---|
| **causal-graphrag (ours)** | **1.000** | **1.000** | **0.000** | **100%** | 10.0 |
| entity-graphrag | 0.857 | 0.750 | 0.107 | 0% | 13.1 |
| vector-rag | 0.250 | 0.250 | 0.000 | 0% | 1.1 |

**อ่านผล:**
- **causal-graphrag** ทำนายตรง gold ทั้งหมด (F1=1.0) เพราะกรองด้วย threshold ระดับน้ำ + เดินตามทิศการไหลจริง → ตัด false positive (ต้นน้ำที่ไม่ท่วม) ออกหมด, และ **ไม่ลดลงเมื่อ chain ยาวขึ้น** (ΔF1=0).
- **entity-graphrag** (undirected, ไม่กรอง) เก็บจังหวัดเกินจริง → precision ตก, และ **ยิ่ง chain ยาว (4-hop) ยิ่งดูดจังหวัดต้นน้ำผิด ๆ เข้ามา** (Tak/Phitsanulok) → F1 ลดจาก 0.857 → 0.750.
- **vector-rag** ได้เฉพาะจังหวัดที่ข่าวรายงาน + ติด "กรุงเทพ" (ข่าวเด่น) เป็น false positive ทุกคำถาม → F1 ต่ำคงที่ 0.25.

### Traceability (% คำตอบที่ชี้ evidence กลับ source ได้)
| System | Traceability % | ทำไม |
|---|---|---|
| causal-graphrag | **100%** | ทุก edge บน chain มี `evidence` (station_id+timestamp+dataset) ครบ |
| entity-graphrag | 0% | เดินกราฟโดยไม่อ่าน evidence |
| vector-rag | 0% | ไม่มีโครงสร้าง evidence (ชี้ได้แค่ข่าว ไม่ใช่ source record) |

### เหตุการณ์ที่ทดสอบ / Test events
| Event | ลุ่มน้ำ | ช่วงเวลา | #จังหวัด gold | ground truth |
|---|---|---|---|---|
| chao_phraya_2022 | เจ้าพระยา (Ping+Nan→ปากน้ำโพ→เจ้าพระยา) | 2022-09-25 → 10-15 | 6 | GISTDA D3 *(fixture — STAC ต่อไม่ติด)* |

---

## 🐞 Bugs & Fixes (บั๊คที่เจอ)

> บันทึกทันทีที่เจอ — วันที่ / อาการ / สาเหตุ / วิธีแก้ / กระทบข้อสรุปไหม.

| วันที่ | Bug (อาการ) | Root cause | Fix | กระทบผลวิจัย? |
|---|---|---|---|---|
| 2026-07-26 | Neo4j default port `7474/7687` เปิดไม่ได้ | มี container อื่น (`thaigraphragbenchmark…neo4j`, `thai-legal-neo4j`) จองพอร์ต Neo4j default + รอง (7475/7688) ไปแล้ว | ตั้ง host port เป็น 7476/7689 (Streamlit 8501) ใน `.env` + `docker-compose.yml`; ในคอนเทนเนอร์ยังใช้ 7474/7687 ตามปกติ | ไม่ |
| 2026-07-26 | **Neo4j ปฏิเสธ property เป็น map** ตอน set `e.evidence = {…}` (ตาม pattern ใน skill) | Neo4j property เป็น primitive/array เท่านั้น — nested map ใช้ไม่ได้ | เก็บ `evidence` เป็น **JSON string** พร็อพเดียว, retriever `json.loads` กลับ; `evidence IS NULL` ยังตรวจ traceability ได้ | ไม่ (traceability ยังครบ) |
| 2026-07-26 | thaiwater `api.thaiwater.net/v1/...` → **404** | path/host API เปลี่ยน | ยืนยัน path ใหม่ `www.thaiwater.net/api/v1/thaiwater/public/dam_daily` → 200 (แต่ body ไม่ใช่ JSON สะอาด) → ใช้ fixture D2 | ไม่ (fixture) |
| 2026-07-26 | **GISTDA STAC ต่อไม่ติด** (`disaster.gistda.or.th/api/stac` → connection fail 000) | ไม่มี public STAC endpoint ตามที่คาด / อาจเป็น internal | fallback เป็น fixture flood extent (D3) เป็น ground truth ชั่วคราว, log ไว้; connector ยังลองยิงจริงทุกครั้ง | **ใช่ (บางส่วน)** — gold เป็น fixture ไม่ใช่ GISTDA จริง → ผลเป็น "on fixture" |
| 2026-07-26 | รัน script บน Windows แล้ว `UnicodeEncodeError` (cp874) | คอนโซลไทยเข้ารหัสอักขระ box-drawing/emoji ไม่ได้ | รัน host ด้วย `PYTHONUTF8=1`; ใน Docker (Linux) ไม่มีปัญหา | ไม่ |
| 2026-07-26 | point-in-polygon จับจังหวัดผิด/ซ้ำ + gold เกิน | polygon จังหวัด fixture (box ±0.18°) **ทับกัน** (นนทบุรี/กรุงเทพห่าง ~0.11°) | ย่อ box เป็น ±0.05° ไม่ให้ทับ → PIP ได้จังหวัดเดียวชัด (ตรงกับ anti-pattern "sliver" ใน skill) | ไม่ |

**Known-risk checklist (เฝ้าระวัง):**
- Timestamp/timezone ของ D1–D3 ไม่ตรงกัน → lag_hours เพี้ยน.
- CRS ของ shapefile ไม่ตรง → point-in-polygon จับจังหวัดผิด (บังคับ reproject เป็น EPSG เดียว).
- STAC/CKAN pagination ทำข้อมูลขาด.
- Reservoir ไม่มี spillway_level → OVERFLOWS_TO threshold ผิด.

---

## 🧾 Research Conclusions (ข้อสรุปงานวิจัย)

> อ้างตัวเลขจาก Results เท่านั้น. **ข้อควรระวัง:** ผลปัจจุบันมาจาก dataset **fixture**
> (ลุ่มเจ้าพระยา 2565) เพราะ GISTDA STAC ต่อไม่ติด → ถือเป็น *ผลสาธิตเชิงวิธี* (methodology
> demonstration) ที่รันซ้ำได้ ยังไม่ใช่ข้อสรุปเชิงประจักษ์บนข้อมูลจริงเต็มรูป.

- **H1 (traceability): สนับสนุน.** causal-graphrag = **100%** traceable (ทุก edge มี evidence ครบ) เทียบกับ entity-graphrag และ vector-rag = **0%**. การบังคับ `evidence` บนทุก edge ทำให้ traceability กลายเป็นคุณสมบัติที่ตรวจได้ฟรี.
- **H2 (ทน hop): สนับสนุน.** F1 ของ causal-graphrag **คงที่ 1.000 ทั้ง 2-hop และ 4-hop (ΔF1=0)** ขณะที่ entity-graphrag ลดลง 0.857→0.750 (ΔF1=0.107) เมื่อ chain ยาวขึ้น. กราฟที่เดินตามสายเหตุ-ผลจริง + กรอง threshold ทน hop ได้ดีกว่า baseline relational ชัดเจน.
- **causal vs relational hop:** causal hop **ไม่ได้** ยากขึ้นแบบเดียวกับ entity-relation hop — ตรงกันข้าม การใส่ทิศการไหล + threshold ทำให้ 4-hop (ข้ามลุ่มน้ำผ่านปากน้ำโพ) ยังแม่นเท่า 2-hop, ต่างจาก entity ที่ 4-hop ดูดจังหวัดต้นน้ำผิดเข้ามา. → causal เป็นมิติที่ *ต่าง* จาก relational hop ไม่ใช่แค่ยากขึ้นตามระยะ.
- **Limitations:**
  - ground truth เป็น **fixture** ไม่ใช่ GISTDA flood extent จริง (STAC ต่อไม่ติด) → ตัวเลขเป็นเชิงวิธี.
  - dataset เล็ก (1 เหตุการณ์, 6 จังหวัด gold, 10 จังหวัดในกราฟ) → ยังไม่ generalize.
  - threshold/ระดับน้ำเป็นค่าที่ตั้งให้ coherent กับเหตุการณ์ ไม่ได้ดึงจาก telemetry จริงรายชั่วโมง.
  - vector corpus เล็ก (8 ข่าว) → ตัวเลข vector ไวต่อ coverage ของข่าว.
- **ต่อยอด:** เปลี่ยน fixture → ข้อมูลจริงเมื่อได้ STAC/telemetry, เพิ่มหลายเหตุการณ์/หลายลุ่มน้ำ, ต่อยอด early-warning + dashboard ความเสี่ยงสะสม (climate-resilience / NECTEC).

---

## 💡 Aha Moments

> ช่วงที่ "อ๋อ!" — insight ที่ไม่คาดคิดระหว่างทำ. บันทึกสั้น ๆ แต่บันทึกทุกอัน.

| วันที่ | Aha | ทำไมสำคัญ |
|---|---|---|
| 2026-07-26 | ยก stack ทั้งชุด (Neo4j + app/UI) ด้วย `docker compose up` ครั้งเดียว โดย `app` รอ Neo4j `service_healthy` ก่อน | ลด setup เหลือคำสั่งเดียว, ไม่ต้อง pip/streamlit บนเครื่อง host, ทำซ้ำได้ทุกเครื่อง |
| 2026-07-26 | บังคับ `Evidence` เป็น dataclass ที่มี `.is_complete` ตั้งแต่ contract → `RetrieverAnswer.is_traceable` คำนวณ traceability ได้ฟรีทั้ง 3 ระบบ | H1 (traceability) วัดได้จากโครง contract เดียว ไม่ต้องเขียน logic ซ้ำต่อ retriever |
| 2026-07-26 | **สิ่งที่แยก causal ออกจาก entity ไม่ใช่ "เดินกราฟ" แต่คือ (1) ทิศการไหล + (2) กรอง threshold ด้วยระดับน้ำ**. พอใส่ 2 อย่างนี้ F1 กระโดดจาก 0.75–0.86 → 1.0 | ยืนยันว่า "causal" มีค่าเพราะ *ใช้ evidence เชิงกายภาพตัดสิน* ไม่ใช่แค่ topology ของกราฟ |
| 2026-07-26 | **entity-graphrag ยิ่ง chain ยาวยิ่งแย่** (0.857→0.750) เพราะ undirected traversal จากจังหวัดปลายน้ำ 4-hop ดูดจังหวัด*ต้นน้ำ*ที่ไม่ท่วมเข้ามา | เป็นหลักฐานตรงของ H2: กราฟที่ไม่คุมทิศ/หลักฐาน *ไม่ได้* ทน hop เหมือน causal |
| 2026-07-26 | vector-rag ติด "กรุงเทพ" เป็น false positive ทุกคำถาม เพราะข่าว "ทำไมกรุงเทพน้ำท่วมทุกปี" เด่นใน corpus | โชว์จุดอ่อน vector: ตอบตาม *ความถี่ข่าว* ไม่ใช่ *สายเหตุ-ผล* → ปลายน้ำจริงที่ข่าวไม่รายงานหลุดหมด |
| 2026-07-26 | จุดที่ทำให้ 2-hop/4-hop ต่างกันคือ **จุดบรรจบปากน้ำโพ** (Confluence) — 4-hop = ต้องข้ามลุ่มน้ำผ่าน node นี้ | ทำให้ "causal hop" เป็นมิติใหม่จริง (ข้ามลุ่มน้ำ) ไม่ใช่แค่ระยะทางกราฟ |

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

รัน pipeline (บน Windows host เติม `PYTHONUTF8=1` กันปัญหา cp874; ใน Docker/Linux ไม่ต้อง):

```bash
python -m src.ingest.run            # D1–D4 probe + fixture (+evidence)  [เฟส 1]
python -m src.geo.basin_to_province # PIP ลุ่มน้ำ→จังหวัด → INUNDATES     [เฟส 2]
python -m src.graph.load            # โหลดเข้า Neo4j                       [เฟส 3]
python -m src.eval.run              # 3 ระบบ → F1-by-hop + traceability   [เฟส 5]
```

รัน test ทั้งหมด (22 ผ่าน; integration ข้ามอัตโนมัติถ้าไม่มี Neo4j):

```bash
pytest
```

แก้โค้ดใน `src/` `ui/` แล้ว Streamlit reload อัตโนมัติ (mount ไว้ใน compose).
