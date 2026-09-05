# HISTORY — how the numbers got here (full transparency log)

The README keeps the *current* results clean. This file preserves the honest journey:
every time a number changed, what changed it, and whether it helped or hurt. Nothing is
hidden — the point of the project is that the causal F1 *fell* when fixtures were replaced
by real data, then recovered on correct structure, and we report each step.

## The F1 journey (causal-graphrag)

`1.000 (fixture, tuned)` → `0.800 (real dam specs)` → `0.545 (real GISTDA ground truth, N=10)`
→ `0.769 (runoff path + real river-gauge, N=10)` → `0.833 (2021 event, N=10)`
→ `0.909 / 0.938 (full 8-sub-basin basin, N=23)`

The drop to 0.545 is the most important number: it is the truth the tuned fixture hid.

## Milestones

**Item 1 — de-circularize dam status (F1 1.000 → 0.800).** `spillway`/`active` moved from
values tuned to match the gold, to real EGAT/RID specs + observed 2022 status
(`dam_specs.json`). Real data showed Bhumibol/Sirikit were *retaining*, not spilling — so a
dam-overflow-centric chain could no longer reach the confluence provinces. Proof the old
1.000 was self-serving.

**Item 2 — real vector corpus (194 news, was 8).** vector-rag F1 stayed ~0.25 and its
false positives *grew* — confirming vector's weakness here is structural ("answers the
loudest news"), not a small-corpus artifact.

**Item 3 — real GISTDA ground truth + real GADM geometry (F1 → 0.545).** Gold became the
GISTDA satellite ≥10,000-rai provinces. causal became the *lowest* graph method (0.545 <
entity 0.729) because the schema lacked the rain→runoff path that actually drove the 2022
flood. Real data exposed a real schema gap.

**Item 3½ — add RUNOFF_TO + real river-gauge gate (F1 0.545 → 0.769).** Added the
rain→runoff→river path (bypassing dams) and gated reaches on real RID gauge capacity
(C.2/C.13 over capacity; Ping P.7A under). causal recovered the confluence provinces via
the real mechanism and legitimately re-passed entity — driven by data, not fixtures.

**Item 4 — second event (2021 Dianmu).** Real per-province GISTDA table for 2021 →
`ground_truth_2021.json`. Per-event (not averaged): causal 0.769 (2022) / 0.833 (2021),
leading on F1 and decisively on traceability. Generalizes across events.

**2026-09-03 — full Chao Phraya basin (N 10 → 23, 8 sub-basins).** Graph expanded to the
real Ping/Wang/Yom/Nan/Sakae Krang/Pasak/Tha Chin/Chao Phraya structure over 23 in-basin
provinces; gold from the full 53-province GISTDA tables at the same cutoff; reach.overflow
from the independent RID SWOC gauge bulletin. causal F1 0.769→0.909 (2022) / 0.833→0.938
(2021); expanding N exposed entity's predict-everything weakness (F1 fell to ~0.64,
specificity 0). Paired P(causal>entity) 0.32→0.80/0.96.

**2026-09-04 — significance, faithfulness, topology, lead-time.** McNemar (causal>vector
p<0.001; causal>entity one-sided p=0.029); deterministic explanation-faithfulness; topology
grounded in real confluences + validated (DAG, sub-basin-consistent) + DEM-validated
(Copernicus, every flow edge downhill) + pysheds flow-accumulation (accumulation grows
downstream; Tha Chin confirmed a distributary three independent ways); lead-time validated
against the 2011 timeline (Spearman ρ 0.02→0.76 after finer main-stem stations with
real-distance lags).

## Full bug / integrity log

| Date | Symptom | Root cause | Fix | Affected results? |
|---|---|---|---|---|
| 2026-07-26 | Neo4j default ports taken | other containers hold 7474/7687(+backup) | host ports 7476/7689 | no |
| 2026-07-26 | Neo4j rejects map property on `evidence` | props are primitive/array only | store `evidence` as a JSON string | no (traceability intact) |
| 2026-07-26 | `api.thaiwater.net/v1` → 404 | API path/host changed | use `dam_specs.json` + RID gauges | no |
| 2026-07-26 | GISTDA STAC unreachable (000) | no public STAC endpoint | use GISTDA-via-thaiwater product | resolved (real gold obtained elsewhere) |
| 2026-07-26 | Windows cp874 UnicodeEncodeError | Thai console encoding | run with `PYTHONUTF8=1` | no |
| 2026-07-26 | PIP double-counts provinces | synthetic province boxes overlapped | real GADM polygons + ≥50% overlap | no |
| 2026-07-27 | Threshold circularity (F1=1.000) | `active`/threshold tuned to gold | dam specs from EGAT/RID | **yes (proved old result self-serving)** |
| 2026-07-27 | Schema mis-attribution (no rain→runoff) | chain assumed dam overflow | added RUNOFF_TO (Item 3½) | **yes (root cause of recall)** |
| 2026-07-27 | hop-tag drifted per event | HOP query filtered `active` | structural hop (no active filter) | no (fixes comparability) |
| 2026-07-27 | Sentinel-1 via GEE not runnable | needs OAuth/GEE account | GISTDA satellite product instead | no |
| 2026-07-27 | daily gauge ≠ satellite extent | gauge is an instant; water lingers | gate on main-channel over-capacity | no (physical limit, reported) |
| 2026-09-03 | Docker Desktop dies mid-session | flaky host daemon | relaunch + `compose up`, poll bolt | no (env only) |
| 2026-09-04 | 2011 mega-flood not addable | only regional aggregates published; would need hand-assigned gold; also near-universal flooding is less discriminating | not faked; pooled 2022+2021 for power instead | no (chose not to fabricate) |

## Known limitations that remain (current)

- **N is still modest (23/event, 46 pooled).** causal>entity is significant one-sided
  (McNemar p=0.029) and P=0.97 by bootstrap, but two-sided sits at the 95% boundary.
- **Graph node/edge is hand-built** from real hydrology — DEM-validated (flow direction +
  flow-accumulation) but not yet auto-delineated by a full gridded flow-accumulation.
- **2021 reach.overflow is medium-confidence** (no independent 2021 RID bulletin).
- **Lead-time** captures downstream ordering (ρ≈0.76) but the 2011 basin filled partly
  non-sequentially, which a downstream-ordered model cannot fully reproduce.
- **Tha Chin / Samut Prakan / Samut Sakhon** not itemized in some source tables.

---

### 2026-09-05 — Roadmap B (forecasting) strengthened + verified

- **Survey ก่อนลงมือ** (WebSearch) → เลือกวิธี: Murphy(1973) Brier decomposition · BSS vs climatology
  (Pappenberger 2015) · ECE (Naeini 2015) · Platt ปลอดภัยกว่า isotonic เมื่อข้อมูลน้อย (Niculescu-Mizil 2005).
- **สร้าง** `src/eval/{case_bank,calibration,warning_verification}.py` — เก็บเคสถูก/ผิด (92 เคส: POD 0.866 /
  FAR 0.094 / CSI 0.795), calibrate ความน่าจะเป็นแบบ LOEO (prequential, ไม่แตะกราฟ/gate).
- **ผลหลัก:** calibrate ตาม causal-hop มี skill (**BSS +0.147**, Brier 0.086→0.0725) ขณะค่าคงที่/climatology ไม่มี.
- **แก้วิธี CI:** case-level bootstrap [−0.38,0.34] (ผิดวิธี เพราะ province-cases correlated) →
  **event-level cluster bootstrap [0.07,0.29]** + per-event LOEO ทุกเหตุการณ์ BSS>0 (skill คงเส้นคงวา).
  หมายเหตุซื่อสัตย์: **4 clusters ยังน้อยเกินเคลม significance มั่นใจ** → ต้องเพิ่มเหตุการณ์.
- **prospective log:** `add_prospective()`/`resolve_prospective()` — log คำเตือนก่อนรู้ผล + เติมผลภายหลัง
  (ทางเดียวที่ทำให้ N โต/CI แคบอย่างซื่อสัตย์). **ไม่ scrape ข้อมูลปีใหม่แบบมั่ว** (ไม่มีข้อมูลจริงในเครื่อง = ไม่ปั้น).
- **drift monitor:** CSI 2021→2024 = .882/.833/.824/.667 (จับการเสื่อมปี 2567). track-record ในหน้า `/warn`.
- อ้างอิงเพิ่ม: ดู `docs/REFERENCES.md` (Probabilistic warning verification). สรุปเตรียมเล่ม: `docs/THESIS_B_SUMMARY.md`.

---

### 2026-09-05 (ต่อ) — เพิ่มเหตุการณ์จริงที่ 5 (เจ้าพระยา 2568) → ผลซื่อสัตย์กว่า

- **แหล่งจริง (WebSearch/WebFetch):** GISTDA satellite ผ่าน Nation Thailand — เจ้าพระยา 2568 (ภาพ 11 พ.ย. 2568)
  2,441,484 ไร่ · **17 จังหวัด** (Ayutthaya, Nakhon Sawan, Suphan Buri, Phichit, Sukhothai, Phitsanulok,
  Lopburi, Nakhon Pathom, Chai Nat, Ang Thong, Sing Buri, Uthai Thani, Kamphaeng Phet, Uttaradit,
  Nonthaburi, Phetchabun, Pathum Thani). src: nationthailand.com/news/general/40058106
- **เพิ่มอย่างถูก protocol (`src/ingest/add_gistda_2025.py`):** gate ตายตัวจาก 2022 (out-of-sample,
  เหมือน 2023/2024 ที่ verified ว่า predicted set เท่ากันเป๊ะ) · gold = รายชื่อจังหวัดทางการ (บทความไม่ให้
  ไร่รายจังหวัด → gold หยาบกว่า cutoff ≥10k ไร่ = บันทึกเป็น caveat). **ไม่ปั้น overflow/prediction.**
- **2568 เดี่ยว:** TP15/FP1/FN2/TN5 → CSI 0.833 (binary ดี)
- **ผลรวม 5 เหตุการณ์ (115 เคส):** POD 0.869 · FAR 0.087 · CSI 0.802
- **แต่ probabilistic BSS ตก:** +0.147 (4 เหตุการณ์) → **+0.069 (5 เหตุการณ์)**; 2568 per-event BSS **−0.322**
  → **การเพิ่มข้อมูลจริงเผยว่า calibration ยังไม่ robust** (4 เหตุการณ์เดิมดูดีเกิน) — รายงานตรง ไม่ revert
  (คู่ขนานกับบทเรียน F1 1.000→0.545: ยิ่งใช้ข้อมูลจริง ยิ่งเห็นความจริง)
- **prospective log CLI** พร้อมใช้ (`--log`/`--resolve`) — ไฟล์ prospective ว่างไว้ (ไม่ ship demo ที่อาจเข้าใจผิด)
