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

### 4.1 Warning skill (binary, 92 province-cases · 4 เหตุการณ์)
- **POD 0.866 · FAR 0.094 · CSI 0.795** (per-event FAR ต่ำ ~0.06)
- เคสผิดสม่ำเสมอ: **FN = ลุ่มปิง** (ตาก/กำแพงเพชร/เชียงใหม่ = local-rain) · **FP = ปทุมธานี/อุทัยธานี**

### 4.2 Probabilistic verification (64 คำเตือน · LOEO prequential)
| calibrator | Brier | **BSS** vs climatology | ECE | sharpness | reliability | resolution |
|---|---|---|---|---|---|---|
| const (0.938) | 0.0860 | **−0.012** | 0.032 | 0.000 | 0.0010 | 0.0000 |
| climatology (ref) | 0.0857 | −0.009 | 0.000 | 0.010 | 0.0017 | 0.0010 |
| **empirical by-hop** | **0.0725** | **+0.147** | 0.042 | 0.119 | 0.0034 | 0.0160 |
| Platt (logistic) | 0.0853 | −0.004 | 0.020 | 0.031 | 0.0163 | 0.0160 |
| isotonic | 0.0846 | +0.004 | 0.000 | 0.037 | 0.0020 | 0.0024 |

- **finding หลัก:** calibrate ตาม **causal-hop มี skill จริง (BSS +0.147)** ขณะที่ค่าคงที่/climatology **ไม่มี** (BSS ≈ 0)
  → ความลึกของสายเหตุ-ผลเป็นสัญญาณ calibrate ที่มีความหมาย
- **ความไม่แน่นอน (วัดให้ถูกวิธี):**
  - *case-level* bootstrap: BSS CI95 = **[−0.38, 0.34]** (คร่อม 0) — *แคบเกินจริง/ผิดวิธี* เพราะ province-cases
    ในเหตุการณ์เดียวกัน correlated
  - *event-level (cluster) bootstrap* (ถูกต้องกว่า): BSS CI95 = **[0.07, 0.29]** (ไม่คร่อม 0)
  - *per-event LOEO*: ทุกเหตุการณ์ BSS **เป็นบวก** (2021 .23 · 2022 .23 · 2023 .09 · 2024 .09) = skill **คงเส้นคงวา**
  - **สรุปตรง:** หลักฐานเชิง consistency + cluster CI *หนุนว่ามี skill* แต่ **4 clusters ยังน้อยเกินจะเคลม
    significance แบบมั่นใจ** (cluster bootstrap กับ cluster น้อยไม่เสถียร) → ทางที่จะปิดจ็อบคือ **เพิ่มเหตุการณ์**
    (ผ่าน prospective log) *ไม่ใช่จูน*
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
- [ ] **เพิ่มเหตุการณ์จริง (>4)** → ทำให้ CI แน่นพอเคลม significance ได้ (ปัจจัยสำคัญสุด — ต้องมีข้อมูล GISTDA ปีใหม่)
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
