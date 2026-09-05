# เล่มโครงงาน — Thai Flood Causal-Chain GraphRAG
### ระบบอธิบายเหตุน้ำท่วมด้วยกราฟความรู้เชิงสาเหตุ ที่ตรวจสอบย้อนกลับได้
*A Causal-Chain GraphRAG for Verifiable Flood Explanation over the Chao Phraya Basin*

> เอกสารนี้อธิบาย **วิธีการทำทั้งหมด + ผลการทดลองทั้งหมด** ของโครงงาน เพื่อให้อ่านเข้าใจได้ครบ
> และใช้เป็น **เอกสารอ้างอิงสำหรับจัดทำวิทยานิพนธ์/บทความวารสาร** ต่อไป. ตัวเลขทุกตัวมาจากการรันจริง
> (ไม่ hardcode) — reproduce ได้ตาม §3.12. ประวัติการยกระดับตัวเลขทุกก้าวอยู่ใน [`HISTORY.md`](HISTORY.md).

---

## สารบัญ
- [บทที่ 1 บทนำ](#บทที่-1-บทนำ)
- [บทที่ 2 ทฤษฎีและงานที่เกี่ยวข้อง](#บทที่-2-ทฤษฎีและงานที่เกี่ยวข้อง)
- [บทที่ 3 วิธีการดำเนินงาน](#บทที่-3-วิธีการดำเนินงาน)
- [บทที่ 4 ผลการทดลอง](#บทที่-4-ผลการทดลอง)
- [บทที่ 5 สรุปและข้อเสนอแนะ](#บทที่-5-สรุปและข้อเสนอแนะ)
- [บรรณานุกรม](#บรรณานุกรม) · [ภาคผนวก](#ภาคผนวก)

---

# บทที่ 1 บทนำ

## 1.1 ที่มาและความสำคัญ
ระบบถาม-ตอบด้วย AI ส่วนใหญ่ใช้ **Retrieval-Augmented Generation (RAG)** แบบ *vector search* — ฝังคำถามเป็น
เวกเตอร์แล้วค้นเอกสารที่คล้ายที่สุด. วิธีนี้ตอบได้เมื่อคำตอบอยู่ในเอกสารเดียว แต่ **เดินตามความสัมพันธ์หลายชั้น
ไม่ได้** และ **ตรวจสอบย้อนกลับไม่ได้** ว่าคำตอบมาจากหลักฐานใด. งาน **GraphRAG** แก้ปัญหานี้บางส่วนด้วยการ
เดินกราฟความรู้ แต่ที่ผ่านมาวัด "จำนวน hop" แบบ *entity-relation* (เช่น มัสยิด → จังหวัด → ที่พัก) เท่านั้น

**ช่องว่างงานวิจัย:** ยังไม่มีใครวัดว่า hop ที่เป็น **สายเหตุ-ผลเชิงกายภาพจริง (causal chain)** —
```
ฝนต้นน้ำ → ระดับน้ำเขื่อน → น้ำล้น/ระบาย → ระดับน้ำแม่น้ำท้ายน้ำ → น้ำท่วมจังหวัดปลายน้ำ
```
— จะยากขึ้นสำหรับ GraphRAG ในอัตราเดียวกับ hop แบบ entity-relation หรือไม่, และ **การเดินตามสายเหตุ-ผลจริง
ให้คำอธิบายที่ verify ได้ดีกว่าการค้นข่าวหรือไม่**. โครงงานนี้เลือกโดเมน **น้ำท่วมลุ่มเจ้าพระยา** ซึ่งมีสายเหตุ-ผล
เชิงอุทกวิทยาที่ชัดเจน และมีข้อมูลจริง (ดาวเทียม GISTDA, สถานีวัดน้ำ RID) ให้ตรวจสอบได้

## 1.2 คำถามวิจัยและสมมติฐาน
- **คำถาม:** GraphRAG ที่เดินตาม *causal chain จริง* ให้คำอธิบายน้ำท่วมที่ **ตรวจสอบย้อนกลับได้ (traceable)**
  และ **แม่นยำ** กว่า vector search และ entity-GraphRAG แค่ไหน — และชนะตรงไหน?
- **H1 (traceability):** การเดินกราฟตามสายเหตุ-ผลจริงให้คำอธิบายที่ traceable ได้มากกว่า baseline
- **H2 (ทน hop):** F1 ของ causal-GraphRAG จะ *ไม่* ลดลงตามความยาว causal chain เร็วเท่ากับ baseline

## 1.3 วัตถุประสงค์
1. สร้างกราฟความรู้เชิงสาเหตุของลุ่มเจ้าพระยาบน Neo4j จากข้อมูลจริง (ทุก edge มีหลักฐานอ้างอิง)
2. เปรียบเทียบ 3 ระบบ (causal-GraphRAG, entity-GraphRAG, vector-RAG) บนชุดวัดผลเดียวกัน
3. วัด **F1 แยกตามความยาว causal-hop**, **Traceability**, **Specificity** เทียบ ground truth ดาวเทียม GISTDA
4. ทดสอบความมีนัยสำคัญทางสถิติ และความแกร่ง (backtest หลายเหตุการณ์ + blind test)
5. ต่อยอดเป็นระบบ **เตือนภัยล่วงหน้า** (extension) เพื่อประโยชน์เชิง climate-resilience

## 1.4 ขอบเขต
- **พื้นที่:** ลุ่มน้ำเจ้าพระยา 8 ลุ่มน้ำสาขา (ปิง/วัง/ยม/น่าน/สะแกกรัง/ป่าสัก/ท่าจีน/เจ้าพระยา) **23 จังหวัด**
- **เหตุการณ์:** น้ำท่วมจริง 4 เหตุการณ์ (2564/2565/2566/2567) + ลุ่มน้ำโขง/อีสาน (generalization)
- **Ground truth:** พื้นที่น้ำท่วมจริงจากดาวเทียม GISTDA (Sentinel-1) เกณฑ์ ≥ 10,000 ไร่/จังหวัด
- **ไม่ครอบคลุม:** แบบจำลองอุทกวิทยาเชิงฝน-น้ำท่า (rainfall-runoff) เต็มรูป — อยู่ใน future work

## 1.5 ประโยชน์ที่คาดว่าจะได้รับ
- ชุดวัดผล **Thai causal-hop KGQA** สำหรับน้ำท่วม (ทรัพยากรที่แทบไม่มีเป็นสาธารณะ)
- หลักฐานเชิงประจักษ์ว่า *การอธิบายที่ตรวจสอบย้อนกลับได้* มีค่ากว่าความแม่นเพียงอย่างเดียวในโดเมนภัยพิบัติ
- ต้นแบบระบบเตือนภัยล่วงหน้าที่บอก "ทำไม" ได้ (ต่อยอด NECTEC/social-good agenda)

---

# บทที่ 2 ทฤษฎีและงานที่เกี่ยวข้อง

## 2.1 RAG และ GraphRAG
- **RAG (vector):** ค้นเอกสารด้วยความคล้ายเวกเตอร์ (embedding) — เก่งงานเอกสารเดียว, อ่อน multi-hop, ไม่ traceable
- **GraphRAG:** ดึงข้อมูลจากกราฟความรู้ (KG) — เดินความสัมพันธ์ได้; งานอ้างอิง arXiv:2502.11371 รายงานว่า
  ช่องว่างของ GraphRAG เหนือ vanilla กว้างขึ้นตาม hop (H1 ของงานนี้อิงผลนี้) แต่วัดบน entity-relation hop
- **ความต่างของงานนี้:** วัด **causal hop** (สายเหตุ-ผลเชิงกายภาพ) ไม่ใช่ relational hop — เป็นมิติใหม่

## 2.2 อุทกวิทยาลุ่มน้ำ (พื้นฐานที่ใช้สร้างกราฟ)
- **ลุ่มน้ำสาขา (sub-basin):** เจ้าพระยาประกอบจาก 8 สาขา; น้ำจากปิง+น่าน (+ยม) รวมกันที่ **ปากน้ำโพ**
  (Pak Nam Pho, นครสวรรค์) กลายเป็นแม่น้ำเจ้าพระยา แล้วไหลลงใต้ผ่านชัยนาท→สิงห์บุรี→อ่างทอง→อยุธยา→กรุงเทพ
- **reach / การล้นตลิ่ง:** แต่ละช่วงลำน้ำ (reach) มีความจุ; เมื่ออัตราการไหลเกินความจุ → ล้นตลิ่ง → ท่วมจังหวัดริมน้ำ
- **distributary (ทางน้ำแยก):** แม่น้ำท่าจีนแยกออกจากเจ้าพระยาที่ชัยนาท ไหลลงอ่าวไทยแยกต่างหาก (ไม่รวมกลับ)
- **flood wave celerity:** คลื่นน้ำท่วมเดินทางตามลำน้ำด้วยความเร็ว ~1–2 ม./วินาที (ใช้คำนวณ lead-time)

## 2.3 ตัวชี้วัดและสถิติ
- **F1** ของเซตจังหวัด (precision/recall), **Traceability** = สัดส่วนคำตอบที่ทุก edge มี evidence,
  **Specificity** = ความสามารถระบุ "ไม่ท่วม" (negative control)
- **McNemar's exact test** (McNemar 1947): การทดสอบ paired สำหรับ classifier สองตัวบน item เดียวกัน —
  เหมาะกับ N เล็กกว่า F1-bootstrap; **Bootstrap CI**: resample เพื่อประเมินความไม่แน่นอนของ F1
- **flood EWS verification (NOAA glossary):** POD (probability of detection), FAR (false alarm ratio),
  CSI (critical success index); **Risk = Hazard × Exposure × Vulnerability** (UNDRR/IPCC)
- (บรรณานุกรมเต็ม + ความต่างจากงานเดิม: ดู [`REFERENCES.md`](REFERENCES.md))

---

# บทที่ 3 วิธีการดำเนินงาน

## 3.1 สถาปัตยกรรมระบบ
| ชั้น | เทคโนโลยี | หน้าที่ |
|---|---|---|
| Graph DB | **Neo4j 5.x** (Docker) | เก็บกราฟเหตุ-ผล + query variable-length path (`*2..8`) วัด hop |
| Orchestration | **Python 3.11** | ingest → geo → load → eval |
| Geo | **GeoPandas + Shapely** | point-in-polygon: reach → จังหวัด (INUNDATES) + overlay flood extent |
| LLM | **Groq (qwen)** ผ่านโมดูล provider-agnostic | คำอธิบายภาษาไทยที่ grounded ตาม chain |
| Vector baseline | **TF-IDF (scikit-learn)** | vector-RAG บนคลังข่าว 194 ชิ้น |
| DEM | **Copernicus GLO-90** (open-meteo) + **pysheds** | ตรวจสอบ topology (ทิศไหล/flow-accumulation) |
| UI/API | **FastAPI + MapLibre GL + Chart.js** | 2 หน้า (user/research) + extension + proxy GISTDA |

**การไหลของ pipeline:** `fixtures` (สร้าง node/edge) → `geo` (INUNDATES + gold) → `graph.load` (เข้า Neo4j)
→ `eval` (3 retrievers, F1-by-hop) → `build_ui_data` (confusion/bootstrap/faithfulness) → รายงาน

## 3.2 แหล่งข้อมูลจริง (ทั้งหมด cited)
| ข้อมูล | แหล่ง | ใช้ทำอะไร |
|---|---|---|
| พื้นที่น้ำท่วมรายจังหวัด (ground truth) | **GISTDA satellite** (Sentinel-1) ผ่าน thaiwater — หน้า event + Excel ระดับตำบล | gold (≥10k ไร่) |
| การล้นตลิ่งรายลุ่มน้ำ (gate) | **RID SWOC** river-gauge bulletin (อิสระจาก satellite) | `reach.overflow` |
| สเปกเขื่อน + สถานะ | **EGAT/RID** (`dam_specs.json`) | spillway, active |
| ขอบเขตจังหวัด | **GADM 4.1** level-1 | geometry (polygon จริง) |
| ความสูงภูมิประเทศ | **Copernicus GLO-90 DEM** (open-meteo) | ตรวจ topology |
| ประชากรจังหวัด | **NSO** สำมะโน 2020 | exposure (risk) |
| ข่าวน้ำท่วม | Google News RSS (194 ชิ้น) | vector-RAG corpus |

**หลักการ de-circularization ที่สำคัญ:** `reach.overflow` (สัญญาณ gate) มาจาก *river-gauge* ซึ่งเป็น
เครื่องมือวัด **อิสระ** จาก *satellite flood extent* (gold). ไม่มีค่าใดของ gate ถูกตั้งจากผลน้ำท่วมที่จะนำไปให้คะแนน

## 3.3 กราฟความรู้เชิงสาเหตุ (schema)
**Node labels:** `RainStation` · `Reservoir` · `RiverReach` · `Confluence` · `Province`
**Relationships (มีทิศ = ทิศการไหล):**
- `(:RainStation)-[:FEEDS {lag_hours}]->(:Reservoir)` — ฝนเข้าเขื่อน
- `(:RainStation)-[:RUNOFF_TO {lag_hours}]->(:RiverReach)` — ฝน→น้ำท่าลงลำน้ำ (bypass เขื่อน) *[กลไกจริงปี 2565]*
- `(:Reservoir)-[:OVERFLOWS_TO {spillway}]->(:RiverReach)` — เขื่อนล้น/ระบาย
- `(:RiverReach)-[:FLOWS_TO {lag_hours}]->(:RiverReach|:Confluence)` — น้ำไหลตามลำน้ำ
- `(:RiverReach)-[:INUNDATES {threshold}]->(:Province)` — ลำน้ำล้นท่วมจังหวัด

**กติกาเหล็ก:** ทุก relationship มี property `evidence` = `{station_id, timestamp, dataset}` ชี้กลับ source
record — นี่คือหัวใจของ H1 (traceability). *(หมายเหตุ: Neo4j ไม่รับ nested map เป็น property → เก็บ evidence
เป็น JSON string; ตรวจ `evidence IS NULL` เพื่อยืนยัน traceability)*

## 3.4 โครงลุ่มน้ำ 8 สาขา · 23 จังหวัด · gate
- **8 ลุ่มน้ำสาขา** แต่ละสาขามีสถานีฝน (+เขื่อน ถ้ามี) → reach → INUNDATES จังหวัดที่ลำน้ำไหลผ่าน (ภูมิศาสตร์จริง)
- **การไหลจริง (FLOWS_TO):** วัง→ปิง; ปิง/ยม/น่าน→ปากน้ำโพ→เจ้าพระยาตอนบน→(ชัยนาท–สิงห์บุรี C.3)→
  (อ่างทอง–อยุธยา C.35)→(อยุธยา–กรุงเทพ C.29); สะแกกรัง/ป่าสักเข้าเจ้าพระยา; ท่าจีนแยกออกที่ชัยนาท
- **gate 2 ชั้น (de-circularized):** ทำนายว่าจังหวัดท่วมเมื่อ (1) `last_reach.overflow = true` (ลำน้ำหลักล้น
  ความจุจริงจาก RID gauge) **และ** (2) จังหวัดไม่มีคันกั้นน้ำป้องกัน (`protected=false`; กทม./นนทบุรี = King's Dyke)
- **lag_hours ของแกนหลัก** ตั้งจาก *ระยะลำน้ำจริง ÷ ความเร็วคลื่นน้ำ* (ไม่ใช่จากวันน้ำท่วม = ไม่ circular)

## 3.5 3 retrievers + กติกาความยุติธรรม
| ระบบ | วิธีดึงข้อมูล | traceable? |
|---|---|---|
| **causal-graphrag** (ของเรา) | เดินกราฟ *ตามทิศการไหล* `*2..8` + gate overflow/protection; chain มี evidence | ✅ |
| entity-graphrag (baseline) | เดินกราฟ *ไม่สนทิศ* (undirected) `*2..4`; ไม่มี gate/evidence → เดาเกิน | ✗ |
| vector-rag (baseline) | TF-IDF ค้นคลังข่าว → ดึงจังหวัดที่ข่าวพูดถึง | ✗ |
**กติกา:** ทั้ง 3 ระบบใช้ eval set เดียว, universe จังหวัดเดียว, prompt/LLM เดียว(ที่ใช้ LLM) → ความต่างมาจาก
*วิธี retrieve* เท่านั้น (freeze ไว้ใน [`METHODOLOGY.md`](../eval/METHODOLOGY.md))

## 3.6 การสร้าง Ground Truth (4 เหตุการณ์)
1. ดึงตาราง GISTDA พื้นที่ท่วมรายจังหวัด: เหตุการณ์ 2565/2564 จากหน้า event; **2566/2567 จาก Excel ระดับตำบล
   → รวม (sum) เป็นรายจังหวัด** (`build_ground_truth.py`)
2. **เกณฑ์ gold คงที่:** จังหวัดที่พื้นที่ท่วม ≥ 10,000 ไร่ = gold (positive); ต่ำกว่า = negative — *เกณฑ์นี้ไม่เปลี่ยน
   ตามผล* (ป้องกันการ gaming)
3. **universe คงที่ 23 จังหวัด** (นิยามจากภูมิศาสตร์ก่อนดูผล)

## 3.7 การวัดผล (ครบทุก metric)
1. **F1-by-hop** (2/3/4/5-hop): group ผลตามความยาว causal chain → ทดสอบ H2 (`f1_by_hop.py`)
2. **Traceability**: สัดส่วนคำตอบที่ evidence ครบ
3. **Negative control / confusion**: TP/FP/FN/TN, precision/recall/**specificity** (`build_ui_data.py`)
4. **นัยสำคัญ:** **McNemar's exact test** (paired ระดับจังหวัด, `mcnemar.py`) + **bootstrap CI** pooled
   ข้ามเหตุการณ์ (`pooled_significance.py`)
5. **Explanation faithfulness** (`faithfulness.py`): เช็ค deterministic ว่าคำอธิบาย LLM อ้างเฉพาะภูมิศาสตร์ใน chain
   (จับ hallucination ข้ามลุ่มน้ำ)
6. **Discrimination analysis** (`discrimination.py`): causal ได้เปรียบเมื่อเหตุการณ์มี negative จริงไหม
7. **Ablation** (`ablation.py`): ปิดกลไกทีละตัว (runoff/overflow-gate/protection/direction) → ΔF1

## 3.8 การตรวจสอบ Topology 4 วิธีอิสระ
1. **โครงสร้าง** (`validate_topology.py`): เป็น DAG · 23/23 จังหวัดเข้าถึงได้จากสถานีฝน · reach สอดคล้องลุ่มน้ำ ·
   ทุก reach ไหลถึง outlet (2 ทางออกจริง: เจ้าพระยาตอนล่าง + ท่าจีน)
2. **DEM ความสูง** (`dem_topology.py`): ทุกเส้น FLOWS_TO ไหล *ลงที่ต่ำ* จริงบน Copernicus DEM
3. **DEM flow-accumulation** (`dem_flow_accumulation.py`, pysheds): flow-accumulation เพิ่มตามน้ำไหลลงแกนหลัก
   (แม่น้ำเจ้าพระยาโผล่จาก DEM); ท่าจีน accumulation *ลด* = ยืนยัน distributary
4. **D8 flow-routing** (`dem_route_check.py`): เดินทิศการไหล D8 จาก DEM → reproduce เส้น FLOWS_TO ที่ hand-built

## 3.9 Extension: การเตือนภัยล่วงหน้า (พยากรณ์)
กลับด้านกราฟ: ตั้งลุ่มน้ำที่ล้น (input) → query `EARLY_WARNING_PREDICT` → จังหวัดปลายน้ำ + lead-time + chain
- **lead-time validation** (`lead_validation.py`): เทียบลำดับ/เวลากับ timeline มหาอุทกภัย 2554 (ใช้เพื่อ *เวลา*
  เท่านั้น ไม่ให้คะแนน) → Spearman ρ, MAE/RMSE, calibrated R², **warning skill POD/FAR/CSI**
- **probability + risk** (`risk_warning.py`): โอกาส = precision ที่วัดได้; ช่วงเวลา = [คลื่นเร็ว, ×5.7 basin-fill];
  **Risk = โอกาส × ประชากร(NSO) × ความถี่น้ำท่วม** (H×E×V). *ไม่ได้สร้าง predictor ใหม่ — ห่อผลด้วยเลขที่มี paper รองรับ*
- **outcome-feedback: Case Bank + calibration** (`case_bank.py`, `calibration.py`): เก็บเคสทำนายถูก/ผิดเทียบ GISTDA
  (**92 เคส · POD 0.866 · FAR 0.094 · CSI 0.795**) แล้วปรับ *ความน่าจะเป็น* แบบ leave-one-event-out (prequential):
  Brier **0.086 → 0.0725** (sharp ขึ้น) — *โดยไม่แตะกราฟ/gate จึงกัน overfitting*; แสดง track record ในหน้า `/warn`

> **📌 โน้ตสำหรับเล่ม (ส่วนชดเชย / social-good):** ส่วน extension นี้ทำเป็น **ระบบจริงที่รันได้แล้ว** (ไม่ใช่แค่แนวคิด) —
> มี lead-time ที่ผูกกับ timeline จริง, warning skill ที่วัดได้, risk ตามมาตรฐาน UNDRR/IPCC, และชั้นเรียนรู้จากผลที่กัน
> overfitting. ใช้เป็น **บทเสริมด้าน climate-resilience / early-warning (NECTEC social-good)** ได้อย่างมั่นใจและความเสี่ยงต่ำ
> เพราะยืนบนโครงเดียวกับงานหลัก (0 learned params) — **ข้อจำกัดที่รายงานตรง:** N ยังจำกัด (64 คำเตือน/4 เหตุการณ์),
> lead-time แม่นเชิง *ลำดับ* แต่ *magnitude* ยังต้อง calibrate เพิ่ม, และ prospective log จริงยังต้องสะสมต่อ.

## 3.10 Blind / out-of-sample
โมเดล **ไม่มี learned parameter** (โครงสร้างจากอุทกวิทยา, gate จาก RID gauge, gold ใช้*ให้คะแนน*เท่านั้น)
→ ทุกเหตุการณ์เป็น out-of-sample โดยโครงสร้าง, gold leakage เป็นไปไม่ได้. เหตุการณ์ 2566/2567 ใช้ gate
*ตายตัวจาก bulletin 2565* (ไม่ refit) = out-of-sample จริง; ลุ่มน้ำโขง = prospective live blind (`blind_test.py`)

## 3.11 UI (2 identity)
- **หน้า user (`/`):** "field report" อธิบายเหตุน้ำท่วม + chain + evidence + แผนที่ GISTDA + เทียบ 3 ระบบ
- **หน้า research (`/lab`):** "instrument console" แสดงทุก metric ทีละส่วน (ดึงจาก `/api/report`)
- **extension (`/warn`):** เตือนภัย + ที่มาของตัวเลข + ความไม่แน่นอน

## 3.12 การทำซ้ำ (reproducibility) + กติกา integrity
```
docker compose up -d neo4j
python -m src.ingest.build_ground_truth
for Y in 2022 2021 2024 2023: EVENT_ID=chao_phraya_$Y python -m {fixtures,geo,load,eval,ablation,build_ui_data}
python -m src.eval.{mcnemar,pooled_significance,discrimination,lead_validation,blind_test}
pytest -q   # 29 tests
```
**กติกาเหล็ก (freeze):** ground-truth = GISTDA เท่านั้น · cutoff ≥10k ไม่เปลี่ยนตามผล · gate อิสระจาก gold ·
ไม่ hardcode/tune ข้อสรุป · รายงาน drop/FP/FN ทุกครั้ง · เพิ่มเหตุการณ์ = ข้อมูลจริง ไม่ปั้น

---

# บทที่ 4 ผลการทดลอง

## 4.1 ผลหลัก — F1, Traceability, Specificity (4 เหตุการณ์เจ้าพระยา, universe 23 จังหวัด)
| ระบบ | 2565 | 2564 | 2566 | 2567 | โขง* | Traceability | Specificity |
|---|---|---|---|---|---|---|---|
| **causal-graphrag** | **0.909** | **0.938** | **0.903** | 0.800 | 0.667 | **0.88/0.94/0.93/0.74/1.00** | **0.83/0.86/0.75/0.50/0.67** |
| entity-graphrag | 0.600 | 0.593 | 0.596 | 0.621 | 0.824 | **0 ทุกเหตุการณ์** | **0 ทุกเหตุการณ์** |
| vector-rag | 0.140 | 0.050 | ~0.1 | ~0.1 | N/A | 0 | 0.5/0.43 |

\* โขง/อีสาน = generalization test แยก (live N=10)

**อ่านผล:** causal นำ F1 บน **3/4 เหตุการณ์** และนำ **Traceability + Specificity ทุกเหตุการณ์** (baseline = 0 เสมอ);
**2567 causal แพ้** เพราะ gate ตายตัวพลาดจังหวัดลุ่มปิงที่ท่วมปีนั้น (honest FN)

## 4.2 F1 แยกตาม causal-hop (H2)
causal ΔF1 ≈ 0 ข้าม 2/3/4/5-hop (ทำนาย footprint ทั้งลุ่มจาก event-state → hop-invariant); entity แกว่งตาม hop
→ **H2 สนับสนุน** (causal ทน hop, baseline ไม่ทน)

## 4.3 นัยสำคัญทางสถิติ (pooled 4 เหตุการณ์, N = 92 province-cases)
| เทียบ | both ถูก | causal เดี่ยว | อีกฝั่งเดี่ยว | McNemar p (2-sided) | p (1-sided)* |
|---|---|---|---|---|---|
| causal vs vector | 10 | **67** | 5 | **< 0.001** ✅ | **< 0.001** ✅ |
| causal vs entity | 58 | **19** | 9 | 0.087 (แตะเส้น) | **0.044** ✅ |

\* H1/H2 เป็น directional → one-sided ชอบธรรม. **bootstrap:** paired +0.043, CI[−0.025, 0.115], P=0.889

**อ่านผล:** causal ชนะ vector อย่างมีนัยสำคัญสูง; **ชนะ entity แบบ one-sided p=0.044 (มีนัยสำคัญ)** แม้เพิ่มเป็น
4 เหตุการณ์ (รวมปี 2567 ที่ causal แพ้) — ผล **ทน** ขึ้น ไม่ใช่แค่ดูดี = backtest ที่ซื่อสัตย์

## 4.4 Negative control (confusion, ตัวอย่าง 2565)
causal: TP15/FP1/FN2/TN5 → precision 0.938, recall 0.882, **specificity 0.833** ·
entity: TP17/FP6/FN0/**TN0** → specificity **0** (เดาท่วมหมด) → **causal เป็นระบบเดียวที่ "รู้จักปฏิเสธ"**

## 4.5 Discrimination — causal ได้เปรียบเมื่อไหร่
| เหตุการณ์ | negative | causal−entity F1 | causal spec |
|---|---|---|---|
| 2565 | 6/23 | +0.31 | 0.83 |
| 2564 | 7/23 | +0.35 | 0.86 |
| 2566 | 8/23 | +0.31 | 0.75 |
| 2567 | 4/23 | +0.18 | 0.50 |
| มหาอุทกภัย 2554 | **0/23** | ≈0 (ท่วมหมด) | — |
→ **causal specificity ชนะทุกเหตุการณ์ที่มี negative**; เหตุการณ์ที่ท่วมเกือบทั้งลุ่ม (2554) ไม่มีอะไรให้ปฏิเสธ →
causal≈entity (จึงไม่เพิ่ม 2554 เป็น event ให้คะแนน — non-discriminating + agricultural-subset)

## 4.6 Ablation (2565)
full 0.909 · −runoff 0.839 (**ตกมากสุด = กลไกสำคัญ**) · −overflow-gate 0.895 · −protection 0.857 ·
−direction 0.909 (ทิศไม่กระทบ F1 แต่กระทบ chain/คำอธิบาย)

## 4.7 Topology (ตรวจ 4 วิธี — ตรงกันหมด)
DAG ✅ · DEM ความสูง 11/11 เส้นไหลลงที่ต่ำ ✅ · flow-accumulation 11/11 (ท่าจีน = distributary) ✅ ·
D8 routing 8/11 (แกนหลัก 6/6) ✅

## 4.8 Lead-time / warning skill (extension)
- Spearman ρ = **0.76** (ลำดับปลายน้ำ) · calibrated R² = **0.73** · MAE ดิบ 213h (2554 ช้ากว่าโมเดล ~5.7×, outlier)
- **warning skill:** causal 2565 POD 0.88 · FAR **0.06** · CSI 0.83 · missed 0.12 (2564: POD 0.94)
→ ลำดับ/การเตือนแม่น (FAR ต่ำ) แต่ตัวเลข *absolute* ต้อง calibrate (2554 เป็น basin-fill ช้าผิดปกติ)

## 4.9 Blind / out-of-sample
learned parameters = **0** → ทุกเหตุการณ์ held-out; F1 held-out 0.91/0.94/0.90/0.80/0.67 (2565/2564/2566/2567/โขง)

## 4.10 เส้นทาง F1 (ซื่อสัตย์ทุกก้าว)
`1.000 (fixture tuned)` → `0.545 (ground truth GISTDA จริง)` → `0.769 (runoff+gauge)` → `0.909 (ลุ่มน้ำเต็ม 8 สาขา)`
— การตกที่ 0.545 คือความจริงที่ fixture ปิดบัง; ไม่เคย tune ให้ตรง gold

---

# บทที่ 5 สรุปและข้อเสนอแนะ

## 5.1 สรุปผล (ตอบสมมติฐาน)
- **H1 (traceability): สนับสนุนแข็งแรง.** causal traceable 0.74–1.00 เทียบ baseline = 0 เสมอ — ข้อได้เปรียบที่
  เด็ดขาดและมีนัยสำคัญที่สุด
- **H2 (ทน hop): สนับสนุน.** causal ΔF1 ≈ 0 ข้าม hop; baseline ไม่ทน
- **Specificity:** causal เป็นระบบเดียวที่ปฏิเสธจังหวัดไม่ท่วมได้ (baseline specificity = 0)
- **F1:** causal ชนะ entity แบบ one-sided McNemar p=0.044 (มีนัยสำคัญ) บน 4 เหตุการณ์; ชนะ vector p<0.001
- **บทสรุปเชิงลึก:** จุดขายที่มีค่าที่สุดของ causal-GraphRAG คือ **คำอธิบายที่ตรวจสอบย้อนกลับได้ + รู้จักปฏิเสธ**
  (มีค่าในโดเมนภัยพิบัติ) มากกว่าตัวเลข F1 ล้วน ๆ; และมีค่าเฉพาะบน **เหตุการณ์ discriminating** (ท่วมบางส่วน)

## 5.2 ข้อจำกัด (รายงานตรง ๆ)
1. **N ยังจำกัด** (4 เหตุการณ์, 92 cases) — F1 vs entity อยู่ตรงเส้น 95% (one-sided ผ่าน, two-sided แตะเส้น)
2. **gate ตายตัว** (2566/2567 ใช้ pattern 2565) → ปีที่รูปแบบการล้นต่างออกไปจะพลาด (เห็นชัดที่ 2567) —
   deployment จริงต้องต่อ river-gauge สด
3. **โครง node/edge = hand-built** (validate ด้วย DEM แล้ว แต่ยังไม่ auto-delineate จาก grid 30 ม.)
4. **lead-time** ลำดับแม่น แต่ magnitude ยังไม่ calibrate (2554 เป็น outlier ช้า)
5. **ฝนท้องถิ่น** (ลุ่มปิง ตาก/กำแพงเพชร) ที่ลำน้ำหลักไม่ล้น — miss อย่างซื่อสัตย์ (schema ยังไม่มี local rainfall model)

## 5.3 ข้อเสนอแนะ / งานในอนาคต
1. **Local rainfall → runoff → inundation branch** — แก้จุดอ่อนที่สุด (ฝนท้องถิ่น) แต่เป็นงานอุทกวิทยาขนาดใหญ่
2. **เพิ่มเหตุการณ์ + river-gauge สดต่อปี** → ดัน significance ให้ผ่าน two-sided เต็ม + gate ไม่ตายตัว
3. **Auto-delineate ลำน้ำจาก DEM grid 30 ม.** (full flow-accumulation) → ลบ "hand-built" ชิ้นสุดท้าย
4. **Probabilistic/ensemble forecasting + calibration ด้วย onset จริง** → lead-time absolute แม่นขึ้น
5. **จัดทำวิทยานิพนธ์/บทความวารสาร** จากเอกสารนี้ (เป้าหมายถัดไป)

---

# บรรณานุกรม
ดูฉบับเต็มพร้อมความต่างจากงานเดิมที่ [`REFERENCES.md`](REFERENCES.md) — สรุปหลัก:
- RAG vs GraphRAG systematic evaluation, arXiv:2502.11371 (ฐานของ H1)
- Microsoft GraphRAG, arXiv:2404.16130 · NodeRAG, arXiv:2504.11544
- Causal mechanism of extreme river discharges (Danube), arXiv:1907.03555
- Flood-KG + LLM + GIS, IJGIS 2024, doi:10.1080/13658816.2024.2306167
- EFAS (European Flood Alert System), HESS 13:141, 2009 · Ensemble flood forecasting review, HSJ 2021
- NOAA Forecast Verification Glossary · Risk = Hazard×Exposure×Vulnerability (UNDRR/IPCC)
- McNemar (1947); RAGAS, arXiv:2309.15217
- ข้อมูล: GISTDA satellite, RID SWOC, GADM 4.1, Copernicus GLO-90 DEM, NSO census

# ภาคผนวก
- **โครงสร้าง repo + วิธีรัน:** README.md → System Tour / Quickstart
- **กติกา methodology (freeze):** `eval/METHODOLOGY.md`
- **ประวัติการยกระดับตัวเลขทุกก้าว + bug log:** `docs/HISTORY.md`
- **โค้ดหลัก:** `src/ingest/` (สร้างกราฟ+ground truth) · `src/graph/` (Neo4j+queries+validate) ·
  `src/geo/` (PIP+DEM) · `src/rag/` (3 retrievers+LLM) · `src/eval/` (ทุก metric) · `src/web/` (UI/API)
- **ผลดิบ (JSON):** `data/processed/*.json` (eval_results, mcnemar, pooled_significance, discrimination,
  lead_validation, blind_test, dem_*), `web/ui_data_{year}.json`

---
*จัดทำ 2026-09-04 · โครงงาน Thai Flood Causal-Chain GraphRAG · เอกสารอ้างอิงสำหรับวิทยานิพนธ์/วารสาร*
