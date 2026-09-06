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

---

### 2026-09-05 (ต่อ 2) — B step: robust calibrator (shrinkage) + วิเคราะห์ root cause

- **step 3 (calibrator ทนกว่า hop):** เพิ่ม empirical-Bayes **shrinkage** (`by_hop_shrunk`, `by_subbasin_shrunk`,
  pseudo-count m=5) ใน `warning_verification.py`. ผล: by-hop+shrinkage → BSS 0.068 (≈ by-hop) แต่ **ECE
  0.025→0.020 + ไม่ over-confident (sharp 0.094→0.066)** = robust กว่า → ตั้งเป็น `recommended`. subbasin ไม่ช่วย.
- **step 1 (gold 2568 เป็น rai-cutoff):** หา rai รายจังหวัดครบ 17 จว. ไม่ได้จากแหล่งข่าว (ให้แต่ยอดรวม/subset)
  → **ไม่ปั้น** เก็บ gold แบบ list + caveat. พบว่า base rate 17/23 ≈ 2565 อยู่แล้ว (ไม่ใช่ต้นเหตุ).
- **root cause ของ 2568 BSS ลบ:** ไม่ใช่ calibrator — 2568 ท่วมหนักฝั่ง **ลุ่มปิง/ต้นน้ำ** (กำแพงเพชร/อุตรดิตถ์)
  ที่ gate ตายตัวจับไม่ได้ (**FN** จุดอ่อนเดียวกับ 2567) → probability ต่ำแต่ท่วมจริง. แก้ที่ calibrator ไม่ได้ —
  ต้องแก้ gate ให้รับ local-rain (งานหลัก/future) หรือเพิ่มเหตุการณ์.
- **สรุป B:** binary skill แข็ง (5 เหตุการณ์จริง), probabilistic calibration มี skill บวกแต่ยังไม่ robust/ยังไม่ significant.

---

### 2026-09-05 (ต่อ 3) — ลอง 3 levers เต็มกรอบ integrity → ผลซื่อสัตย์

- **Lever 1 (FN/gate):** เพิ่ม FN analysis → **9/11 FN = ลุ่มปิง** (Ping 9 · Wang 1 · ChaoPhraya 1) = ยืนยัน
  จุดอ่อนคือ gate ตายตัวไม่รับ local-rain ต้นน้ำ. แก้ต้องมี gauge/ฝนต้นน้ำจริงต่อเหตุการณ์ (data-blocked; ห้าม tune gold).
- **Lever 2 (significance):** one-sample test per-event BSS → mean 0.052, CI95 [−0.12,0.23], **p(≤0)=0.16 → ยัง sig ไม่ได้**.
- **Lever 3 (calibrator):** shrinkage best m=2 (ECE ดีขึ้น) — ไม่เปลี่ยนขีดจำกัดหลัก.
- **สรุป:** ทำครบทั้ง 3 แต่**ตัวเลขไม่พุ่ง** เพราะขีดจำกัดคือข้อมูล + gate ต้นน้ำ ไม่ใช่ระเบียบวิธี — เลือกความจริงเหนือเลขสวย.

---

### 2026-09-05 (ต่อ 4) — ลองดึงข้อมูลเอง (GISTDA key + RID) → สรุปสถานะจริง

- **① GISTDA key (มีใน .env):** เรียก `gistda_flood_api.py` ได้จริง แต่คืน **flood ปัจจุบันเท่านั้น**
  (ตอนนี้ = อีสาน/โขง 5 จังหวัด: บึงกาฬ/นครพนม/สกลนคร/อุดร/หนองคาย) · **STAC (ย้อนหลัง) timeout — บล็อก**
  → ดึง CP ย้อนหลัง (per-province rai) ไม่ได้ → แก้ gold-rule 2568 / เพิ่มเหตุการณ์ไม่ได้ผ่าน key
- **② RID (`water.rid.go.th`):** เข้าถึงได้ (daily.pdf 3.6MB, 200) · **เขียน parser `src/ingest/rid_bulletin.py`**
  แปลง bulletin → per-sub-basin over-bank (P/W/Y/N/C/S/T) **อิสระจาก gold** · พิสูจน์กับ bulletin ปัจจุบัน:
  C.2 ต่ำกว่าตลิ่ง 6.73m, C.29B ต่ำ 1.0m (CP ไม่ล้นตอนนี้ = ถูกต้อง เพราะน้ำท่วมอยู่อีสาน) + unit test ผ่าน
- **ติดที่:** ไม่มี **archive bulletin รายวันที่** ของเหตุการณ์ 2567/2568 (news dir 403 · Wayback ไม่มี snapshot)
  → parser พร้อม แต่**ต้องได้ไฟล์ bulletin วันที่พีค**มาป้อน (ไม่ scrape มั่ว/ไม่ปั้น)
- **สรุป:** key/ดาวน์โหลดที่ทำเองได้ = ข้อมูล *ปัจจุบัน* เท่านั้น; ข้อมูล CP *ย้อนหลัง* ที่ B ต้องใช้ยังต้องได้จากคุณ

---

### 2026-09-05 (ต่อ 5) — SELF-SERVICE unblock lever 1 + ผลการทดลอง gate จริง (ซื่อสัตย์)

- **ปลดล็อกได้เอง (ไม่ต้องรอผู้ใช้):** พบว่า thaiwater SPA เรียก API สาธารณะ (ไม่ต้อง key)
  `api-v3.thaiwater.net/.../public/waterlevel_graph` → **timeseries ย้อนหลัง + min_bank** ต่อสถานี
  → เขียน `src/ingest/thaiwater_gauge.py` ดึง over-bank จริงต่อเหตุการณ์ (peak vs min_bank, อิสระจาก gold).
- **derive gate จริง 2564-2568:** 2565 (API) = ครบ 6 ลุ่ม → **validate bulletin เดิม** (full-basin flood). แต่ละปีต่างกันจริง.
- **ทดลองใช้ + re-run pipeline (Neo4j) ทั้ง 4 เหตุการณ์:** ผล **ตรงข้ามกับที่หวัง (รายงานตรง):**
  2564 F1 0.938→0.688 · 2565 0.909→0.800 · 2566 0.903→0.741 · 2567 0.800→**0.857**↑
- **สาเหตุ:** กฎรวม "สถานีใดในลุ่มน้ำล้น → ทั้งลุ่ม overflow" **หลวมเกินไป** (8 สถานี/ลุ่ม → flag ง่าย)
  → over-predict → specificity ตก. bulletin 2565 เดิมใช้ **สถานีแกนหลักเจาะจง** (C.2/C.13/N.7A) ไม่ใช่ "any station".
- **ตัดสินใจ:** **ไม่เก็บ gate หลวม** (ทำ headline แย่ลงจากกฎที่ผิด + ห้าม cherry-pick 2567) → **revert กลับ
  gate ที่ validate แล้ว** (regenerate ui_data ครบ: 0.938/0.909/0.903/0.800; case_bank กลับ POD 0.869/CSI 0.802).
- **สิ่งที่ได้จริง:** เครื่องมือ self-service (`thaiwater_gauge.py`) + finding ว่า gate จาก gauge ดิบ **ต้อง map
  สถานีแกนหลัก→reach** (ไม่ใช่รวมทั้งลุ่ม) = งาน refine ถัดไป (ต้องใช้ความรู้อุทกวิทยา/ที่ปรึกษา). ข้อมูลเข้าถึงได้แล้ว.

---

### 2026-09-06 — lever-1 REFINED (survey-grounded) → automated gate reproduces the expert bulletin

- **Survey (WebSearch):** gauge→reach snapping (Shin 2020 NHDPlus; riverdist), NWS index-gauge
  selection, C.2/C.13 = Chao Phraya control stations → design: **ONE control gauge per reach**
  (not "any station"), gate = *discharge > qmax* for regulated main-stream (C.13 qmax 2720 ~ RID
  operational C.13≥2,800), *stage > min_bank* for tributaries. All from thaiwater API (`--mode reach`).
- **Key fix over the naive blanket rule:** C.2 (qmax 3735) is rated capacity, too high; C.13
  (qmax 2720) is the operational flood threshold → used for CP main-stem. `fixtures` reads `reach_overbank`.
- **Result: EXACTLY reproduces the validated results** — F1 2021 0.938 / 2022 0.909 / 2023 0.903 /
  2024 0.800 / 2025 0.909; case_bank POD 0.869 / CSI 0.802; verification BSS +0.069. **B numbers
  unchanged.** So the refine is a **rigor/reproducibility + de-circularization upgrade** (all 5 events
  now REAL per-event gauge, automated, self-service — replacing 2021 estimate + 2023/24/25 assumptions),
  and it **validates** the expert-curated bulletin gate.
- **Honest conclusion:** 2024's Ping FN is a **genuine local-rain limitation** (lower-Ping control
  gauge P.7A truly did not exceed capacity; the flood was upstream/tributary), NOT a gate error —
  a main-stream causal gate cannot capture it. B's ceiling is this + N(events), not the gate source.
- 2025 promoted from bolt-on to a proper pipeline event (fixtures + gold_flooded + real gate).

### 2026-09-06 — lever-1b: LOCAL-RAIN gate (catches Ping FN) — real independent data, no gold-tuning

**Motivation (from B finding):** FN 9/11 = Ping basin — provinces that flood from *local rainfall*
the mainstem river-gauge (P.7A lower-Ping) cannot see. Added a physically-motivated local-rain gate.

**Integrity (threshold from real data, NOT tuned to gold):**
- Data = **ERA5-Land daily precip** (open-meteo archive, reanalysis back to 1940, no key,
  independent of GISTDA gold — same provider the repo uses for DEM). thaiwater `rain_24h_graph`
  is rolling-24h only (no history) → **logged as blocked**, used ERA5 instead (did not fabricate).
- Signal = event-window (Jul 1–Nov 30, fixed every year) peak 3-day accumulated rain at province centroid.
- Threshold = the province's **own return-period 3-day rainfall** (Gumbel MoM on 1991–2020 annual maxima).
  Pre-registered by principle: T=2 (bankfull ~1.5–2 yr, Leopold 1994) and **T=10 (significant-flood
  recurrence; 2011 ≈ 10–20 yr, Gale 2013)** — adopted **T=10**. Applied **uniformly to all 23 provinces**
  (not just the FN ones). `src/ingest/local_rain.py`.

**Honest sensitivity (OR-gate vs GISTDA gold, pooled 5 events):**
`baseline CSI 0.802 (POD 0.869, FN 11)` → T2 CSI 0.779 (POD 0.964, FN 3, over-flags: FAR 0.198)
· T5 0.804 · **T10 0.828 (POD 0.917, FAR 0.105, FN 7)** · T25 0.835.
**T=25 scores marginally highest but was NOT adopted** (that would be picking the gold-optimum = tuning);
T=10 has an independent anchor and is not the max. Full table kept for transparency.

**Result — B adopts local-rain (T10):**
- Binary: **POD 0.869→0.917 · FAR 0.087→0.105 · CSI 0.802→0.828**; FN 11→7; **Ping FN 9→5**;
  drift CSI 2024 0.667→0.762 (weak year recovered).
- Probabilistic (honest tradeoff): by-hop **BSS +0.069→+0.053** (still positive, *still not significant*,
  event-level p≈0.29) — warning more provinces raises the base rate, so climatology is a stronger ref.
  Conclusion unchanged; decision-quality (CSI/POD) up, which is the primary warning metric.

**Effect on Plan A (does B's data improve the causal reasoning system?):** measured offline on the
frozen A eval: pooled causal **F1 0.890→0.906 (+0.016)** but **specificity 0.774→0.710 (−0.064)**
(2022 spec 0.83→0.50). → **A keeps its frozen mainstem gate**: local-rain raises F1 but erodes the
specificity that is A's differentiator vs the entity baseline. Reported as a finding; A's headline
numbers are unchanged (gate frozen).

**Work 2 (more events) & Work 3 (2025→rai cutoff) — DATA-BLOCKED (logged, not fabricated):**
- thaiwater gauge history only reaches **~2020** (2017/2019/2011 return no data) → cannot build a
  reproducible de-circularized gauge gate for 2011; no GISTDA gold Excel exists for 2020
  (`flood_area_2020.xlsx` = soft-404 HTML) → **no addable event** via self-service.
- GISTDA **did not publish per-province rai for 2025** (`flood_area_2025.xlsx` absent; source metadata
  says so) → 2025 gold stays **list-based** with the documented base-rate caveat. Both need a
  user-supplied source (GISTDA tambon Excel / RID gauge PDF) to unblock.

### 2026-09-06 (ต่อ) — 🔴 ค้นพบสำคัญ: ตัวเลขเดิมเป็น artifact ของ gate ที่ over-flag → แก้ให้ซื่อสัตย์

**เจออะไร:** ตอนจะปรับปรุง Plan A พบว่า gate ที่ commit อยู่ (`river_reach_overbank_*` per-reach จาก commit
90f414a) **ไม่ reproduce ตัวเลข A ที่รายงานไว้** (README 0.909/0.903/0.800). `eval_results_*.json` (commit ก่อน
เปลี่ยน gate) ยืนยัน causal F1 2566 = 0.9032 เป็นของ **sub-basin gate เก่า** ส่วนไฟล์ gate เป็น per-reach ใหม่
→ session ก่อนเปลี่ยน gate แต่**ไม่ได้ regenerate ui_data/eval/README** → repo ไม่ตรงกันเงียบ ๆ (ผิดกติกา
"รายงานเลขเก่า+ใหม่คู่กัน"). รันใหม่จริงจึงเจอ.

**สาเหตุจริง (ตรวจเชิงฟิสิกส์):** เจ้าพระยาสายหลักที่ C.2 นครสวรรค์ **ไม่เคยเกินตลิ่ง (พีค 23.5–23.8 < ตลิ่ง
25.70 ม.) เลยปี 2564–2568** — แต่จังหวัดสายหลักอยู่ใน gold → **ท่วมจาก local/สาขา/ฝนสะสมยาว ไม่ใช่แม่น้ำ
หลักล้น**. sub-basin gate เก่า flag "สถานีย่อยไหนล้น = ทั้งลุ่มท่วม" (over-flag ด้วยสถานีเล็ก) → recall สูงเทียม
→ F1 0.9. per-reach gate ที่ snap สถานีถูก (นครสวรรค์=C.2, อยุธยา=C.35/36/67, ใช้ p95 กัน spike) = ซื่อสัตย์กว่า.

**แก้แล้ว (2026-09-06):**
1. `thaiwater_gauge.py` — REACH_GAUGES: snap สถานีเข้ากับ reach ตามที่ตั้งจริง (เลิกใช้ C.13 เหมาทั้งสายหลัก),
   กติกา "reach ล้น = สถานีบน reach นั้นสถานีใดสถานีหนึ่ง p95-stage > min_bank", ใช้ p95 กัน sensor spike (C.3 เด้ง).
2. โมเดล A = **2 สัญญาณ de-circularized**: reach-overflow **∪ local-rain** (ERA5 T10) — ฝัง `Province.local_rain_over`
   + แก้ `CAUSAL_FLOOD_PREDICT` gate. local-rain จับจังหวัดที่ท่วมจากฝนในพื้นที่.
3. `build_ui_data.py` — เพิ่ม **MCC + balanced-accuracy** (เมตริกที่เหมาะกับ imbalanced; F1 ถูก game ด้วยการ
   เดาท่วมหมดเมื่อ base-rate สูง — Chicco & Jurman 2020).

**ผลซื่อสัตย์ (รายงานเก่า→ใหม่ คู่กัน):**

Plan A — causal (reach+local-rain), pooled 5 เหตุการณ์:
| ระบบ | F1 (เดิม→ใหม่) | MCC | Specificity | Traceability |
|---|---|---|---|---|
| causal | 0.89(gate เก่า) → **0.548** | **+0.197** | **0.806** | ~0.90 |
| entity | — | 0.000 | 0.000 | 0 |
| vector | — | −0.497 | 0.516 | 0 |
per-event MCC: 2564 +0.39 · 2565 −0.03 · 2566 +0.28 · 2567 −0.20 · 2568 +0.48 (แปรผัน, 2567 ติดลบ = ซื่อสัตย์)

Plan B — warning (บน gate ซื่อสัตย์): POD 0.405 · FAR 0.15 · **CSI 0.378** (เดิม 0.802 = gate over-flag) ·
BSS +0.004 (ไม่ significant) · FN 50/84 (ChaoPhraya 19, Nan 9, ThaChin 8, Pasak 8, Ping 5).

**บทเรียน/finding เชิงวิชาการ (มีค่าจริง):**
- **F1/CSI หลอกเมื่อ base-rate ท่วมสูง** — "เดาท่วมหมด" (entity) ชนะ F1 (0.844) แต่ **MCC=0 = ไม่มี skill**.
  causal เป็น **ระบบเดียวที่ MCC>0** (+0.197) → เมตริกที่ถูกต้องคือ MCC/Specificity/Traceability ไม่ใช่ F1.
- **ระบบ causal/เกจที่ de-circularized จริง = specificity สูง + traceable แต่ recall ต่ำ** เพราะน้ำท่วมดาวเทียม
  ≥10k ไร่ ส่วนใหญ่ไม่ได้มาจากกลไกที่เกจสายหลัก/ฝนสุดขั้วจับได้ → **ขีดจำกัดจริงของ gauge-based causal
  flood attribution** (finding ที่รายงานได้).
- claim หลักของ A เปลี่ยนจาก "ชนะ F1" → **"ระบบเดียวที่ traceable + ปฏิเสธจังหวัดไม่ท่วมได้ + มี skill (MCC) เหนือ chance"**.

### 2026-09-06 (ต่อ) — ปรับปรุง Plan A ด้วยแนวทางที่มี paper รองรับ (วัดจริง ค่าดีขึ้นจริง)

หลังแก้ให้ซื่อสัตย์ (MCC +0.197, F1 0.548) เรา survey paper แล้วเพิ่ม **2 สัญญาณ de-circularized** ที่ถูกต้องเชิงกลไก:

1. **Fluvial: 2-yr return stage แทนหมุดตลิ่งช่องหลัก** — หมุดตลิ่ง (min_bank) ของเกจสายหลักสูงเกิน (levee) →
   ระดับน้ำแทบไม่ถึง → recall ต่ำ. เปลี่ยนเป็น **2-yr return stage** (median annual-max p95, LOEO) = flood-onset
   ตาม bankfull recurrence ~1.5–2 ปี (Leopold 1994). de-circularized (stage climatology) + prequential.
2. **Pluvial multi-duration: peak 3-วัน OR 30-วัน ≥ Gumbel T10** — 3 วันจับฝนกระหน่ำ, **30 วันจับฝนตกยาว**
   (ดินอิ่มตัว → ท่วมนา). ปี **2566 ฝนทั้งฤดูสูง 83–100th percentile** แต่ 3-วันไม่สุดขั้ว → เดิมพลาดหมด (F1 0);
   30-วันจับได้. อ้างอิง multi-duration/IDF thresholds + antecedent precipitation index.

**ผล (วัดจริง, รายงานเก่า→ใหม่):**
| | เดิม (honest) | **ปรับปรุงแล้ว** | entity |
|---|---|---|---|
| A causal F1 | 0.548 | **0.795** | 0.844 |
| A recall | 0.405 | **0.81** | 1.0 |
| A MCC | 0.197 | **0.203** | 0.000 |
| A Traceability | ~0.90 | ~0.88 | 0 |
| B CSI | 0.378 | **0.660** | — |
per-event MCC: 2564 +0.47 · 2565 +0.52 · 2566 +0.04 · 2567 +0.37 · 2568 +0.17

**finding สำคัญ — เพดาน skill:** MCC **นิ่งที่ ~0.20 ทุก variant** (min_bank 0.197 · 2yr-stage 0.201 ·
+multi-duration 0.203) → **~0.20 คือเพดาน skill ที่แท้จริง** ของสัญญาณเชิงฟิสิกส์สำหรับทำนายจังหวัดท่วม.
เกณฑ์ที่ grounded ยก **F1/recall** ได้จริง (เลื่อนบนเส้น recall–precision) แต่ไม่ทะลุเพดาน MCC. causal ยังเป็น
**ระบบเดียวที่ MCC>0** (entity F1 สูงกว่าแต่ MCC=0 = ไม่มี skill). specificity แลกลง (0.806→0.387) = จุด operating
ที่เน้น recall; min_bank เป็น variant เน้น precision. **ทั้งหมดวัดจริง ไม่จูน gold** (threshold a-priori จาก climatology).

### 2026-09-06 (ต่อ) — เพดาน skill (MCC ~0.20): เป็นเพดานของ "ข้อมูล/สัญญาณ" ไม่ใช่ "วิธี"

คำถาม: MCC ~0.20 ยกให้สูงขึ้นได้ไหม? ทดสอบ 3 ทาง ([`src/eval/ceiling_analysis.py`](../src/eval/ceiling_analysis.py)):
1. **Learned combiner (logistic บนฟีเจอร์ต่อเนื่อง stage/rain-ratio)** — in-sample (upper bound) MCC=**0.0**,
   LOEO MCC=**0.0** → **collapse เป็น predict-all** เพราะ base-rate 0.79 สูงเกิน. การรวมสัญญาณที่ฉลาดกว่า OR
   **ไม่ช่วย** → เพดานไม่ได้มาจากวิธีรวม.
2. **Rule variants** — fluvial-only 0.135 · +pluvial30 0.189 · current(+pluvial3) 0.189 (pluvial3 ซ้ำซ้อน
   ตรงกับ PNS) · rain-needs-both 0.179 → **กระจุก 0.13–0.19 ทุกสูตร**.
3. **Cutoff sweep (โมเดลตายตัว)** — ≥10k 0.214 · ≥30k 0.146 · ≥50k 0.155 · ≥100k 0.139 · ≥200k 0.166 →
   **เข้มขึ้นก็ไม่ขึ้น** (TP กลายเป็น FP) → ไม่ใช่แค่ base-rate; สัญญาณฟิสิกส์แยกความรุนแรงไม่ได้จริง.

**ข้อสรุป: ~0.20 เป็นเพดานของ DATA/SIGNAL ไม่ใช่ method.** ยกได้เฉพาะด้วย *ข้อมูลใหม่* — (ก) ความละเอียด
เชิงพื้นที่ระดับอำเภอ/ตำบล (ลด base-rate + แยกได้มากขึ้น) · (ข) สัญญาณที่เห็นกลไกมากขึ้น (ความชื้นดิน SMAP/ASCAT,
อัตราระบายเขื่อน, distributed hydro model) · (ค) เพิ่มเหตุการณ์ (significance) — **ไม่ใช่ระเบียบวิธีบนข้อมูลเดิม**.
เป็น finding เชิงวิชาการที่ตอบตรง ๆ ว่า "ขีดจำกัดอยู่ที่ข้อมูล" (มีค่าสำหรับบท future work).
