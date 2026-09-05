# แผนพัฒนาส่วนพยากรณ์ + แยกโครงงานเป็น 2 ทิศทาง (Forecasting Roadmap)

> เอกสารวางแผน (proposal) — แยก **ส่วนให้เหตุผล (reasoning)** ออกจาก **ส่วนพยากรณ์ (forecasting)**,
> ออกแบบการ "เรียนรู้จากผลทำนายถูก/ผิด" โดย **ไม่ให้เกิด overfitting**, พร้อม paper อ้างอิง และกลยุทธ์ทำ 2 thesis.
> อัปเดต 2026-09-05 · ยังเป็นแผน (ยังไม่ลงมือเขียนโค้ดส่วนนี้ — จะพัฒนาร่วมกันต่อ).

---

## 0. บทสรุปข้อเสนอ (Executive summary)

1. **แยก 2 โมดูล แต่เป็นระบบเดียว** ที่แชร์ *causal graph* ตัวเดียวกัน
   - **โมดูล A — Causal-GraphRAG (ให้เหตุผล):** "ทำไมจังหวัดนี้ท่วม" → chain + evidence (verifiability)
   - **โมดูล B — Early-Warning (พยากรณ์):** "จังหวัดไหน/เมื่อไหร่/โอกาสเท่าไร" + เรียนรู้จากผลถูก/ผิด
2. **เรียนรู้จากผลโดยไม่ overfit:** ตรึงโมเดลฟิสิกส์ (0 learned params) ไว้เหมือนเดิม → เพิ่มแค่ **Case Bank** (บันทึกคำเตือนก่อนรู้ผล) + **ชั้น calibration บาง ๆ** (ปรับความน่าจะเป็นเท่านั้น ไม่แตะกลไก)
3. **แสดงผลถูก/ผิดในหน้า `/warn`** เป็น "track record" (โปร่งใส + ใช้ปรับ calibration)
4. **กลยุทธ์ thesis:** ระบบเดียว (รวม + ปรับปรุง) แต่เขียน **2 เปเปอร์ claim คมแยกกัน** (A: verifiability, B: calibrated warning) — ได้เครดิตรวมมากกว่าเปเปอร์เดียวที่ claim เบลอ

---

## 1. สถาปัตยกรรม: แยก reasoning ⟂ forecasting

```
                         ┌───────────────────────────────┐
                         │  Causal Graph (Neo4j) — FROZEN │  ← 0 learned params
                         │  โครง/gate/lag = ฟิสิกส์จริง    │     (blind property คงอยู่)
                         └───────┬───────────────┬────────┘
              (โมดูล A)          │               │           (โมดูล B)
        ┌────────────────────────▼──┐        ┌───▼───────────────────────────┐
        │ Causal-GraphRAG · ให้เหตุผล│        │ Early-Warning · พยากรณ์         │
        │ → คำอธิบาย + chain + evidence│      │ → จว. + lead window + prob      │
        │ วัด: traceability, F1-by-hop│       │ วัด: POD/FAR/CSI, calibration    │
        └────────────────────────────┘        └───┬────────────────────────────┘
                 ↑ Thesis A                        │  (เฉพาะโมดูล B)
                                    ┌──────────────▼───────────────┐
                                    │ Prediction Log / Case Bank    │  ← บันทึก "ก่อนรู้ผล"
                                    │ (timestamp · chain · window)  │
                                    └──────────────┬───────────────┘
                                    ผลจริง GISTDA → ป้าย TP/FP/FN/TN
                                    ┌──────────────┼───────────────┬──────────────┐
                                    ▼              ▼               ▼
                          Calibration layer   Track-record     Drift monitor
                          (isotonic/Platt,    panel → /warn    (เตือนเมื่อ skill ตก)
                          rolling holdout)     (โปร่งใส)
                                    │  ↑ Thesis B
                          ปรับ *ความน่าจะเป็น* เท่านั้น — ไม่แตะกราฟ/gate
```

**ทำไมต้องแยก:** สอง question คนละชนิด — A เป็น *explanatory* (retrospective, "ทำไม"), B เป็น *predictive* (prospective, "จะเกิดไหม/เมื่อไหร่"). แยกโค้ด + แยก metric ทำให้ **ประเมินแต่ละอันได้อย่างสะอาด** และ claim ไม่ปน. interface ร่วม = causal graph + evidence.

---

## 2. ส่วนพยากรณ์ + การเรียนรู้จากผลถูก/ผิด (โดยไม่ overfit)

### 2.1 เก็บตัวอย่างถูก/ผิด (Case Bank)
- ทุกครั้งที่ระบบออกคำเตือน → **log ก่อนรู้ผล**: `{ts, event, province, chain, lead_window[24h..×5.7], prob, risk_level}`
- เมื่อผ่านเหตุการณ์ → ดึงผลจริงจาก GISTDA → แปะ outcome → ป้าย **TP / FP / FN / TN**
- เก็บทั้ง **ทำนายถูก** (เช่น กรณีสระบุรี) และ **ทำนายผิด** (เช่น 2567 ลุ่มปิง FN) เป็นคลังตัวอย่างถาวร

### 2.2 แสดงในหน้า `/warn` (track record)
- พาเนล "สถิติการเตือนย้อนหลัง": POD/FAR/CSI สะสม + reliability curve + รายการเคสถูก/ผิดที่เด่น
- โปร่งใส: ผู้ใช้เห็นว่าระบบเคยพลาดที่ไหน (สอดคล้องกติกา integrity ของโปรเจกต์)

### 2.3 กัน overfitting — 5 หลักการ (สำคัญที่สุด)
1. **ตรึงโมเดลฟิสิกส์:** โครงกราฟ / gate (`overflow`, `protected`) / `lag_hours` **ห้ามแก้ตามผล** → ยังเป็น 0 learned params, blind test ยังจริง
2. **ปรับได้แค่ชั้นบาง:** calibration (isotonic regression / Platt scaling) มีพารามิเตอร์น้อยมาก → เสี่ยง overfit ต่ำ; fit บน **rolling temporal holdout** + nested CV
3. **Prospective / prequential เท่านั้น:** เทรน(calibrate)บนอดีต → ทดสอบบนเหตุการณ์อนาคตที่ยังไม่เห็น — ห้าม fit แล้ววัดบนชุดเดิม (กัน leakage)
4. **แยก "ปรับ" ออกจาก "กลไก":** ผลถูก/ผิด ใช้เพื่อ (a) calibrate ความน่าจะเป็น (b) โชว์ track record (c) เฝ้า drift — **ไม่เคย** ใช้จูน threshold/กราฟให้ตรงเฉลย (นั่นคือกับดัก overfit ที่ต้องเลี่ยง)
5. **วัด calibration + sharpness คู่กัน:** ตาม Gneiting et al. — โมเดลต้อง *calibrated* (ความน่าจะเป็นตรงความถี่จริง) และ *sharp* (มั่นใจเท่าที่ควร) พร้อมกัน ไม่ใช่ดันตัวเลขให้สวย

### 2.4 โปรโตคอลประเมิน
- Warning skill: POD / FAR / CSI (NOAA glossary — ใช้อยู่แล้ว)
- Probabilistic: reliability diagram + Brier score + sharpness
- Temporal: prequential (test-then-train) + drift alarm เมื่อ CSI ตกต่ำกว่า baseline

---

## 3. Paper อ้างอิง (แนวทาง improve แบบไม่ overfit)

| หัวข้อ | อ้างอิง |
|---|---|
| **Case-based reasoning** (คลังเคสถูก/ผิด) | Aamodt & Plaza (1994), *Case-Based Reasoning: Foundational Issues…*, AI Communications 7(1):39–59 |
| **Concept drift / online โดยไม่พังจากข้อมูลใหม่** | Gama, Žliobaitė, Bifet, Pechenizkiy, Bouchachia (2014), *A survey on concept drift adaptation*, ACM Computing Surveys 46(4) |
| **Prequential evaluation** (เทรนอดีต-ทดสอบอนาคต) | Gama, Sebastião, Rodrigues (2013), *On evaluating stream learning algorithms*, Machine Learning 90(3); Dawid (1984) prequential principle |
| **Probability calibration (ชั้นบาง พารามิเตอร์น้อย)** | Platt (1999) Platt scaling; Niculescu-Mizil & Caruana (2005), *Predicting Good Probabilities with Supervised Learning*, ICML; Guo et al. (2017), *On Calibration of Modern Neural Networks*, ICML |
| **Calibration + sharpness (หลักคิดพยากรณ์ความน่าจะเป็น)** | Gneiting, Balabdaoui, Raftery (2007), *Probabilistic forecasts, calibration and sharpness*, JRSS-B 69(2) |
| **Forecast verification (คู่มือ)** | Jolliffe & Stephenson (2012), *Forecast Verification*, 2nd ed., Wiley; NOAA Forecast Verification Glossary |
| **Operational/ensemble flood forecasting + post-processing** | Cloke & Pappenberger (2009), *Ensemble flood forecasting: A review*, J. Hydrology 375; EFAS (Thielen et al., HESS 2009) |
| **Data assimilation ในพยากรณ์อุทกวิทยา** | Liu et al. (2012), *Advancing data assimilation in operational hydrologic forecasting*, HESS 16 |

> หลักร่วมของทุกอ้างอิง: **แยก "โมเดลกลไก" (ตรึง) ออกจาก "ชั้นปรับ" (บาง, cross-validate, ทดสอบ prospective)** — เป็นสูตรกัน overfit ที่ยอมรับในวงการ

---

## 4. แผน 2 thesis (เนื้อหาแยกกัน)

### 📘 Thesis A — Causal-Chain GraphRAG เพื่อคำอธิบายน้ำท่วมที่ตรวจสอบได้
- **Claim/novelty:** การเดินกราฟตาม *สายเหตุ-ผลจริง* ให้คำอธิบายที่ **traceable/specific** กว่า entity-graph และ vector-RAG (H1/H2)
- **วิธี:** causal graph + Cypher `*2..8` + evidence ต่อ edge + de-circularized gate
- **ประเมิน:** F1-by-hop, Traceability, Specificity, McNemar/bootstrap, DEM validation, faithfulness
- **สถานะ:** ~เสร็จแล้ว (ฐาน: [`SYSTEM_DEVELOPMENT.md`](SYSTEM_DEVELOPMENT.md) + [`PROJECT_REPORT.md`](PROJECT_REPORT.md))
- **จุดแข็งสอบ:** เป็น novelty ที่ชัด (causal ≠ relational hop) วัดได้ + ซื่อสัตย์ (F1 1.000→0.545→0.909)

### 📗 Thesis B — Early-Warning ที่ calibrate จากผลจริง บนกราฟเหตุ-ผล (กัน overfitting)
- **Claim/novelty:** กราฟฟิสิกส์ที่ **ตรึง (0 learned params)** + ชั้น calibration บาง ๆ จากผลถูก/ผิด → คำเตือนที่ **calibrated + sharp + drift-aware** โดย *ไม่* overfit
- **วิธี:** lead-time (Σlag), risk = Hazard×Exposure×Vulnerability, Case Bank + isotonic/Platt (rolling holdout), prequential eval
- **ประเมิน:** POD/FAR/CSI, reliability/Brier, sharpness, prospective (เหตุการณ์อนาคตจริง เช่น กรณีสระบุรี), drift monitor
- **สถานะ:** โครงมีแล้ว (`risk_warning.py`, `lead_validation.py`, `/warn`) — ต้องเพิ่ม Case Bank + calibration + track record
- **จุดแข็งสอบ:** applied/social-good (NECTEC), มี prospective confirmation จริง, และมี "การกัน overfit" เป็นประเด็นระเบียบวิธีที่ตอบได้

### รวมหรือแยก? — คำแนะนำ
- **ระบบ:** ทำ **ตัวเดียวรวมกัน** (แชร์กราฟ + ทั้ง 2 โมดูล + ปรับปรุงแล้ว) = product/demo ที่สมบูรณ์
- **การเขียน:** **2 เปเปอร์ claim คมแยกกัน** (B อ้าง A) — *ไม่* ยัดเป็นเปเปอร์เดียว เพราะ:
  - เปเปอร์เดียว 2 เรื่อง → claim เบลอ, reviewer เห็น contribution ตื้น 2 อัน → มักได้คะแนน **น้อยกว่า**
  - 2 เปเปอร์ claim คม + ระบบร่วม → เครดิตรวม **มากกว่า** และต่อยอดกันได้
- **ถ้าจำเป็นต้องเล่มเดียว:** ให้ reasoning/verifiability เป็นแกน (บทหลัก) และ forecasting เป็นบท application — อย่าให้ novelty เจือจาง

---

## 4½. แผนที่ไฟล์ → เล่ม (file → thesis mapping)

| ไฟล์ / โมดูล | เล่ม | ทำอะไร |
|---|---|---|
| `src/rag/{causal,entity,vector}_*.py`, `registry.py` | **A** | 3 retrievers ที่เปรียบเทียบ |
| `src/graph/{queries,load,client}.py` | shared | กราฟเหตุ-ผล + Cypher hop/predict |
| `src/geo/dem_*.py`, `graph/validate_topology.py` | **A** | ยืนยัน topology (DEM 4 วิธี) |
| `src/eval/{f1_by_hop,mcnemar,pooled_significance,discrimination,ablation,faithfulness,blind_test}.py` | **A** | วัด verifiability / F1 / สถิติ |
| `src/eval/{lead_validation,risk_warning}.py` | **B** | lead-time + risk = Hazard×Exposure×Vuln |
| `src/eval/case_bank.py` ✅ | **B** | คลังเคสถูก/ผิด (TP/FP/FN/TN) + prospective |
| `src/eval/calibration.py` ✅ | **B** | calibrate ความน่าจะเป็น (LOEO — กัน overfit) |
| `web/warn.html` + `/api/track-record`, `/api/early-warning` ✅ | **B** | หน้าเตือน + track record |
| `src/ingest/*`, `src/geo/basin_to_province.py` | shared | ข้อมูลจริง + สร้างกราฟ |
| `web/index.html` (`/`), `web/lab.html` (`/lab`) | **A** | UI แสดงเหตุผล + ผลการทดลอง |

---

## 5. ขั้นตอน (todo / done)
- [x] **`src/eval/case_bank.py`** — เก็บเคสถูก/ผิดเทียบ GISTDA → **92 เคส: POD 0.866 · FAR 0.094 · CSI 0.795** (FN = ลุ่มปิง local-rain, FP = ปทุม/อุทัย — ตรงที่ documented)
- [x] **`src/eval/calibration.py`** — LOEO (prequential): **Brier คงที่ 0.086 → แยกตาม hop 0.0725** (sharp ขึ้น sd 0.119) = ดีขึ้นโดยไม่ overfit
- [x] **track-record panel** ในหน้า `/warn` + `/api/track-record` (แสดงสถิติ + เคสถูก/ผิด)
- [x] **tests** — `tests/test_forecasting.py` (3 ผ่าน)
- [ ] drift monitor (CSI สะสมข้ามเวลา เทียบ baseline)
- [ ] `case_bank.add_prospective(...)` — บันทึกคำเตือน "ก่อนรู้ผล" จริง (เช่นสระบุรี) พร้อม timestamp
- [ ] เขียนโครงเปเปอร์ B แยกจาก A

> ⚠️ ทุกขั้น: **ห้ามแตะโครงกราฟ/gate จากผลทำนาย** — ปรับได้เฉพาะชั้น calibration บาง ๆ เท่านั้น (กติกากัน overfit ของทิศทาง B)
