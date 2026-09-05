# REFERENCES / Related Work

Prior work this project builds on, and how it differs. Citations are given as
title + venue/arXiv id (verify the id before formal citation). Grouped by theme.

---

## 1. GraphRAG & multi-hop retrieval (the method family)

- **RAG vs. GraphRAG: A Systematic Evaluation and Key Insights** — arXiv:2502.11371.
  Benchmarks RAG vs GraphRAG on single- and multi-hop QA; reports the gap widening with
  hop count. **This is the paper CLAUDE.md cites for H1** — our contribution is to test
  whether that hop-count effect holds for a *causal* chain, not an entity-relation chain.
- **From Local to Global: A Graph RAG Approach to Query-Focused Summarization**
  (Microsoft GraphRAG) — arXiv:2404.16130. The reference GraphRAG system; community-based,
  entity-relation graph. Our `entity-graphrag` baseline is in this family.
- **NodeRAG: Structuring Graph-based RAG with Heterogeneous Nodes** — arXiv:2504.11544.
  Heterogeneous-node graph RAG; relevant to our typed causal schema (RainStation/Reservoir/
  RiverReach/Confluence/Province).
- **Awesome-GraphRAG** (DEEP-PolyU) — https://github.com/DEEP-PolyU/Awesome-GraphRAG.
  Curated survey of GraphRAG papers/benchmarks; useful map of the space.

> **How we differ:** existing GraphRAG benchmarks traverse *entity-relation* hops
> (e.g. mosque → province → hotel). We measure hops along a *physical causal chain*
> (rain → reservoir/runoff → river reach → confluence → province) and score against an
> independent satellite ground truth — a causal, not merely relational, hop dimension.

## 2. Flood knowledge graphs, causal river-network analysis, early warning

- **Causal mechanism of extreme river discharges in the upper Danube basin network** —
  arXiv:1907.03555. Infers the causal structure of extreme discharges over a river-basin
  network. Closest in spirit to our causal-chain graph; they infer causality statistically,
  we encode it from hydrology + gate it on independent gauges.
- **A flood knowledge-constrained large language model interactable with GIS** —
  Int. J. Geographical Information Science, 2024, doi:10.1080/13658816.2024.2306167.
  Flood KG + LLM + GIS for public risk perception. Shares the KG+LLM+GIS stack; we add the
  causal-hop evaluation and traceability metric.
- **A data-driven global flood forecasting system for medium to large rivers** —
  Scientific Reports, 2024, s41598-024-59145-w (Google flood forecasting). State-of-the-art
  data-driven forecasting; complementary — our goal is *verifiable explanation*, not
  point forecasting.
- **Spatial Decision Support System for Real-Time Flood Early Warning in the Vu Gia–Thu Bon
  River Basin, Vietnam** — PMC7147717. SE-Asian basin early-warning DSS; motivates our
  lead-time / early-warning framing (§ README #6, lead_validation).

> **How we differ:** these forecast *whether/how much* it floods. We focus on *why this
> province floods* — a traceable causal chain back to source records — and quantify how
> much more verifiable that is than vector search over news.

## 3. RAG evaluation

- **RAGAS: Automated Evaluation of Retrieval Augmented Generation** — arXiv:2309.15217.
  Reference-free RAG metrics (faithfulness, context relevance). Named in CLAUDE.md's stack;
  our `src/eval/faithfulness.py` is a deterministic, reproducible grounding check in the
  same spirit (no LLM-judge), specialized to catch cross-basin geographic hallucination.
- **LlamaIndex `PropertyGraphIndex`** — https://docs.llamaindex.ai. Property-graph retriever
  framework named as the intended stack in CLAUDE.md.

## 3b. Flood early-warning: verification, probability, risk (for the /warn + lead-time work)

- **EFAS — The European Flood Alert System, Part 2** — Hydrology and Earth System Sciences
  13:141, 2009. The canonical operational probabilistic flood EWS; verifies with Brier
  skill score vs lead-time. Template for our probabilistic-warning framing.
- **Two decades of ensemble flood forecasting** — Hydrological Sciences Journal, 2021,
  doi:10.1080/02626667.2021.2023157. State-of-the-art review of probabilistic/ensemble
  flood forecasting (what a full #3/#4 would build toward).
- **NOAA Forecast Verification Glossary** — authoritative definitions of POD (probability
  of detection), FAR (false alarm ratio), CSI (critical success index), Brier score. Used
  by `src/eval/lead_validation.py` (warning skill) and `mcnemar.py`.
- **Flood Risk Assessment Based on Flood Hazard and Vulnerability Indexes** (2021) and the
  **Risk = Hazard × Exposure × Vulnerability** decomposition (UNDRR/IPCC; holistic flood-risk
  methodology, Nature Sci. Rep. s41598-025-13025-z). Basis for `src/eval/risk_warning.py`.
- Exposure data: **NSO Thailand** province population (2020 census).

> **How we differ:** we do NOT build a hydrological/ensemble forecaster. We reuse a
> *verifiable causal-retrieval* graph as an operator early-warning tool and wrap it with a
> calibrated probability (our measured precision) + the standard risk index — reporting
> honest verification skill (POD/FAR/CSI, lead-time error) rather than claiming forecast
> accuracy we did not build.

## 4. Statistics / methodology

- **McNemar's test** (McNemar, 1947) — the paired test for two classifiers on the same
  items; standard for small-N classifier comparison. Used in `src/eval/mcnemar.py` (and by
  the sibling `thai-multiteacher-opd` repo). We pair it with a paired bootstrap CI.

## 5. Data sources (primary, used in this repo)

- **GISTDA** satellite flood-area products (via thaiwater.net) — ground truth (2565/2564,
  full 53-province tables).
- **RID SWOC** river-gauge / over-bank situation bulletins — the independent overflow gate.
- **GADM 4.1** (Thailand level-1) — province geometry.
- **HII / thaiwater** 2011 mega-flood timeline — lead-time validation only (not scored;
  per-province area not published at the eval cutoff — see README Bugs).
- **data.go.th (CKAN)**, **EGAT/RID dam specs** — telemetry & reservoir specs.

Full source links + endpoint status: README → *System — All Links*.

---

### Sibling repos (same author, cross-referenced methodology)

- **thai-graphrag-benchmark** — Thai multi-hop KGQA benchmark by hop_type; fairness rules
  enforced in code. Origin of our "compare fairly, cap context" discipline.
- **thai-legal-temporal-graphrag** — temporal KG traversal to avoid citing repealed law;
  frozen-methodology + honest-limitations template our METHODOLOGY.md follows.
- **thai-multiteacher-opd** — McNemar + Holm + pre-registration discipline reused here.

---

### Forecasting improvement (Roadmap B) — เรียนรู้จากผลถูก/ผิด โดยกัน overfitting

> ดูแผน: [`docs/FORECASTING_ROADMAP.md`](FORECASTING_ROADMAP.md). หลักร่วม: แยก "โมเดลกลไก" (ตรึง) ออกจาก "ชั้นปรับ" (บาง, cross-validate, ทดสอบ prospective).

- **Aamodt & Plaza (1994)** — *Case-Based Reasoning: Foundational Issues, Methodological
  Variations, and System Approaches.* AI Communications 7(1):39–59. → รากของ **Case Bank** (คลังเคสถูก/ผิด).
- **Gama, Žliobaitė, Bifet, Pechenizkiy & Bouchachia (2014)** — *A survey on concept drift
  adaptation.* ACM Computing Surveys 46(4). → ปรับตามข้อมูลใหม่โดยไม่พัง + drift monitor.
- **Gama, Sebastião & Rodrigues (2013)** — *On evaluating stream learning algorithms.*
  Machine Learning 90(3). (+ Dawid 1984, prequential principle) → ประเมิน **prequential** (เทรนอดีต→ทดสอบอนาคต).
- **Platt (1999)** Platt scaling; **Niculescu-Mizil & Caruana (2005)** *Predicting Good
  Probabilities with Supervised Learning* (ICML); **Guo, Pleiss, Sun & Weinberger (2017)**
  *On Calibration of Modern Neural Networks* (ICML). → **ชั้น calibration บาง ๆ** พารามิเตอร์น้อย = เสี่ยง overfit ต่ำ.
- **Gneiting, Balabdaoui & Raftery (2007)** — *Probabilistic forecasts, calibration and
  sharpness.* JRSS-B 69(2):243–268. → วัด **calibration + sharpness** คู่กัน (ไม่ดันตัวเลขให้สวย).
- **Jolliffe & Stephenson (2012)** — *Forecast Verification: A Practitioner's Guide.* 2nd ed.,
  Wiley. (+ NOAA Forecast Verification Glossary) → POD/FAR/CSI, reliability, Brier.
- **Cloke & Pappenberger (2009)** — *Ensemble flood forecasting: A review.* J. Hydrology 375. →
  บริบทพยากรณ์น้ำท่วมเชิงปฏิบัติการ + post-processing.
- **Liu et al. (2012)** — *Advancing data assimilation in operational hydrologic forecasting.*
  HESS 16. → อัปเดตพยากรณ์จากข้อมูลจริง (เชิงหลักการ).

### Probabilistic warning verification (Thesis B — ทำ B ให้แข็ง)

- **Brier (1950)** — *Verification of forecasts expressed in terms of probability.* Monthly Weather
  Review 78(1):1–3. → Brier score.
- **Murphy (1973)** — *A new vector partition of the probability score.* J. Applied Meteorology 12(4).
  → **Brier decomposition** reliability − resolution + uncertainty (ใช้ในโค้ด).
- **Pappenberger, Ramos, Cloke et al. (2015)** — *How do I know if my forecasts are better? Using
  benchmarks in hydrological ensemble prediction.* J. Hydrology 522:697–713. → **Brier Skill Score
  เทียบ climatology/naïve** (กัน "naïve skill").
- **Naeini, Cooper & Hauskrecht (2015)** — *Obtaining Well Calibrated Probabilities Using Bayesian
  Binning.* AAAI. → **Expected Calibration Error (ECE)**.
- **Bröcker & Smith (2007)** — *Increasing the reliability of reliability diagrams.* Weather and
  Forecasting 22(3). → วิธีอ่าน/สร้าง reliability diagram ที่เชื่อถือได้.
- **Wilks (2011)** — *Statistical Methods in the Atmospheric Sciences*, 3rd ed. → มาตรฐาน verification.
- **WWRP/WGNE Joint Working Group on Forecast Verification** (cawcr.gov.au/projects/verification) →
  นิยาม POD/FAR/CSI, reliability, sharpness, BSS ที่ใช้อ้าง.
