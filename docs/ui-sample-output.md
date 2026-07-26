# Test UI — ตัวอย่างผลจริงจากหน้าจอ

จับจากหน้า Streamlit `http://localhost:8501` (รันในคอนเทนเนอร์ `thaiflood-app`)
คำถาม: **"ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วมในเหตุการณ์ลุ่มเจ้าพระยาปี 2565?"**
Ground truth (gold): Ang Thong, Ayutthaya, Chai Nat, Nakhon Sawan, Pathum Thani, Sing Buri

> วิธีเปิดหน้าจริง: `docker compose up -d` → เปิด http://localhost:8501
> (จับภาพหน้าจอเก็บเป็น `docs/ui-why-flood.png` ได้จากเบราว์เซอร์)

## เทียบ 3 ระบบ side-by-side

| | causal-graphrag (ของเรา) | entity-graphrag (baseline) | vector-rag (baseline) |
|---|---|---|---|
| **hop** | 4 | 3 | 0 |
| **F1** | **1.00** | 0.75 | 0.25 |
| **traceable** | ✓ | ✗ | ✗ |
| latency | 686.9 ms | 348.3 ms | 5.1 ms |
| #ทำนาย | 6 | 10 | 2 |
| ถูก (∈gold) | ทั้ง 6 จังหวัด | 6 | Nakhon Sawan |
| เกิน (∉gold) | — | Bangkok, Nonthaburi, Phitsanulok, Tak | Bangkok |
| ตกหล่น | — | — | Ang Thong, Ayutthaya, Chai Nat, Pathum Thani, Sing Buri |

## 🔗 Causal chain viewer (causal-graphrag)

```
เขื่อนภูมิพล (Bhumibol) → ปิงท้ายเขื่อนภูมิพล → ปากน้ำโพ (Pak Nam Pho)
  → เจ้าพระยาตอนบน (ปากน้ำโพ–ชัยนาท) → Nakhon Sawan
```
ความยาวสายเหตุ-ผล = **4-hop (ข้ามลุ่มน้ำผ่านจุดบรรจบปากน้ำโพ)**

## 🧾 Evidence panel (ทุกชิ้น complete → traceable)

1. ✅ `D2/thaiwater dam_daily`
2. ✅ `D1/data.go.th river gauge`
3. ✅ `D1/data.go.th river gauge`
4. ✅ `D4/basin+province PIP + D3/GISTDA extent`

## 🗺️ Overlay flood extent (GISTDA)
🔵 พื้นที่น้ำท่วมจริง (GISTDA)  ·  🔴 จังหวัดที่ causal-graphrag ทำนายว่าท่วม (ตรงกันทั้ง 6)

---
**อ่านผล:** causal-graphrag ตอบตรง gold ทั้งหมดพร้อมหลักฐานครบ ขณะที่ entity-graphrag
เกิน 4 จังหวัด (รวมจังหวัดต้นน้ำ Tak/Phitsanulok ที่ไม่ท่วม) และ vector-rag ได้แค่
Nakhon Sawan + ติด Bangkok ผิด แล้วตกหล่นจังหวัดปลายสายอีก 5 จังหวัด.
