# สรุปเล่ม B — Early-Warning ที่ Calibrate จากผลจริง บนกราฟเหตุ-ผล (กัน overfitting)

> ไฟล์เตรียมทำ **เล่ม B** (แยกจากเล่ม A ที่เป็น causal-GraphRAG reasoning) — สรุปว่า B เริ่มจากอะไรของ A,
> ทำอะไรไปแล้ว, ได้ผลยังไง, ระเบียบวิธี/อ้างอิง, ข้อจำกัด, และโครงเล่ม.
> อัปเดต 2026-09-05. ระบบเดียวกับ A (แชร์กราฟ) แต่ claim/บทแยกกัน. ดู [`FORECASTING_ROADMAP.md`](FORECASTING_ROADMAP.md).

---

## 1. Claim ของเล่ม B
**"กราฟเหตุ-ผลเชิงฟิสิกส์ที่ตรึงพารามิเตอร์ (0 learned params) + ชั้น calibration บาง ๆ จากผลทำนายถูก/ผิด
ให้คำเตือนน้ำท่วมที่ *calibrated + มี skill เหนือ climatology + drift-aware* โดยไม่เกิด overfitting."**

ต่างจากเล่ม A (ตอบ "ทำไมท่วม" = verifiability) — เล่ม B ตอบ **"จังหวัดไหน / เมื่อไหร่ / โอกาสเท่าไร"** (prospective).

---

## 2. B เริ่มมาจากอะไรของ A (inheritance)

| ใช้ต่อจาก A (shared) | B เพิ่มเอง |
|---|---|
| Causal graph (Neo4j) + `evidence` ต่อ edge | **กลับทิศกราฟ** → early-warning (`EARLY_WARNING_PREDICT`) |
| gate de-circularized (`overflow` จาก RID · `protected`) | lead-time = Σ `lag_hours` ตามสายสั้นสุด |
| GISTDA gold (ground truth) | risk = Hazard×Exposure×Vulnerability (UNDRR/IPCC) |
| หลัก "0 learned params / blind" | **Case Bank** (เก็บเคสถูก/ผิด) + **calibration** (LOEO) |
| POD/FAR/CSI (มีบางส่วน) | **verification เต็ม**: Brier decomp · BSS · ECE · reliability · sharpness · bootstrap CI · drift |

> B ยืนบนโครงเดียวกับ A ทั้งหมด — จึง **รักษาสมบัติ blind/ไม่ overfit** ที่เป็นจุดขายร่วม

---

## 3. ทำอะไรไปแล้ว (ระบบจริง รันได้)

| ไฟล์ | ทำอะไร |
|---|---|
| `src/eval/lead_validation.py` | lead-time เทียบ timeline 2554 (ρ, MAE/RMSE, POD/FAR/CSI) |
| `src/eval/risk_warning.py` | โอกาส (precision) · window [wave, ×5.7] · risk H×E×V |
| **`src/eval/case_bank.py`** ✅ | เก็บเคสถูก/ผิดเทียบ GISTDA → TP/FP/FN/TN + subbasin + prospective log แยก |
| **`src/eval/calibration.py`** ✅ | calibrate ความน่าจะเป็นแบบ LOEO (empirical by hop) + Brier/reliability |
| **`src/eval/warning_verification.py`** ✅ | Brier **decomposition (Murphy)** · **BSS vs climatology** · **ECE** · sharpness · เทียบ calibrator (const/climatology/by-hop/**Platt**/**isotonic**) · **bootstrap CI** · **drift monitor** |
| `web/warn.html` + `/api/track-record` ✅ | หน้าเตือน + พาเนล track record (สถิติ + เคสถูก/ผิด + BSS/ECE/drift) |
| `tests/test_forecasting.py` ✅ | 4 tests (case bank · calibration · Murphy identity · BSS/drift) |

---

## 4. ผลลัพธ์ (รายงานตรง — ไม่ tune)

### 4.1 Warning skill (binary, 115 province-cases · **5 เหตุการณ์**)
- **POD 0.869 · FAR 0.087 · CSI 0.802** (per-event CSI 0.667–0.882 — คงเส้นคงวา)
- เพิ่มเหตุการณ์ที่ 5 จริง: **เจ้าพระยา 2568 (GISTDA satellite, 11 พ.ย. 2568, 2.44 ล้านไร่/17 จังหวัด)**
  ใช้ **gate ตายตัวจาก 2022** (out-of-sample, protocol เดียวกับ 2023/2024) → TP15/FP1/FN2/TN5 = **CSI 0.833**
- เคสผิดสม่ำเสมอ: **FN = ลุ่มปิง** (ตาก/กำแพงเพชร/เชียงใหม่ = local-rain) · **FP = ปทุมธานี/อุทัยธานี**

### 4.2 Probabilistic verification (80 คำเตือน · **5 เหตุการณ์** · LOEO prequential)
| calibrator | Brier | **BSS** vs climatology | ECE | sharpness |
|---|---|---|---|---|
| const (0.938) | 0.0805 | **−0.008** | 0.025 | 0.000 |
| climatology (ref) | 0.0804 | −0.007 | 0.000 | 0.008 |
| **empirical by-hop** | **0.0743** | **+0.069** | 0.025 | 0.094 |
| Platt (logistic) | 0.0810 | −0.015 | 0.008 | 0.019 |
| isotonic | 0.0794 | +0.006 | 0.000 | 0.034 |

- **finding หลัก:** calibrate ตาม **causal-hop ยังมี skill เป็นบวก (BSS +0.069)** เหนือค่าคงที่/climatology (≈0)
  → ความลึกสายเหตุ-ผลยังเป็นสัญญาณที่มีความหมาย
- **⚠️ ผลที่ซื่อสัตย์กว่าเมื่อเพิ่มเหตุการณ์จริง (2568):** BSS pooled **ตกจาก +0.147 (4 เหตุการณ์) → +0.069 (5 เหตุการณ์)**
  และ **2568 เองมี per-event BSS = −0.322** (calibration ที่เรียนจากปีก่อนไม่ fit ปีนี้ดี — ส่วนหนึ่งเพราะ
  gold 2568 ใช้รายชื่อจังหวัด ไม่ใช่ cutoff ≥10k ไร่ → base-rate สูงต่างออกไป)
  → **การเพิ่มข้อมูลจริงทำให้เห็นว่า calibration *ยังไม่ robust* จริง** (4 เหตุการณ์เดิมทำให้ดูดีเกิน) — รายงานตรงตามกติกา
- **ความไม่แน่นอน:** event-level cluster bootstrap BSS CI95 = **[−0.25, 0.20]** (คร่อม 0);
  per-event LOEO: 2021 .19 · 2022 .19 · 2023 .09 · 2024 .09 · **2025 −0.32**
  → **ยัง *ไม่* significant** — จุดที่ต้องพัฒนา: gold ให้เป็นมาตรฐานเดียว (rai cutoff) + เพิ่มเหตุการณ์ + ฟีเจอร์ calibrate ที่ทนกว่า hop
- **binary skill (CSI) ยังแข็งทั้ง 5 เหตุการณ์** — จุดอ่อนอยู่ที่ *การ calibrate ความน่าจะเป็น* ไม่ใช่การตัดสินใจเตือน
- **Platt/isotonic ไม่ชนะ empirical** — ตรงกับ survey: ข้อมูลน้อย **isotonic เสี่ยง overfit, Platt ก็ยังไม่พอ**
  (Niculescu-Mizil & Caruana 2005) → empirical-by-hop (LOEO) เหมาะสุดกับสเกลข้อมูลนี้

### 4.3 Drift monitor (CSI ตามลำดับเวลา)
`2021: 0.882 · 2022: 0.833 · 2023: 0.824 · 2024: 0.667` → เห็นการเสื่อมชัดปี 2567 (ปีที่ gate ตายตัวพลาดลุ่มปิง)

### 4.4 Lead-time
- **ลำดับแม่น** (Spearman ρ ≈ 0.76, calibrated R² ≈ 0.73) · warning skill FAR ~0.06
- **magnitude ยังไม่ calibrate** (2554 เป็น outlier ช้า ~5.7×) → รายงานเป็นช่วง [wave, ×5.7] + ระบุความไม่แน่นอน

---

## 5. ระเบียบวิธีกัน overfitting (จุดขายเชิงวิธีของ B)
1. **ตรึงโมเดลฟิสิกส์** — กราฟ/gate/lag ไม่แก้จากผล (0 learned params) → blind ยังจริง
2. **ปรับเฉพาะชั้นความน่าจะเป็น** (บาง, พารามิเตอร์น้อย)
3. **Leave-one-event-out (prequential)** — ประเมินเหตุการณ์หนึ่งด้วยเหตุการณ์อื่นเท่านั้น (ไม่มี leakage)
4. **วัด calibration + sharpness คู่กัน** (Gneiting) + **BSS เทียบ climatology** (กัน naïve skill, Pappenberger)
5. **รายงานทุก calibrator + CI ตรง ๆ** — ไม่เลือกเฉพาะที่สวย

**อ้างอิงหลัก:** Murphy (1973) · Brier (1950) · Pappenberger et al. (2015) · Naeini et al. (2015) ·
Gneiting et al. (2007) · Niculescu-Mizil & Caruana (2005) · Gama et al. (2014) · Cloke & Pappenberger (2009)
· WWRP/WGNE verification. (รายการเต็ม: [`REFERENCES.md`](REFERENCES.md))

---

## 6. ข้อจำกัด + สิ่งที่ต้องทำต่อ (เพื่อให้ B เป็นเล่มที่แข็ง)
- [x] **วัด CI ให้ถูกวิธี** — เพิ่ม event-level cluster bootstrap + per-event LOEO (เห็น skill คงเส้นคงวา)
- [x] **prospective log pipeline** — `case_bank.add_prospective()` (log ก่อนรู้ผล) + `resolve_prospective()` (เติมผลภายหลัง)
- [x] **เพิ่มเหตุการณ์จริงที่ 5** — เจ้าพระยา 2568 จาก GISTDA (`src/ingest/add_gistda_2025.py`). ผล: BSS ตก → เห็นว่า
  calibration ยังไม่ robust (ซื่อสัตย์). **ยังต้องเพิ่มอีก** ให้ CI แน่น + ทำ gold 2568 เป็น rai cutoff (ตอนนี้ list-based)
- [x] **prospective log CLI** — `python -m src.eval.case_bank --log EVENT PROV TS` / `--resolve EVENT PROV 1|0`
- [ ] เดินเครื่อง prospective จริง (log เหตุการณ์ที่กำลังจะเกิด → เก็บผล → เพิ่ม N ตามเวลา)
- [ ] **calibrate magnitude ของ lead-time** (ต้องมี onset ของเหตุการณ์ปกติหลายเหตุการณ์)
- [ ] ขยายฟีเจอร์ calibrate (subbasin/#overflow) เมื่อข้อมูลมากพอ (ตอนนี้ hop ปลอดภัยสุด)

---

## 7. โครงเล่ม B (outline เตรียมเขียน)
1. **บทนำ** — ปัญหา early-warning ที่ "อธิบายได้" + ช่องว่าง (พยากรณ์ที่ calibrate จากผลโดยไม่ overfit)
2. **ทฤษฎี/งานที่เกี่ยวข้อง** — verification (Murphy/Brier/BSS) · calibration (Platt/isotonic/ECE) ·
   concept drift/prequential · ensemble flood forecasting
3. **วิธีการ** — กราฟเหตุ-ผล (จาก A) → lead-time/risk → Case Bank → calibration LOEO → verification เต็ม → drift
4. **ผลการทดลอง** — §4 ทั้งหมด (skill · BSS · reliability · CI · drift · calibrator comparison)
5. **สรุป/ข้อเสนอ** — calibrate ตาม causal-hop มี skill; ข้อจำกัด N; roadmap เพิ่มเหตุการณ์/real-time

> **สถานะประเมิน:** ตอนนี้ B = "ดี/รันได้จริง + ระเบียบวิธีแน่น" แต่ยัง **ไม่ significant (CI กว้าง)** →
> ต้องเพิ่มเหตุการณ์ก่อนจะเป็นเล่มเดี่ยวที่แข็งเต็มที่. ระหว่างนี้ใช้เป็น **บท extension ของเล่ม A** ได้ทันที (social-good).
