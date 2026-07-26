# KICKOFF PROMPT — Thai Flood Causal-Chain GraphRAG

วางบล็อกด้านล่างเป็นข้อความแรกใน Claude Code (ใน repo นี้). Claude Code จะอ่าน `CLAUDE.md` เป็นบริบทอัตโนมัติ.
Paste the block below as your first message in Claude Code (inside this repo).

---

## ▶️ Kickoff prompt (copy จากบรรทัดนี้ลงไป)

```
คุณคือ research engineer ของโปรเจกต์ "Thai Flood Causal-Chain GraphRAG".
อ่าน CLAUDE.md และ .claude/skills/ ให้ครบก่อนเริ่ม แล้วยึด stack/schema/workflow ตามนั้น.

เป้าหมายงานวิจัย:
วัดว่า GraphRAG ที่เดินตาม "สายเหตุ-ผลจริง" (ฝนต้นน้ำ → ระดับน้ำเขื่อน → น้ำล้นสปิลเวย์
→ ระดับน้ำแม่น้ำท้ายน้ำ → น้ำท่วมจังหวัดปลายน้ำ) ให้คำอธิบายที่ traceable/verify ได้
มากกว่า vector search บนข่าวน้ำท่วมแค่ไหน — วัดด้วย F1 แยกตามความยาว causal chain
(2-hop เขื่อนเดียว vs 4-hop ข้ามลุ่มน้ำ). เทียบ 3 ระบบ: causal-graphrag (ของเรา),
entity-graphrag (baseline relational), vector-rag (baseline). ground truth = flood extent
จริงจาก GISTDA.

ทำเป็นเฟส commit ทีละขั้น และหยุดให้ฉันรีวิวท้ายแต่ละเฟส:

เฟส 0 — Scaffold
- สร้างโครงตาม repo layout ใน CLAUDE.md, docker-compose (Neo4j), .env.example,
  requirements.txt, pytest skeleton.

เฟส 1 — Ingest (src/ingest)
- เขียน connector สำหรับ D1 data.go.th (CKAN), D2 thaiwater API, D3 GISTDA STAC,
  D4 basin/province geometry. ยืนยัน endpoint จริงก่อน แล้วอัปเดตตาราง "System All Links"
  ใน README. กติกาเหล็ก: ทุก edge ต้องแนบ property evidence (station id + timestamp + dataset).

เฟส 2 — Geo (src/geo)
- ใช้ skill geo-basin-to-province ทำ point-in-polygon จับคู่ลุ่มน้ำ → จังหวัดท้ายน้ำ,
  reproject ทุกชั้นเป็น EPSG เดียว, สร้าง INUNDATES edges. เขียน unit test.

เฟส 3 — Graph (src/graph)
- โหลดเข้า Neo4j ตาม schema, เขียน Cypher variable-length -[:*2..4]-> สำหรับวัด hop.

เฟส 4 — Retrievers (src/rag)
- causal_graphrag.py (LlamaIndex PropertyGraphIndex), entity_graphrag.py, vector_rag.py
  (FAISS/Chroma บนข่าว). อินเทอร์เฟซเหมือนกันเพื่อเทียบกันได้.

เฟส 5 — Eval (src/eval)
- build_eval_set.py: สร้างชุดคำถาม "ทำไมจังหวัด X ท่วม" ที่ label ด้วย GISTDA ground truth
  และ tag ความยาว chain (2-hop/4-hop). f1_by_hop.py: F1 แยก hop + traceability score.
- กรอกตาราง Results ใน README ด้วยตัวเลขจริง (ห้าม hardcode).

เฟส 6 — Test UI (ui/app.py, Streamlit)
- หน้า "ทำไมจังหวัดนี้ถึงน้ำท่วม": เลือกจังหวัด+ช่วงเวลา, เทียบ 3 ระบบ side-by-side,
  causal chain viewer, evidence panel (คลิก edge เห็น source), overlay flood extent GISTDA,
  ตัวชี้วัดสด (hop, F1, traceability). เก็บ screenshot ใน docs/ แล้วลิงก์ใน README.

ตลอดงาน:
- log ทุก bug และ aha moment ลงตารางใน README ทันทีที่เจอ.
- อย่าเขียนข้อสรุปวิจัยจนกว่าจะมีตัวเลข eval จริง.
- ถ้าข้อมูลจริงติดปัญหา (endpoint เปลี่ยน/ล่ม) ให้ทำ fixture ตัวอย่างเล็ก ๆ ต่อได้ก่อน
  แล้วบันทึกใน Bugs.

เริ่มที่เฟส 0 แล้วสรุปแผนสั้น ๆ ก่อนลงมือ.
```

---

## 🔁 คำสั่งลัดต่อเนื่อง / Handy follow-ups
- `"ต่อเฟส N"` — ทำเฟสถัดไปตามแผนข้างบน.
- `"อัปเดต Results จาก eval ล่าสุด"` — รัน `src/eval/f1_by_hop.py` แล้วเติมตาราง README.
- `"บันทึก aha: <ข้อความ>"` — เพิ่มแถวใน Aha Moments.
- `"ตรวจ traceability"` — เช็คว่าทุก edge มี evidence และ retriever ชี้กลับ source ได้.

## ✅ เกณฑ์รับงานแต่ละเฟส
เฟสถือว่าเสร็จเมื่อ: มี test ผ่าน, commit แล้ว, และ (ถ้าเกี่ยว) README section ถูกอัปเดตด้วยของจริง.
