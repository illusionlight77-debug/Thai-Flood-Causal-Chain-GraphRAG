# Test UI — ตัวอย่างผลจริงจากหน้าจอ

จับจากหน้า Streamlit `http://localhost:8501` (รันในคอนเทนเนอร์ `thaiflood-app`)
คำถาม: **"ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วมในเหตุการณ์ลุ่มเจ้าพระยาปี 2565?"**
Ground truth จริง (GISTDA, gold 7 จังหวัด): **Ang Thong, Ayutthaya, Chai Nat, Nakhon Sawan, Phitsanulok, Sing Buri, Tak**

> ผลนี้ = สถานะปัจจุบัน (หลัง Item 1–4: ground truth จริง + runoff path + river-gauge จริง).
> วิธีเปิดหน้าจริง: `docker compose up -d` → http://localhost:8501

## เทียบ 3 ระบบ side-by-side

| | causal-graphrag (ของเรา) | entity-graphrag (baseline) | vector-rag (baseline) |
|---|---|---|---|
| **hop** | 4 | 4 | 0 |
| **F1** | **0.77** | 0.82 | 0.40 |
| **traceable** | ✓ | ✗ | ✗ |
| #ทำนาย | 6 | 10 | 3 |
| ถูก (∈gold) | Ang Thong, Ayutthaya, Chai Nat, Nakhon Sawan, Sing Buri | 6 | Nakhon Sawan, Tak |
| เกิน (∉gold) | Pathum Thani | Bangkok, Nonthaburi, Pathum Thani | Nonthaburi |
| ตกหล่น | Phitsanulok, Tak | Phitsanulok, Tak | Ang Thong, Ayutthaya, Chai Nat, Phitsanulok, Sing Buri |

> หมายเหตุ: F1 ต่อคำถาม (นครสวรรค์) ต่างจาก F1 รวมทั้ง eval set เล็กน้อย — F1 รวม 2565 = causal **0.769** / entity 0.729 / vector 0.296. entity ต่อคำถามนี้ได้ 0.82 เพราะทำนายเกินจนบังเอิญครอบ gold แต่ traceability = 0.

## 🔗 Causal chain viewer (causal-graphrag) — เริ่มจาก *ฝน→runoff* (กลไกจริง)

```
สถานีฝนปิงตอนบน (Ping upper) ─RUNOFF_TO→ ปิงท้ายเขื่อนภูมิพล ─FLOWS_TO→ ปากน้ำโพ (Pak Nam Pho)
  ─FLOWS_TO→ เจ้าพระยาตอนบน (ปากน้ำโพ–ชัยนาท) ─INUNDATES→ Nakhon Sawan
```
ความยาวสายเหตุ-ผล = **4-hop (ข้ามลุ่มน้ำผ่านจุดบรรจบปากน้ำโพ)** — ต้นสายเป็น *ฝน* ไม่ใช่เขื่อนล้น
(ปี 2565 เขื่อนภูมิพล/สิริกิติ์กักน้ำ ไม่ได้ล้น; นครสวรรค์ท่วมจากน้ำท่า+น้ำเหนือที่ปากน้ำโพ ยืนยันด้วย C.2 = 3,099 ≥ ความจุ 2,840).

## 🧾 Evidence panel (ทุกชิ้น complete → traceable)

1. ✅ `D1/data.go.th rain→runoff`  (RUNOFF_TO)
2. ✅ `D1/data.go.th river gauge`
3. ✅ `D1/data.go.th river gauge`
4. ✅ `D4/basin+province PIP + D3/GISTDA extent`

## 🗺️ Overlay flood extent (GISTDA)
🔵 พื้นที่น้ำท่วมจริง (GISTDA + GADM)  ·  🔴 จังหวัดที่ causal-graphrag ทำนาย  ·  ม่วง = ทับกัน (ถูก)

---
**อ่านผล (ซื่อสัตย์):** causal-graphrag อธิบายนครสวรรค์ได้ถูกด้วยสาย *ฝน→runoff→ปากน้ำโพ* พร้อม evidence ครบ (traceable),
แต่ **ตกหล่น พิษณุโลก/ตาก** (ท่วมจากฝนท้องถิ่นในลุ่มย่อยที่ลำน้ำหลักไม่ล้น) และ **เกิน ปทุมธานี** (per-province
threshold ยัง tuned). entity ทำนายเกิน 10 จังหวัดแต่ traceability = 0; vector ได้แค่จังหวัดที่ข่าวรายงาน + ติด
false positive และ traceability = 0. ดู [README → Results](../README.md#-results-ผลลัพธ์) สำหรับผลรวมทั้ง 2 เหตุการณ์.
