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
