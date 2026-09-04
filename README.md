# Thai Flood Causal-Chain GraphRAG 🌊

**"ทำไมจังหวัดนี้ถึงน้ำท่วม?" / "Why did this province flood?"**

ระบบตอบคำถามน้ำท่วมโดยเดินกราฟตาม *สายเหตุ-ผลจริง* (ฝน → เขื่อน → แม่น้ำ → จังหวัด) แล้ววัดว่าให้คำอธิบายที่ **ตรวจสอบย้อนกลับได้ (traceable)** ดีกว่าการค้นข่าวด้วย vector search แค่ไหน — วัดด้วย **F1 แยกตามความยาว causal chain**.

> A flood-explanation system that walks a *real causal chain* and measures how much more verifiable its answers are than vector search over news, scored by **F1 per causal-hop length**.

📘 **เอกสาร:** [เอกสารการพัฒนาระบบฉบับสมบูรณ์ (System overview + ทุกฟังก์ชัน end-to-end)](docs/SYSTEM_DEVELOPMENT.md) · [เล่มโครงงาน (5 บท)](docs/PROJECT_REPORT.md) · [methodology (freeze)](eval/METHODOLOGY.md) · [references](docs/REFERENCES.md) · [history + bug log](docs/HISTORY.md)

---

## 📑 สารบัญ / Table of Contents
1. [System Tour + เจาะทีละก้อน](#️-system-tour)
2. [UI — 3 หน้า (User / Research / Warning)](#️-หน้าจอระบบ--ui--3-หน้าแยกกันชัดเจน)
3. [System — All Links](#-system--all-links)
4. [ผลการทดลอง / Experiment Report](#-รายงานผลการทดลอง-experiment-report)
5. [ข้อจำกัด + Integrity](#️-ข้อจำกัดปัจจุบัน--integrity-current-limitations)
6. [Research Conclusions](#-research-conclusions-ข้อสรุปงานวิจัย)
7. [Aha Moments](#-aha-moments)
8. [Quickstart](#-quickstart)

---

## 🗺️ System Tour

ไล่จากข้อมูล**จริง** → กราฟเหตุผล (มี path ฝน→น้ำท่า) → 3 ระบบตอบคำถาม → วัดผลกับ GISTDA จริง → หน้าเว็บ.

> 📈 **สถานะปัจจุบัน:** universe ลุ่มเจ้าพระยา **23 จังหวัด (8 ลุ่มน้ำสาขา)** · **5 เหตุการณ์** (เจ้าพระยา 2565/2564/2566/2567 + โขง/อีสาน live) · **3 หน้า UI** (`/` user · `/lab` research · `/warn` warning).
> **ข้อมูลจริง:** ground truth ✅GISTDA satellite · geometry ✅GADM4.1 · dam specs ✅EGAT/RID · **reach.overflow ✅RID SWOC gauge (อิสระจาก gold)** · vector corpus ✅194 ข่าว. โครง node/edge = hand-built จาก topology จริง **+ validate ด้วย DEM (Copernicus/pysheds)**.
> **ฟีเจอร์:** คำอธิบาย LLM (grounded) · ablation · negative-control · McNemar + bootstrap · lead-time · risk layer · blind test. freeze: [`eval/METHODOLOGY.md`](eval/METHODOLOGY.md) · refs: [`docs/REFERENCES.md`](docs/REFERENCES.md).

รายละเอียดแต่ละขั้นตอน (input → process → output → ทำไมเชื่อถือได้) ดูที่ **[เจาะทีละก้อน](#-system-overview--ภาพรวม--เจาะทีละก้อน)** ด้านล่าง.

### 🧭 System Overview — ภาพรวม + เจาะทีละก้อน

ภาพรวมทั้งระบบในภาษาเล่าเรื่องของโปรเจกต์ (บน = **สายเหตุ-ผลที่เราเดินตาม**, ล่าง = **ระบบที่สร้างมาวัดมัน**):

![System Overview](docs/system_overview.svg)

> 📖 เวอร์ชันเล่าเรื่องเต็ม (สำหรับเล่าให้อาจารย์/นำเสนอ): [`docs/STORY.md`](docs/STORY.md)

**เจาะเข้าไปทีละก้อน** — แต่ละก้อนบอก *เอาอะไรเข้า → ทำอะไร → ได้อะไรออก → ทำไมเชื่อถือได้*:

<details open>
<summary><b>① Ingestion &amp; Graph Build</b> — เปลี่ยนข้อมูลจริงเป็นกราฟเหตุ-ผลใน Neo4j</summary>

![① Ingestion & Graph Build](docs/blocks/block1_ingest.svg)
</details>

<details>
<summary><b>② Geo Mapping</b> — GeoPandas จับลำน้ำ→จังหวัด + วางเฉลยจากภาพน้ำท่วม</summary>

![② Geo Mapping](docs/blocks/block2_geo.svg)
</details>

<details>
<summary><b>③ 3 Retrievers ★</b> — หัวใจงาน: causal vs entity vs vector เดินคนละแบบ</summary>

![③ 3 Retrievers](docs/blocks/block3_retrievers.svg)
</details>

<details>
<summary><b>④ Evaluation</b> — ให้คะแนนกับเฉลย GISTDA + ยืนยันทางสถิติ (รายงานตรง)</summary>

![④ Evaluation](docs/blocks/block4_eval.svg)
</details>

<details>
<summary><b>⑤ DEM Validation</b> — ตรวจว่าน้ำไหลตามที่กราฟบอกจริง (ข้อมูลฟิสิกส์อิสระ)</summary>

![⑤ DEM Validation](docs/blocks/block5_dem.svg)
</details>

<details>
<summary><b>⑥ Extension</b> — พยากรณ์/ความเสี่ยง + "ทำไมอาจไม่เกิด" (ส่วนเสริม)</summary>

![⑥ Extension](docs/blocks/block6_extension.svg)
</details>

#### 🌐 English version

▶ **[Open the interactive walkthrough](docs/system_walkthrough.html)** — one page, click through the overview + all 6 blocks (open it locally / via GitHub Pages).

![System Overview (EN)](docs/system_overview_en.svg)

<details>
<summary><b>① Ingestion &amp; Graph Build</b> — turn real data into a causal graph in Neo4j</summary>

![① Ingestion & Graph Build](docs/blocks/block1_ingest_en.svg)
</details>

<details>
<summary><b>② Geo Mapping</b> — GeoPandas maps reach→province + lays down the gold key</summary>

![② Geo Mapping](docs/blocks/block2_geo_en.svg)
</details>

<details>
<summary><b>③ 3 Retrievers ★</b> — the core: causal vs entity vs vector</summary>

![③ 3 Retrievers](docs/blocks/block3_retrievers_en.svg)
</details>

<details>
<summary><b>④ Evaluation</b> — score vs GISTDA + statistical confirmation (reported straight)</summary>

![④ Evaluation](docs/blocks/block4_eval_en.svg)
</details>

<details>
<summary><b>⑤ DEM Validation</b> — independent physics check of flow direction</summary>

![⑤ DEM Validation](docs/blocks/block5_dem_en.svg)
</details>

<details>
<summary><b>⑥ Extension</b> — forecasting/risk add-on + "why it might not happen"</summary>

![⑥ Extension](docs/blocks/block6_extension_en.svg)
</details>

### 🕸️ โครงสร้างกราฟ (Neo4j schema) + ตัวอย่าง multi-hop

โครงสร้าง label/relationship ของ causal graph — เทียบเท่าผลของ `CALL db.schema.visualization()` ใน Neo4j Browser (**5 labels · 5 relationship types**, ทิศลูกศร = ทิศการไหลของน้ำ):

![Neo4j schema](docs/neo4j_schema.svg)

> ดูของจริงบน **Neo4j Browser** (`http://localhost:7476`): รัน `CALL db.schema.visualization()` เพื่อดู schema นี้สด ๆ (หรือดูเส้นทางจริงด้วย query ใน [Extension `/warn`](#️-หน้าจอระบบ--ui--3-หน้าแยกกันชัดเจน) ด้านล่าง).

**การให้เหตุผลผ่านหลาย hop (multi-hop reasoning)** — เดินตามสายเหตุ-ผลทีละ hop สะสม `lag` + `evidence` จนถึงจังหวัด (2-hop = ในลุ่มน้ำสาขาเดียว · 4-hop = ข้ามลุ่มน้ำผ่านจุดบรรจบปากน้ำโพ):

![Multi-hop reasoning](docs/multihop_reasoning.svg)

---
### 🖥️ หน้าจอระบบ / UI — 3 หน้าแยกกันชัดเจน

FastAPI ([`src/web/server.py`](src/web/server.py)) เสิร์ฟ 3 หน้า (Tailwind + MapLibre GL + Chart.js) ที่ **http://localhost:8501** — API keys (GISTDA) อยู่ **ฝั่ง server** (proxy) ไม่หลุดไป client. ออกแบบเอง 2026-09-04 (ฟอนต์ Trirong + IBM Plex Sans Thai/Mono, ลาย contour แผนที่ — ไม่ใช้ template สำเร็จรูป):

---
#### 🅰️ หน้า USER (`/`) — "รายงานภาคสนาม" (โทนกระดาษอุ่น) — สำหรับประชาชน/ผู้ใช้ทั่วไป

![หน้า user — field report](docs/ui-friendly.png)

เลือกจังหวัด → **การ์ดรายงาน**อธิบายเหตุน้ำท่วมด้วยภาษาไทยธรรมชาติ (คำอธิบาย LLM grounded, drop-cap) + ป้ายสถานะ (GISTDA ท่วมจริง · อธิบายได้ · เตือนล่วงหน้า · hop) + **สายเหตุ-ผลแบบ stepped** + หลักฐานตรวจย้อนได้ + **แผนที่ GISTDA จริง** (🔵ท่วมจริง 🟢ทำนายถูก 🔴เกิน) + น้ำท่วม real-time + เทียบ 3 ระบบย่อ. เข้าใจง่าย ใช้งานได้ทุกฟังก์ชัน.

---
#### 🅱️ หน้า BACKEND (`/lab`) — "Research Console" (โทนเข้ม เครื่องมือวัด) — ดูผลการทดลองละเอียด

![หน้า research console — ผลการทดลองครบ](docs/ui-lab.png)

**แดชบอร์ดวิจัยครบทุก metric อ่านทีละส่วนจากเมนูซ้าย (11 ส่วน):** สถานะข้อมูล · เส้นทาง F1 · KPI · ผลหลัก 3 ระบบ (+กราฟ F1-by-hop & ablation) · **นัยสำคัญ McNemar 4 เหตุการณ์ + bootstrap** · negative-control confusion · **discrimination (ได้เปรียบเมื่อไหร่)** · **lead-time skill (MAE/RMSE + POD/FAR/CSI)** · **topology 4 วิธี** · **blind test** · ทุกจังหวัด × 3 ระบบ. ดึงจาก `/api/report`.

---
#### 🧩 Extension (`/warn`) — พยากรณ์ & เตือนภัยล่วงหน้า

![หน้า extension — เตือนภัย + ที่มาของตัวเลข](docs/ui-warn.png)

กลับด้านกราฟเหตุ-ผลมา**ทำนายล่วงหน้า**: ตั้งว่าลุ่มน้ำใดล้น → เตือนจังหวัดปลายน้ำ พร้อม **โอกาสท่วม % (จาก precision จริง) · ระดับเสี่ยง (Hazard×Exposure×Vulnerability) · ช่วงเวลา · confidence · ประชากรเสี่ยง** เรียงตามความเสี่ยง. มีส่วน **"ที่มาของตัวเลข & ทำไมอาจไม่เกิด"** (ตามหลัก EFAS/NOAA/risk-index) — โปร่งใสว่าค่ามาจากอะไรและความไม่แน่นอนอยู่ตรงไหน.

**ตัวอย่าง NORU 2565:** นครสวรรค์ risk **สูงมาก** 94% → เพชรบูรณ์/พิษณุโลก **ด่วนมาก ~24h** → อยุธยา ~42h → กรุงเทพ-ปริมณฑล (ลำดับตรงกับ timeline 2554, ρ≈0.76). API: `/api/early-warning`.

> อีกหน้าต่างนอกแอป: **Neo4j Browser** `http://localhost:7476` (user `neo4j` / pass `floodgraph123`) —
> รัน `MATCH p=(src {active:true})-[:FEEDS|OVERFLOWS_TO|FLOWS_TO|RUNOFF_TO|INUNDATES*2..4]->(:Province) RETURN p`
> (src = เขื่อนที่ล้น *หรือ* สถานีฝน) เพื่อดูเส้นทาง 2-hop / 4-hop ดิบบนกราฟ.

📄 ผลตัวเลขเต็ม ๆ: [docs/ui-sample-output.md](docs/ui-sample-output.md)

---

## 🔗 System — All Links

### แหล่งข้อมูล / Data sources
> สถานะ endpoint ยืนยันเมื่อ **2026-07-26/27** (ดู `data/processed/provenance.json` ที่ ingest เขียน). ✅ = ใช้จริงในผลปัจจุบัน.

| Source | Link | สถานะ | ใช้ทำอะไร |
|---|---|---|---|
| data.go.th CKAN | `https://data.go.th/api/3/action/package_search` | ✅ **200** (พบ 12 dataset) | ค้น/ดึงระดับน้ำโทรมาตร (D1) |
| **GISTDA satellite flood — NORU 2565** | `.../2022/NORU2022/flood_area.html` (thaiwater) | ✅ **ใช้จริง** — พื้นที่ท่วมรายจังหวัด | **ground truth 2565** |
| **GISTDA satellite flood — Dianmu 2564** | `.../2021/DIANMU2021/flood_area.html` (thaiwater) | ✅ **ใช้จริง (Item 4)** — พื้นที่ท่วมรายจังหวัด | **ground truth 2564** |
| **GADM 4.1 (ขอบเขตจังหวัดจริง)** | `https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_THA_1.json` | ✅ **ใช้จริง** — polygon 77 จว. | geometry (D4) |
| **RID river-gauge bulletin (9 ต.ค. 65)** | `http://water.rid.go.th/flood/news/` | ✅ **ใช้จริง** — C.2/C.13/P.7A ความจุ+อัตราไหล | reach.overflow (2565) |
| **dam specs (EGAT/RID)** | ดู `data/processed/dam_specs.json` (มี source_url ต่อค่า) | ✅ **ใช้จริง** — spillway + สถานะปี 2565 | Reservoir active/spillway |
| thaiwater api/v1 | `www.thaiwater.net/api/v1/...` · `api.thaiwater.net/v1/...` | ❌ ไม่มี JSON API สาธารณะ (คืน HTML/404, เทสต์สด 2026-07-27) → **ใช้ `dam_specs.json` + RID gauge จริงแทน** | ✅ ข้อมูลได้ครบแล้ว |
| GISTDA STAC API | `https://disaster.gistda.or.th/api/stac/search` | ❌ **ต่อไม่ติด (000)** subdomain ถูกบล็อก → **ใช้ GISTDA satellite ผ่านหน้า NORU2022/DIANMU2021 แทน** (ข้อมูลตัวเดียวกัน) | ✅ ground truth ได้ครบแล้ว |
| Sentinel-1 SAR — **Copernicus (ไม่ต้องใช้บัตร)** | `dataspace.copernicus.eu` (openEO) | ⬜ optional cross-check — โค้ดพร้อมที่ [`copernicus_flood_extent.py`](src/ingest/copernicus_flood_extent.py) (สมัครฟรี ไม่ผูกบัตร) | ยืนยัน GISTDA ด้วยแหล่ง 2 |
| Sentinel-1 SAR — GEE (ทางเลือก) | earthengine.google.com | ⬜ ต้อง OAuth/บัญชี GCP — โค้ดพร้อมที่ [`sentinel1_flood_extent.py`](src/ingest/sentinel1_flood_extent.py) | เหมือนกัน (แต่ขอบัตร) |
| **GISTDA disaster API — flood (real-time)** | `api-gateway.gistda.or.th/api/2.0/resources/features/flood/{1day\|3days\|7days\|30days}` | ✅ **ใช้ได้จริง** (header `API-Key`) — คืน GeoJSON น้ำท่วมปัจจุบัน (Sentinel-1) | live flood (B2) — ดู [`gistda_flood_api.py`](src/ingest/gistda_flood_api.py) |
| **GISTDA sphere basemap** | `basemap.sphere.gistda.or.th/tiles/...` | ✅ **ใช้ได้จริง** (query `key=`) — เป็น basemap ใน UI | แผนที่พื้นหลัง |

> **สรุป 3 แถว ❌ = "ทางที่ปิด" ไม่ใช่ "ข้อมูลที่ขาด"** — ข้อมูลทุกอย่างที่ endpoint พวกนี้จะให้ ดึงมาครบแล้วจากประตูที่เปิดอยู่
> (RID gauge + GISTDA-via-thaiwater + dam_specs). ถ้าจะต่อยอดเป็น **real-time early-warning** ค่อยขอ API key จาก สสน./GISTDA โดยตรง (future feature).

### เครื่องมือ / Tooling
| Tool | Link |
|---|---|
| Neo4j (Docker) | http://localhost:7476 (Browser) · `bolt://localhost:7689` |
| Web UI (FastAPI) | http://localhost:8501 (`/` user · `/lab` research · `/warn` warning) |

> **พอร์ต host เลือกเลี่ยงการชนกับ container อื่นในเครื่องนี้** (สำรวจด้วย `docker ps` ตอนเฟส 0):
> Neo4j default `7474/7475/7687/7688` ถูกจองแล้ว → โปรเจกต์นี้ใช้ **HTTP 7476 · Bolt 7689 · FastAPI UI 8501**.
> ค่าเหล่านี้ตั้งใน `.env` (`NEO4J_HTTP_PORT` / `NEO4J_BOLT_PORT` / `STREAMLIT_PORT`) และ `docker-compose.yml` อ่านต่อ.
| GeoPandas (basin→province PIP) | https://geopandas.org |
| scikit-learn (TF-IDF vector baseline) | https://scikit-learn.org |
| pysheds (DEM flow-accumulation) | https://mattbartos.com/pysheds |

### ภายใน repo / Internal
| ไฟล์ | หน้าที่ |
|---|---|
| `.claude/skills/causal-graphrag/SKILL.md` | สร้าง/query causal graph + F1-by-hop |
| `.claude/skills/geo-basin-to-province/SKILL.md` | point-in-polygon ลุ่มน้ำ→จังหวัด |
| `docker-compose.yml` · `Dockerfile` | ยก Neo4j + app/UI ครั้งเดียว |
| `.env.example` | ตัวแปรแวดล้อม + API keys + พอร์ต |
| `src/config.py` | จุดเดียวอ่าน port/creds/endpoints |
| `src/ingest/{fixtures,connectors,run}.py` | สร้าง node/edge (+evidence); `EVENT_ID` เลือกเหตุการณ์ |
| `src/ingest/scrape_news.py` | scrape ข่าวจริง (Google News RSS) → corpus v2 |
| `src/ingest/copernicus_flood_extent.py` | Sentinel-1 flood mapping ผ่าน Copernicus (openEO, ไม่ต้องใช้บัตร) |
| `src/ingest/sentinel1_flood_extent.py` | Sentinel-1/GEE flood mapping (ทางเลือก, ต้องมี GEE account) |
| `src/geo/basin_to_province.py` | GeoPandas PIP (GADM) → INUNDATES + gold overlay |
| `src/graph/{queries,load,client}.py` | schema (มี `RUNOFF_TO`) + hop cypher + loader |
| `src/rag/{base,causal_graphrag,entity_graphrag,vector_rag,registry}.py` | 3 retrievers อินเทอร์เฟซเดียว |
| `src/eval/{build_eval_set,f1_by_hop,run}.py` | eval set + F1-by-hop + traceability |
| `src/eval/build_ui_data.py` | precompute ผล 3 ระบบทุกจังหวัด → `web/ui_data_{year}.json` |
| **`src/web/server.py`** | **FastAPI** — เสิร์ฟ UI + API + proxy GISTDA (keys ฝั่ง server) |
| **`web/index.html`** | **หน้า UI ใหม่** (Tailwind + MapLibre + Chart.js) |
| `src/ingest/gistda_flood_api.py` | ดึง flood จริง real-time จาก GISTDA gateway (data key) |
| **`data/processed/dam_specs.json`** | สเปกเขื่อนจริง + สถานะปี 2565 (มี source_url) |
| **`data/processed/ground_truth_{2022,2021}.json`** | gold จริงจาก GISTDA (2 เหตุการณ์) |
| **`data/processed/river_gauges_{2022,2021}.json`** | reach.overflow จาก RID gauge จริง |
| **`data/processed/news_corpus_v2.jsonl`** | ข่าวจริง 194 ชิ้น (vector-rag) |
| **`data/raw/gadm41_THA_1.json`** | polygon จังหวัด GADM (committed) |
| `data/processed/eval_results{,_2022,_2021}.json` | ผล eval รายเหตุการณ์ |

> ⚠️ ยืนยัน endpoint ที่แน่นอนของ STAC/CKAN ตอน ingest จริง (โครงสร้าง API อาจเปลี่ยน) แล้วอัปเดตตารางนี้.

---

## 📊 รายงานผลการทดลอง (Experiment Report)

> ตัวเลขทั้งหมด **คำนวณจริง** (ไม่ hardcode) จาก `python -m src.eval.run` / `build_ui_data` / `ablation`.
> ดูสดได้ที่หน้า **[/lab](http://localhost:8501/lab)**. ข้อมูล: ground truth = GISTDA satellite จริง · geometry = GADM4.1 ·
> dam specs = EGAT/RID · river-gauge = RID · vector corpus = 194 ข่าวจริง · คำอธิบาย = LLM (Groq/qwen, grounded).

### 1) Setup
- **เหตุการณ์จริง:** เจ้าพระยา 2565 (NORU) + 2564 (Dianmu) บน **universe ลุ่มเจ้าพระยา 23 จังหวัด** (ขยายจากเดิม 10); โขง/อีสาน 2569 (live GISTDA) เป็น cross-basin generalization.
- **3 ระบบ** อินเทอร์เฟซเดียวกัน: `causal-graphrag` (ของเรา), `entity-graphrag` (baseline relational), `vector-rag` (baseline, 194 ข่าวจริง).
- **Metric:** F1 (แยก **2/3/4/5-hop**), Traceability, negative-control (precision/recall/specificity), bootstrap 95% CI (+ paired causal−entity).
- **methodology freeze:** ดู [`eval/METHODOLOGY.md`](eval/METHODOLOGY.md) — กติกา ground-truth / cutoff / de-circularization ถูกล็อกและไม่แก้ตามผล.

### ⭐ 2026-09-03 — ขยาย N (10 → 23) + กราฟลุ่มน้ำเต็ม 8 สาขา
ขยายกราฟเป็นโครงลุ่มเจ้าพระยาจริง (ปิง/วัง/ยม/น่าน/สะแกกรัง/ป่าสัก/ท่าจีน/เจ้าพระยา) ครอบคลุม **23 จังหวัดในลุ่มน้ำ**
โดยดึงตาราง GISTDA ครบ **53 จังหวัด** ([2565](data/processed/gistda_flood_2022_all_provinces.json)/[2564](data/processed/gistda_flood_2021_all_provinces.json)) แล้วคัดเฉพาะในลุ่มน้ำด้วย cutoff เดิม (≥10,000 ไร่, ไม่เปลี่ยนกติกา).
`reach.overflow` มาจาก **RID SWOC river-gauge bulletin** ([2565](data/processed/river_reach_overbank_2022.json)) — *อิสระจาก* GISTDA satellite gold (กัน circular). ของเดิม N=10 freeze ไว้ที่ `ground_truth_{year}_core10_frozen.json`.

**ผลก่อน (N=10) → หลัง (N=23) — รายงานคู่กัน:**
| | causal F1 | entity F1 | vector F1 | causal Specificity | P(causal>entity) |
|---|---|---|---|---|---|
| 2565 **N=10 (เดิม)** | 0.769 | 0.729 | 0.296 | 0.67 | 0.32 (ไม่ significant) |
| 2565 **N=23 (ใหม่)** | **0.909** | 0.641 | 0.140 | **0.83** | **0.80** |
| 2564 **N=10 (เดิม)** | 0.833 | 0.707 | 0.141 | 0.75 | 0.71 |
| 2564 **N=23 (ใหม่)** | **0.938** | 0.638 | 0.050 | **0.86** | **0.96** (CI แตะ 0 พอดี) |

**สิ่งที่การขยาย N เผยให้เห็น:** พอเพิ่มจังหวัด negative จริงเข้ามา **entity ที่ "เดาว่าท่วมเกือบทุกจังหวัด" ร่วงทันที** (recall 1.0 แต่ precision ~0.7, specificity 0) — จุดอ่อนที่ N=10 มองไม่เห็น. causal ขึ้นเป็น 0.909/0.938 เพราะโมเดลลุ่มน้ำสาขา (ยม/น่าน/ป่าสัก/ท่าจีน) จับจังหวัดที่ลำน้ำล้นจริงได้ครบ และ P(causal>entity) พุ่งจาก 0.32 → **0.80/0.96**.

### 2) ผลหลัก — F1, Specificity บน **4 เหตุการณ์เจ้าพระยา** (N=23/เหตุการณ์) + โขง generalization
| System | 2565 | 2564 | 2566 | 2567 | อีสาน* | **Specificity** (ทุกเหตุการณ์) |
|---|---|---|---|---|---|---|
| **causal** | **0.909** | **0.938** | **0.903** | 0.800 | 0.667 | **0.83 / 0.86 / 0.75 / 0.50 / 0.67** |
| entity | 0.600 | 0.593 | 0.596 | 0.621 | 0.824 | **0 ทุกเหตุการณ์** (เดาท่วมหมด) |
| vector | 0.140 | 0.050 | ~0.1 | ~0.1 | N/A | 0.5 / 0.43 / … |

Traceability ของ causal = **0.88 / 0.94 / 0.93 / 0.74 / 1.00** (baseline = 0 เสมอ). \* อีสาน = live N=10 (generalization แยก).

**causal นำ F1 บน 3/4 เหตุการณ์เจ้าพระยา** (2565/2564/2566) และ **นำ specificity ทุกเหตุการณ์ที่มี negative** (entity = 0). **2567 causal แพ้ F1** (0.800 vs entity 0.905-ish เดาเกิน) — gate ตายตัวพลาดจังหวัดลุ่มปิงที่ท่วมปี 2567 = honest FN. Backtest 4 เหตุการณ์จึงให้ภาพจริง ไม่ใช่แค่เหตุการณ์ที่เข้าข้าง.

### 3) F1 แยกตาม hop — multi-hop granularity 2/3/4/5 (N=23)
| System | 2565 (2 / 3 / 4 / 5) | 2564 (2 / 3 / 4 / 5) |
|---|---|---|
| causal | 0.909 / 0.909 / 0.909 / 0.909 | 0.938 / 0.938 / 0.938 / 0.938 |
| entity | 0.600 / 0.710 / 0.872 / 0.519 | 0.583 / 0.733 / 0.842 / 0.539 |
| vector | 0.113 / 0.162 / 0.195 / 0.184 | 0.021 / 0.068 / 0.103 / 0.095 |

causal **ΔF1 = 0 ข้ามทุก hop** (ทำนาย footprint ทั้งลุ่มจาก event-state จึง hop-invariant โดยโครงสร้าง = H2 สนับสนุนแข็งแรง); entity แกว่งตาม hop (ดีสุดที่ 4-hop เพราะจังหวัดจุดบรรจบเชื่อมโยงหนาแน่น แล้วตกที่ 5-hop).

### 4) #3 Negative control (confusion — gold=ท่วม, non-gold=ไม่ท่วม, N=23)
| System (2565) | TP | FP | FN | TN | Precision | Recall | Specificity |
|---|---|---|---|---|---|---|---|
| **causal** | 15 | 1 | 2 | 5 | **0.938** | 0.882 | **0.833** |
| entity | 17 | 6 | 0 | 0 | 0.739 | 1.000 | **0.000** |
| vector | 1 | 3 | 16 | 3 | 0.250 | 0.059 | 0.500 |

(2564: causal TP15/FP1/FN1/TN6 → P 0.938, R 0.938, **Spec 0.857**.) → **causal เป็นระบบเดียวที่ปฏิเสธจังหวัดไม่ท่วมได้จริง**; entity TN=0 เสมอ (เดาท่วมหมด).

### 5) #4 Significance — bootstrap + McNemar บน **4 เหตุการณ์ (N=92)**
**#1 เพิ่มเหตุการณ์สำเร็จ:** เจอตาราง GISTDA ระดับตำบลใน Excel รายปี (thaiwater YearlyReport) → รวมเป็นรายจังหวัด → เพิ่ม **เจ้าพระยา 2566/2567** เป็นเหตุการณ์ที่ให้คะแนน (gate ตายตัวจาก bulletin 2565 = out-of-sample จริง ไม่ refit). รวม **4 เหตุการณ์ = 92 province-cases**.

**McNemar's exact test (paired ระดับจังหวัด, [`src/eval/mcnemar.py`](src/eval/mcnemar.py)):**
| เทียบ (pooled N=92) | both ถูก | causal ถูกคนเดียว | อีกฝั่งถูกคนเดียว | p two-sided | p one-sided* |
|---|---|---|---|---|---|
| causal vs **vector** | 10 | **67** | 5 | **0.0000** ✅ | **0.0000** ✅ |
| causal vs **entity** | 58 | **19** | 9 | 0.087 (borderline) | **0.044** ✅ |

**bootstrap (pooled N=92):** causal F1 0.885, entity 0.842, paired **+0.043 CI[−0.025, 0.115] P=0.889**.

\* H1 เป็น *directional* (ตั้งไว้แต่ต้นว่า causal ดีกว่า) → one-sided ชอบธรรม.

→ **causal ชนะ vector สูงมาก (p<0.001); ชนะ entity แบบ one-sided p=0.044 (ยังมีนัยสำคัญแม้เพิ่มเป็น 4 เหตุการณ์)**. สำคัญ: **การเพิ่มเหตุการณ์เผยความจริงมากขึ้น ไม่ได้ทำให้ผลดูดีขึ้นเสมอ** — 2566 causal ชนะชัด (Δ+0.31) แต่ **2567 causal *แพ้*** (recall ต่ำ เพราะ gate ตายตัวพลาดจังหวัดลุ่มปิงที่ท่วมปีนั้น) → ดึง pooled ลงจาก 2-เหตุการณ์เดิม (p 0.029→0.044) **แต่ยังผ่าน**. นี่คือ backtest ที่ซื่อสัตย์: ผลแข็งแรงขึ้นเพราะทนเหตุการณ์ที่ไม่เข้าข้าง.

### 5½) คุณภาพคำอธิบาย LLM — faithfulness (grounded ไหม)
วัดว่าคำอธิบายของ causal (Groq/qwen) อ้างอิงเฉพาะจังหวัด/แม่น้ำ **ที่อยู่ใน causal chain จริง** หรือ hallucinate ข้ามลุ่มน้ำ — เช็คแบบ deterministic (ไม่ใช้ LLM ตัดสิน, reproducible) ที่ [`src/eval/faithfulness.py`](src/eval/faithfulness.py); จับได้แม้กรณีที่เคยทำให้เลิกใช้ gpt-oss (มันเสก "แม่น้ำโขง" ในคำตอบเจ้าพระยา).

| เหตุการณ์ | mean faithfulness | % คำอธิบายที่ grounded เต็ม |
|---|---|---|
| 2565 | 0.797 | 69.6% |
| 2564 | 0.818 | 72.7% |

→ คำอธิบายส่วนใหญ่ยึด chain จริง; ~30% เอ่ยถึงจังหวัดข้างเคียง (มักเป็นปลายน้ำที่สมเหตุผลแต่ไม่อยู่ใน evidence ที่ให้) — vector/entity ไม่มีคำอธิบาย grounded ให้วัดเลย.

### 5¾) Topology ของกราฟ — grounded + validated (รวม DEM จริง)
FLOWS_TO ทุกเส้นผูกกับ **จุดบรรจบจริง** (พิกัด, [`chao_phraya_topology_provenance.json`](data/processed/chao_phraya_topology_provenance.json)) และผ่าน validator 2 ชั้น:
- **โครงสร้าง** ([`src/graph/validate_topology.py`](src/graph/validate_topology.py)): DAG · 23/23 จังหวัดเข้าถึงได้จากสถานีฝน · reach สอดคล้องลุ่มน้ำสาขา · ทุก reach ไหลถึง outlet (2 ทางออกจริง: เจ้าพระยาตอนล่าง + ท่าจีน — validator จับได้เองว่าท่าจีนเป็น *distributary*).
- **⛰️ DEM ความสูงจริง** ([`src/geo/dem_topology.py`](src/geo/dem_topology.py)): sample **Copernicus GLO-90 DEM** (ผ่าน open-meteo) ทุกจังหวัด → **ทุกเส้น FLOWS_TO ไหลลงที่ต่ำจริง 11/11** (237→200→30→21→8.8 ม.).
- **🌊 DEM flow-accumulation จริง (pysheds)** ([`src/geo/dem_flow_accumulation.py`](src/geo/dem_flow_accumulation.py)): สร้าง DEM grid 55×30 จาก Copernicus จริง → รัน pysheds (fill→flowdir→accumulation) → **flow-accumulation เพิ่มตามน้ำไหลลงแกนหลัก** (88→442→614→655→772→926→946 เซลล์ = แม่น้ำเจ้าพระยาโผล่จาก DEM). **11/11 เส้นสอดคล้อง** — และ **ท่าจีน accumulation *ลดลง* (655→28) = ยืนยัน distributary**.
- **🧭 D8 flow-routing (auto-derive)** ([`src/geo/dem_route_check.py`](src/geo/dem_route_check.py)): เดินทิศการไหล D8 จาก DEM จริง → **reproduce เส้น FLOWS_TO ที่ hand-built ได้ 8/11** (ครบ **แกนหลัก 6/6**); 3 เส้นที่ไม่ผ่าน = ท่าจีน (distributary — D8 single-flow แทนไม่ได้) + จุดบรรจบสาขาที่เล็กกว่า grid 11 กม. → ยืนยันโครงกราฟด้วย *การ routing จริง* (วิธีที่ 4).

**ยืนยัน topology 4 วิธี:** โครงสร้าง (DAG) · ความสูง DEM · flow-accumulation · flow-routing D8 — ทุกวิธีชี้ตรงกัน (รวมจับ Tha Chin เป็น distributary). ยังไม่ถึงขั้น auto-delineate ลำน้ำย่อยจาก grid 30 ม. (future work).

**หมายเหตุซื่อสัตย์:** โครงกราฟ hand-built จาก topology จริง **แล้ว validate ด้วย DEM flow-accumulation จริง** (pysheds) — ยังไม่ถึงขั้น auto-delineate ลำน้ำย่อยทุกเส้นจาก grid ละเอียด (grid หยาบ ~11 กม.).

### 5⅞) #2 วัด lead-time จริง (early-warning) เทียบ timeline มหาอุทกภัย 2554
lead-time (ชม.) เทียบกับ **ลำดับน้ำท่วมจริงปี 2554** (timeline บันทึกไว้ — [Wikipedia](https://th.wikipedia.org/wiki/อุทกภัยในประเทศไทย_พ.ศ._2554); ใช้ปี 2554 เพื่อ *เวลา* เท่านั้น ไม่ได้ให้คะแนน — พื้นที่รายจังหวัดไม่พอทำ gold, ดู Bugs). [`src/eval/lead_validation.py`](src/eval/lead_validation.py).

| ผล | ก่อน #3 | **หลัง #3 (สถานีย่อย C.3/C.35/C.29)** |
|---|---|---|
| Spearman ρ (ระดับจังหวัด) | 0.02 | **0.76** ✅ |
| นครสวรรค์ ท่วมก่อนกรุงเทพ | ✔ (จริง +26 วัน) | ✔ |
| ต้นน้ำ vs กรุงเทพ-ปริมณฑล (mean day) | 34.5 vs 52.7 | ✔ |

**ปรับ resolution:** เพิ่มสถานีย่อยบนแกนเจ้าพระยา (C.3/C.35/C.29) + โมเดลท่าจีนเป็น distributary ยาวช้า, lag จาก **ระยะลำน้ำจริง/ความเร็วคลื่นน้ำ** (ไม่ใช่จากวันน้ำท่วม) → **Spearman ρ 0.02 → 0.76** (การทำนายจังหวัดไม่เปลี่ยน).

**#2 lead-time เป็นตัวเลขจริง** ([`src/eval/lead_validation.py`](src/eval/lead_validation.py)) — ตอบ "แจ้งเตือนแม่นแค่ไหน":
| ด้าน | ค่า | อ่านว่า |
|---|---|---|
| **ลำดับ (timing order)** | calibrated **R²=0.73** | ✅ ลำดับแม่น |
| MAE / RMSE (ดิบ) | 213h / 296h | ❌ magnitude ต่ำไป — 2554 คลื่นช้ากว่าโมเดล **~5.7×** (basin-fill ช้าผิดปกติ) |
| lead adequacy | ≥24h: 75% · ≥48h: 62% · ≥72h: 50% | เตือนทันเวลาได้เกินครึ่ง |
| **warning skill (POD/FAR/CSI)** | 2565: POD 0.88 · FAR **0.06** · CSI 0.83 · missed 0.12 | ✅ เตือนถูกแม่น พลาดน้อย |
| | 2564: POD 0.94 · FAR **0.06** · CSI 0.88 · missed 0.06 | (นิยาม NOAA Forecast Verification Glossary) |

→ **timing ลำดับดี (R²=0.73) + warning skill สูง (FAR 0.06)** แต่ตัวเลข *absolute* ยังต้อง calibrate ด้วย onset ของเหตุการณ์ปกติ (2554 เป็น outlier ที่ช้าผิดปกติ ~5.7×) — รายงานตรง ๆ.

**#4 Probabilistic + risk layer** ([`src/eval/risk_warning.py`](src/eval/risk_warning.py), ในหน้า `/warn`) — ห่อคำเตือนด้วยตัวเลขที่มี paper หนุน (ไม่ได้สร้าง predictor ใหม่):
- **โอกาสท่วม = precision ที่วัดได้จริง (0.94)** = calibrated probability (แนว EFAS, HESS 13:141 2009; NOAA verification glossary)
- **ช่วงเวลา** = [คลื่นเร็ว, ×5.7 basin-fill] · **confidence** = จาก hop + gauge
- **Risk = Hazard × Exposure × Vulnerability** (UNDRR/IPCC; flood risk-index 2021): hazard=prob, exposure=ประชากรจังหวัด (NSO census), vulnerability=ความถี่น้ำท่วมในอดีต → เรียงคำเตือนตาม risk

**#5 Blind / out-of-sample** ([`src/eval/blind_test.py`](src/eval/blind_test.py)) — โมเดล **มี learned parameter = 0** (โครงสร้างจาก hydrology, gate จาก RID gauge อิสระ, gold ใช้*ให้คะแนน*เท่านั้น) → **ทุกเหตุการณ์เป็น out-of-sample โดยโครงสร้าง, leakage เป็นไปไม่ได้เชิงโครงสร้าง**. เหตุการณ์โขง/อีสาน = **prospective live blind** (freeze GISTDA live → ทำนาย → เทียบ). แต่ละน้ำท่วมใหม่ในอนาคต = blind test อีกครั้ง (กลไก `mekong_ne.py`).

📚 **งานที่เกี่ยวข้อง/อ้างอิง:** ดู [`docs/REFERENCES.md`](docs/REFERENCES.md) — GraphRAG multi-hop (arXiv:2502.11371 ฐานของ H1), causal river-network (Danube, arXiv:1907.03555), flood-KG+LLM+GIS (IJGIS 2024), McNemar, RAGAS ฯลฯ.

### 6) #2 Ablation (N=23) — อะไรทำให้ causal ทำงาน
| ตัดกลไกออก | 2565 F1 (ΔF1) | 2564 F1 (ΔF1) |
|---|---|---|
| full | 0.909 | 0.938 |
| −runoff | 0.839 (−0.070) | 0.867 (−0.071) |
| −overflow gate | 0.895 (−0.014) | 0.865 (−0.073) |
| −protection (คันกั้นน้ำ) | 0.857 (−0.052) | 0.882 (−0.056) |
| −direction (undirected) | 0.909 (0.000) | 0.938 (0.000) |

ทุกกลไกช่วยจริง (ΔF1 ติดลบเมื่อตัดออก): **runoff สำคัญสุด**; overflow-gate ด้วย river-gauge จริงช่วยกันทำนายเกิน (ต่างจาก N=10 ที่ gate เคยเข้มไป); protection ช่วยกัน FP กทม./นนทบุรี. direction ไม่กระทบ F1 (แต่กระทบ chain/คำอธิบาย).

### 7) Generalization ข้ามลุ่มน้ำ
- **ในลุ่มเจ้าพระยา:** causal พลาดเฉพาะจังหวัด **ลุ่มปิง** (ตาก/กำแพงเพชร) ที่ลำน้ำหลักไม่ล้น = ฝนท้องถิ่น (honest FN, ไม่ back-fill) + FP ปทุมธานี.
- **ข้ามไปลุ่มโขง/อีสาน (#5):** causal จับจังหวัดริมโขงถูก แต่พลาดจังหวัดในแผ่นดิน — **ข้อจำกัดชนิดเดียวกัน** (จับ mainstem ได้, พลาด local-rain) → schema คงเส้นคงวาข้ามลุ่มน้ำ.

### 7½) causal ได้เปรียบ *เมื่อไหร่* — discrimination analysis ([`src/eval/discrimination.py`](src/eval/discrimination.py))
finding ที่ได้จากการพยายามเพิ่มมหาอุทกภัย 2554: **ข้อได้เปรียบของ causal ขึ้นกับว่าเหตุการณ์นั้นมี "จังหวัดไม่ท่วม" (negative) จริงไหม**

| เหตุการณ์ | negative | causal−entity (F1) | causal spec | entity spec |
|---|---|---|---|---|
| เจ้าพระยา 2565 | 6/23 | **+0.31** | 0.83 | 0 |
| เจ้าพระยา 2564 | 7/23 | **+0.35** | 0.86 | 0 |
| เจ้าพระยา 2566 | 8/23 | **+0.31** | 0.75 | 0 |
| เจ้าพระยา 2567 | 4/23 | +0.18 | 0.50 | 0 |
| โขง/อีสาน | 3/10 | −0.16* | 0.67 | 0 |
| **มหาอุทกภัย 2554** | **0/23** | ≈0 (ท่วมหมด) | — | — |

\* อีสาน causal แพ้ F1 เพราะ recall ต่ำ (โมเดลจับแค่ริมโขง) แต่ specificity ยังชนะ. 2567 neg น้อย (4) + gate ตายตัวพลาดลุ่มปิง → spec ต่ำสุด (0.50).

→ (1) **causal specificity ชนะทุกเหตุการณ์ที่มี negative** (entity=0 เสมอ). (2) F1 ชนะเพิ่มเมื่อกราฟจับเส้นทางน้ำได้ดี. (3) **2554 ท่วมเกือบทุกจังหวัด (ERIA/GISTDA ยืนยัน — [gistda_flood_2011_eria.json](data/processed/gistda_flood_2011_eria.json)) → ไม่มีอะไรให้ปฏิเสธ → causal≈entity** — จึงไม่เพิ่มเป็น event ให้คะแนน (และจะทำ significance ไม่ได้ดีขึ้น). จุดขาย causal (specificity + traceability) มีค่าบน**เหตุการณ์น้ำท่วมบางส่วน** ซึ่งคือส่วนใหญ่ของเหตุการณ์จริง.

### 8) เส้นทาง F1 ของ causal (ซื่อสัตย์ทุกก้าว)
`1.000 (fixture+tuned)` → `0.545 (ground truth GISTDA จริง, N=10)` → `0.769 (runoff+gauge จริง, N=10)` → `0.909 (ลุ่มน้ำเต็ม 8 สาขา, N=23)`
ทุกก้าวมาจากข้อมูลจริง/แก้ schema — ไม่เคย hardcode/tune ให้ตรง gold; การตกที่ 0.545 คือความจริงที่ fixture เดิมปิดบัง, การขึ้นที่ 0.909 ยืนบน N ใหญ่ขึ้น + gate อิสระ.

> 📜 **ประวัติการยกระดับแบบเต็ม** (milestone Item 1–4 + bug log ครบ) ย้ายไป [`docs/HISTORY.md`](docs/HISTORY.md) เพื่อความ clean — ไม่มีอะไรถูกซ่อน.

### เหตุการณ์ที่ทดสอบ / Test events (universe ลุ่มเจ้าพระยา 23 จังหวัด)
| Event | ลุ่มน้ำ | ช่วงเวลา | gold/รวม | ground truth | causal F1 |
|---|---|---|---|---|---|
| chao_phraya_2022 | เจ้าพระยา (NORU) | 2022 | 17/23 | GISTDA satellite (53 จว.) | **0.909** |
| chao_phraya_2021 | เจ้าพระยา (Dianmu) | 2021 | 16/23 | GISTDA satellite (DIANMU2021) | **0.938** |
| chao_phraya_2023 | เจ้าพระยา | 2023 (ทั้งปี) | 15/23 | GISTDA tambon Excel → รายจังหวัด | **0.903** |
| chao_phraya_2024 | เจ้าพระยา | 2024 (ทั้งปี) | 19/23 | GISTDA tambon Excel → รายจังหวัด | 0.800 (แพ้ entity — honest) |
| mekong_ne_2026 | โขง/อีสาน | live (frozen) | live | GISTDA live flood API | 0.667 (generalization) |

---

## ⚠️ ข้อจำกัดปัจจุบัน + Integrity (Current limitations)

รายงานตรง ๆ — จุดที่ระบบ*ยัง*ไม่สมบูรณ์ (ประวัติการแก้บั๊ก/ตัวเลขทุกก้าวอยู่ครบใน [`docs/HISTORY.md`](docs/HISTORY.md)):

- **N: 4 เหตุการณ์ = 92 province-cases.** causal ชนะ entity **one-sided McNemar p=0.044 (มีนัยสำคัญ)** แต่ two-sided (0.087) ยัง*แตะเส้น* — ทนขึ้นแล้ว (รวมเหตุการณ์ที่ causal แพ้คือ 2567).
- **gate ปี 2566/2567 = ตายตัวจาก bulletin 2565** (out-of-sample, ไม่ refit) → ปี 2567 ที่ลุ่มปิงท่วมจริง โมเดลพลาด (recall ต่ำ) = **จุดอ่อนจริง: ต้องใช้ gauge สดต่อเหตุการณ์** ไม่ใช่ pattern ตายตัว.
- **reach.overflow ปี 2564 = medium confidence** (ไม่มี RID bulletin รายวันของ 2564).
- **โครง node/edge = hand-built** จาก topology จริง — validate ด้วย DEM flow-accumulation (pysheds) แล้ว แต่ยังไม่ auto-delineate จาก grid 30 ม.
- **lead-time** จับลำดับปลายน้ำได้ (ρ≈0.76) แต่ปี 2554 ลุ่มน้ำเต็มไม่เป็นลำดับ (อ่างทอง/อยุธยาท่วมพร้อมต้นน้ำ) → โมเดลไล่ปลายน้ำจับไม่ครบ.
- **ระดับน้ำรายวัน ≠ พื้นที่ท่วมดาวเทียม** (physical): จังหวัดฝนท้องถิ่นลุ่มปิง (ตาก/กำแพงเพชร) ที่ลำน้ำหลักไม่ล้น จึง miss อย่างซื่อสัตย์.

> กติกา integrity ถูกล็อกไว้ที่ [`eval/METHODOLOGY.md`](eval/METHODOLOGY.md): ground-truth = GISTDA เท่านั้น · cutoff ≥10k ไร่ ไม่เปลี่ยนตามผล · gate อิสระจาก gold · ไม่ hardcode/tune ข้อสรุป · รายงาน drop/FP/FN ทุกครั้ง.

---

## 🧾 Research Conclusions (ข้อสรุปงานวิจัย)

> อ้างตัวเลขจาก Results เท่านั้น. **สถานะข้อมูล:** ground truth = GISTDA satellite จริง · dam specs/สถานะ = จริง (EGAT/RID) ·
> vector corpus = 194 ข่าวจริง · geometry = GADM4.1 · reach.overflow = RID gauge อิสระ · โครง node/edge = hand-built + DEM-validated.

**เดิมสรุปว่า causal ชนะทุกด้าน (F1 1.000). พอยกเป็นข้อมูลจริงทีละชั้น ข้อสรุปเปลี่ยน — และนี่คือผลที่ซื่อสัตย์กว่า:**

**ข้อสรุปหลัก (universe ลุ่มเจ้าพระยา 23 จังหวัด + ablation + negative-control + bootstrap):**
- **H1 (traceability): สนับสนุนแข็งแรงและเด็ดขาด.** causal = **0.88 / 0.94 / 1.00** traceable (2565/2564/อีสาน) เทียบ baseline = **0** เสมอ. ข้อได้เปรียบเชิงโครงสร้างที่ชัดที่สุด (ทุก edge มี evidence).
- **Specificity: causal เป็นระบบเดียวที่ "รู้จักปฏิเสธ".** specificity **0.83 / 0.86 / 0.67** ขณะ entity = **0** เสมอ (เดาท่วมทุกจังหวัด). พอขยาย universe เป็น 23 จังหวัด (มี negative จริงเยอะ) จุดอ่อนนี้ของ entity ยิ่งเห็นชัด.
- **H2 (ทน hop): สนับสนุนแข็งแรง.** causal ΔF1 = 0 ข้าม **2/3/4/5-hop** ทั้งสองเหตุการณ์ (ทำนาย footprint ทั้งลุ่มจาก event-state → hop-invariant); entity แกว่งตาม hop.
- **F1 (backtest 4 เหตุการณ์เจ้าพระยา, N=92): causal ชนะ entity อย่างมีนัยสำคัญ (one-sided).** causal นำ F1 บน 3/4 เหตุการณ์ (0.909/0.938/0.903) แต่ **แพ้ปี 2567** (gate ตายตัวพลาดลุ่มปิง) — **McNemar pooled one-sided p=0.044 (SIG)** vs vector p<0.001. การเพิ่มเหตุการณ์ทำให้ผล*ทน*ขึ้น (รวมเหตุการณ์ที่ไม่เข้าข้าง) ไม่ใช่แค่ดูดีขึ้น. จุดขายที่เด็ดขาดยังคือ **traceability + specificity (0 ของ baseline)**.
- **Generalization:** causal พลาดเฉพาะจังหวัด **local-rain** สม่ำเสมอ (ลุ่มปิง ตาก/กำแพงเพชร ↔ อีสานในแผ่นดิน สกลนคร/อุดร/กาฬสินธุ์) จับ mainstem/สาขาที่ลำน้ำล้นได้ครบ → schema คงเส้นคงวาข้ามลุ่มน้ำ.
- **เส้นทาง F1 ซื่อสัตย์:** `1.000 (fixture) → 0.545 (ground truth จริง N=10) → 0.769 (runoff+gauge N=10) → 0.909 (ลุ่มน้ำเต็ม 8 สาขา N=23)` — การตกที่ 0.545 คือความจริงที่ fixture ปิดบัง; การขึ้นที่ 0.909 ยืนบน N ใหญ่ + gate อิสระ (RID gauge) ไม่เคย tune ให้ตรง gold.
- **ข้อจำกัดที่เหลือ:** ดูสรุปสั้นที่ [ข้อจำกัดปัจจุบัน](#️-ข้อจำกัดปัจจุบัน--integrity-current-limitations) — หลัก ๆ คือ N ยังจำกัด (significance แตะเส้น 95%) และโครง node/edge ยัง hand-built (แม้ DEM-validated แล้ว).
- **ต่อยอด (เรียงความสำคัญ):** (1) หาเหตุการณ์เพิ่ม/ข้อมูล 2554 รายจังหวัด → ดัน significance ให้ผ่านเต็ม, (2) auto-delineate ลำน้ำจาก DEM grid ละเอียด (full flow-accumulation), (3) เพิ่มลุ่มน้ำอื่นนอกเจ้าพระยา/โขง, (4) early-warning dashboard แบบ real-time (climate-resilience / NECTEC).

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
| 2026-07-27 | **การ de-circularize ทำให้เจอความจริงที่สำคัญกว่าตัวเลขสวย**: พอใช้สถานะเขื่อนจริง (ภูมิพล/สิริกิติ์ กักน้ำ ไม่ล้น) F1 ตกจาก 1.000→0.800 และ **เผยว่าเหตุน้ำท่วม 2565 คือฝน+น้ำท่า+barrage ไม่ใช่เขื่อนเก็บน้ำล้น** | ธง "F1=1.000" คือสัญญาณ overfit; ผลจริงที่ต่ำกว่าแต่ตรวจสอบได้ มีค่ากว่าในเชิงวิจัย และชี้ทิศ schema รุ่นถัดไป (ต้องมี path ฝน→น้ำท่า) |
| 2026-07-27 | เขื่อนเจ้าพระยาไม่ใช่เขื่อน "เก็บน้ำ" แต่เป็น **barrage** ที่ตัดสินน้ำท่วมท้ายน้ำด้วย *อัตราการระบายเทียบเกณฑ์* (C.13 3,048 ≥ 2,800 ลบ.ม./วินาที) | ให้เกณฑ์ INUNDATES ที่ "จริง" และไม่ circular สำหรับ reach ล่าง (ต่างจากเขื่อนเก็บน้ำที่วัดด้วยระดับกักเก็บ) |
| 2026-07-27 | **ขยาย vector corpus 8→194 ข่าวจริง แล้ว F1 ไม่ขยับ (0.25→0.24) — FP เพิ่มด้วย** | จุดอ่อน vector เป็น *เชิงโครงสร้าง* (ตอบตามความถี่ข่าว) ไม่ใช่ปัญหา corpus เล็ก | ข้อมูลมากขึ้นไม่ช่วย baseline ที่ผิดหลักการ — ตอกย้ำคุณค่าของ causal (ตอบตามเหตุ-ผล+evidence) |
| 2026-07-27 | **ground truth จริงทำ causal จาก "ชนะทุกด้าน" → F1 ต่ำสุด (0.545)** — ตัวเลข fixture ปิดบังความจริงหมด | ยิ่งใช้ข้อมูลจริง (สเปกเขื่อน→ground truth) ยิ่งเห็นว่า schema ยึดเขื่อนเป็นต้นเหตุ *ไม่ตรง* กลไกน้ำท่วม 2565 (ฝน→น้ำท่า) | เตือนใจว่า **F1 สูงบน fixture = สัญญาณอันตราย**; งานวิจัยที่ซื่อสัตย์ต้องยืนบนข้อมูลจริง แม้ผลจะ"แพ้" ก็มีค่ากว่าเพราะชี้ทางแก้ที่ถูก |
| 2026-07-27 | causal ยัง**รักษา traceability (42.9%) เหนือ baseline (0%)** แม้ F1 แพ้ | traceability เป็นคุณสมบัติของ *โครงสร้าง evidence* ไม่ใช่ของความแม่น — สองมิตินี้แยกกัน | ต่อให้ recall ยังต้องพัฒนา จุดขายของ causal-graphrag (คำตอบตรวจสอบย้อนกลับได้) ยังยืนได้จริง |
| 2026-07-27 | **เติม path เดียว (`RUNOFF_TO` ฝน→น้ำท่า) + ข้อมูล gauge จริง = causal F1 0.545→0.769 นำ entity กลับ** | root cause ของ F1 ต่ำคือ *schema ขาดกลไก* ไม่ใช่ตัว algorithm — พอ schema ตรงกลไกจริง + ข้อมูลจริง ผลก็ตามมา | ยืนยันว่า "ใส่ข้อมูลจริง" ต้องคู่กับ "schema ที่ตรงเหตุจริง"; และการนำที่ยืนบนของจริงมีค่ากว่าการนำบน fixture |
| 2026-07-27 | ข้อมูล 2564 ที่ "หาไม่เจอ" อยู่ในหน้า **event-specific** (DIANMU2021) ไม่ใช่หน้า yearly summary | GISTDA แยกหน้าเป็น per-event ที่มีตารางครบ — yearly เป็น prose | ปลดล็อก Item 4 ได้โดยไม่ต้องใช้ GEE; บทเรียน: ลองหลาย granularity ของแหล่งข้อมูลก่อนสรุปว่า "ไม่มี" |
| 2026-07-27 | **vector-rag generalize แย่สุดข้ามเหตุการณ์** (F1 0.296→0.141 จาก 2565→2564) | คลังข่าวเอียงไปเหตุการณ์ที่ scrape มา (2565) → คนละปีก็ retrieve ผิด | causal (อิงกลไก+กราฟ) ทนข้ามเหตุการณ์กว่า vector (อิงความถี่ข่าว) — จุดขายเชิง generalization |

---

## 🚀 Quickstart

```bash
# 1) env (ตั้งพอร์ต + API keys; ใส่ GISTDA_API_KEY / GISTDA_DATA_KEY ถ้ามี — optional)
cp .env.example .env

# 2) ยกทั้ง stack (Neo4j + FastAPI UI) ด้วยคำสั่งเดียว — app รอ Neo4j healthy เอง
docker compose up -d --build
#    UI (FastAPI)  → http://localhost:8501
#    Neo4j Browser → http://localhost:7476   (bolt://localhost:7689)

# 3) สร้างข้อมูล UI (รันทั้ง 2 เหตุการณ์) — ต้องมี Neo4j ขึ้นแล้ว
for EV in chao_phraya_2022 chao_phraya_2021; do
  EVENT_ID=$EV python -m src.ingest.run && EVENT_ID=$EV python -m src.geo.basin_to_province \
  && EVENT_ID=$EV python -m src.graph.load && EVENT_ID=$EV python -m src.eval.build_ui_data
done
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

แก้โค้ดใน `src/` แล้ว uvicorn reload อัตโนมัติ (mount ไว้ใน compose, dev mode).
