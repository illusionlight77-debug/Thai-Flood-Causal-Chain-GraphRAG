<!--
============================================================================
AI FIRST-DRAFT (Step 1 of the 5-step integrity loop) — REWRITE BEFORE USE
============================================================================
Per docs CLAUDE.md / research-paper-integrity SKILL.md:
  Step 1 DRAFT (this file, by AI)  ->  Step 2 REWRITE (you, in your own words,
  without looking at this draft)  ->  Step 3 MEASURE 5-gram overlap (<20%; and
  again excluding proper nouns/numbers/terms)  ->  Step 4 POLISH grammar only
  ->  Step 5 DISCLOSE in Acknowledgment.
This draft is a scaffold of *facts you have verified*. It is NOT final wording.
Do NOT paste it into the template as-is. Rewrite each paragraph from the fact
list, then paste. IEEE style names are noted in [brackets] for the .docx template.
Every number below traces to a real result file — see the traceability table at
the end (Appendix N). If a number is not in a file, it is NOT in this draft.
============================================================================
-->

# [papertitle] Verifiable, Not Just Accurate: Faithfulness and a Predictability Ceiling in Causal-Chain GraphRAG for Provincial Flood Attribution

*(Alternative shorter title options — pick one and rewrite:*
*"Causal-Chain GraphRAG for Traceable Flood Attribution in the Chao Phraya Basin";*
*"When F1 Misleads: Faithful Flood Attribution and Its Data Ceiling".)*

**[Author]** *(one author block; fill per template — name, dept., organization, city, country, email)*

---

## [Abstract]

Abstract— Retrieval-augmented systems for flood question answering are usually judged by predictive accuracy, but a correct answer is not necessarily a *verifiable* one. We study whether a GraphRAG system that traverses a real hydrological causal chain (rainfall → reservoir → river reach → downstream province) produces flood explanations that are more traceable to evidence than an entity-relation graph baseline or a vector-retrieval baseline over news. On five real Chao Phraya flood events (2021–2025; 23 provinces; 115 province-cases) scored against GISTDA satellite ground truth, the causal system attains a Matthews correlation coefficient (MCC) of +0.203 and near-complete evidence traceability (~0.90), and is the only system with skill above chance: the entity baseline reaches a higher F1 (0.844 vs. 0.795) purely by predicting almost every province flooded, yet its MCC is 0.000 and its specificity is 0. We show, using a de-circularized gate whose thresholds are drawn from gauge and rainfall climatology rather than from the ground truth, that a counterfactual necessity/sufficiency (PNS) analysis quantifies the contribution of each causal mechanism, and that agreement among mechanisms raises precision from 0.782 to 0.833. Finally, three independent tests (a learned combiner, a rule-variant sweep, and a ground-truth-cutoff sweep) plus a soil-moisture probe show that the ~0.20 MCC is a *data/signal* ceiling rather than a method ceiling: the residual missed floods are consistent with hydraulic backwater rather than soil saturation. We report where our method loses, and we disclose the correction of an earlier over-flagging evaluation that had inflated F1.

*(Rewrite target: 150–200 words, one paragraph, IEEE Abstract style.)*

## [Keywords]

Keywords— GraphRAG; flood attribution; causal graph; faithfulness; Matthews correlation coefficient; de-circularized evaluation; probability of necessity and sufficiency; Chao Phraya basin

---

## [Heading1] I. Introduction

**Facts the rewrite must contain:**
- Flood QA / early-warning systems are typically evaluated on predictive accuracy (F1/CSI), but for decision support the *verifiability* of the explanation matters: a user (or committee) needs to trace "why is this province predicted to flood?" back to evidence.
- Correctness ≠ faithfulness in retrieval-augmented generation [ref: arXiv:2412.18004]: a system can be right for untraceable reasons.
- Our contribution is a causal-chain GraphRAG whose every edge carries an `evidence` property, so every prediction is traceable; and an honest, de-circularized evaluation that shows *what such a system can and cannot do*.
- Contributions (state plainly): (1) a causal-chain GraphRAG for provincial flood attribution with 100% edge-level evidence traceability; (2) an evaluation showing that at high flood base rates F1 is gamed by a trivial "predict-all" baseline, so MCC/specificity/traceability are the appropriate criteria; (3) a counterfactual PNS analysis of each hydrological mechanism; (4) an empirical demonstration that the achievable skill (~0.20 MCC) is a *data* ceiling, with the residual floods attributable (hypothesis) to hydraulic backwater; (5) a transparent account of correcting an over-flagging evaluation artifact.
- H1: causal traversal yields more verifiable explanations than baselines. H2: quality does not degrade with causal-chain length (hop count).

*(Do not claim "more accurate." Claim "more verifiable / only system with skill.")*

## [Heading1] II. Related Work

**Facts / citations to place (use only the refs in docs/REFERENCES.md that you can actually cite):**
- GraphRAG and multi-hop retrieval [ref: GraphRAG survey / arXiv:2502.11371].
- Faithfulness/attribution evaluation in RAG; correctness ≠ faithfulness [arXiv:2412.18004].
- Causal graphs over river networks [ref: Danube causal, arXiv:1907.03555]; flood knowledge graphs + LLM + GIS [ref: IJGIS 2024].
- Evaluation of imbalanced classification: MCC over F1/accuracy [Chicco & Jurman 2020].
- Counterfactual necessity/sufficiency and feature attribution [Pearl; FANS, arXiv:2402.08845].
- Hydrology: bankfull discharge recurrence ~1.5–2 yr [Leopold 1994]; return-period rainfall / Gumbel frequency analysis; 2011 Chao Phraya flood return period [Gale 2013]; probability calibration with small data [Niculescu-Mizil & Caruana 2005].

*(One paragraph per cluster; every citation must appear in the reference list and vice versa.)*

## [Heading1] III. System and Method

### [Heading2] A. Causal Graph
- Node types: RainStation, Reservoir, RiverReach, Confluence, Province. Directed edges follow flow direction: FEEDS, RUNOFF_TO, OVERFLOWS_TO, FLOWS_TO, INUNDATES.
- Every edge stores an `evidence` property (source station, dataset, timestamp) as a JSON string; this is the basis of the traceability claim. Hop count = shortest causal path from a rainfall source (variable-length 2–8).
- Scope: 8 Chao Phraya sub-basins, 23 provinces.

### [Heading2] B. De-circularized Prediction Gate
A province is predicted to flood if (fluvial ∪ pluvial) AND it is not dike-protected:
- **Fluvial (2-year return stage).** Each reach is snapped to the gauge physically on it (e.g., Nakhon Sawan → C.2, Sing Buri → C.3, Ayutthaya → C.35/C.36/C.67). The reach over-tops if its p95 stage (95th percentile, to suppress sensor spikes) exceeds the gauge's own 2-year return stage (median annual maximum, leave-one-event-out). Rationale: bankfull — the stage at which water begins to spill onto the floodplain — recurs about every 1.5–2 years [Leopold 1994]; the raw main-channel bank at these gauges is a high levee that the river rarely reaches.
- **Pluvial (multi-duration rainfall).** A province's own peak 3-day OR 30-day accumulated rainfall exceeds its 10-year Gumbel return level (ERA5-Land, climatology 1991–2020). The 3-day term captures cloudburst flooding; the 30-day term captures prolonged rain that saturates the basin.
- **De-circularization (state explicitly):** the ground truth is satellite flood extent; the gate uses river gauges and reanalysis rainfall — different sources — and every threshold comes from the *signal's own climatology*, never from the ground truth. Evaluation is leave-one-event-out (prequential).

### [Heading2] C. Baselines
- entity-graphrag: an entity-relation graph retriever.
- vector-rag: TF-IDF character n-gram retrieval over a real Thai news corpus.
- Same province universe and eval set for all three.

### [Heading2] D. Metrics
- Traceability: fraction of an explanation's claims that trace to graph evidence (baseline = 0 by construction).
- MCC (primary): appropriate for the high flood base rate; F1 is reported but is shown to be gamed by predict-all. Also report precision/recall/specificity/F1.
- PNS: for each mechanism, Necessity = fraction of true positives lost when the mechanism is removed (counterfactual intervention); Sufficiency = precision of the mechanism when it fires. Precision–recall as a function of the number of agreeing mechanisms.

## [Heading1] IV. Experimental Setup

- Events: five Chao Phraya floods, 2021–2025 (B.E. 2564–2568); 23 provinces each; 115 province-cases total.
- Ground truth: GISTDA satellite flooded area per province, cutoff ≥ 10,000 rai (fixed a priori). Base rate of flooding ≈ 0.73 over the scored cases.
- Data sources (Table I): satellite (ground truth), thaiwater river gauges (fluvial), ERA5-Land via the open-meteo archive (pluvial), GADM 4.1 (geometry), Copernicus GLO-90 DEM (independent flow-direction validation).
- No structural parameters are learned; thresholds are climatological and fixed before scoring.

## [Heading1] V. Results

### [Heading2] A. Main comparison
*(Table II — [tablehead] "TABLE II. PROVINCIAL FLOOD ATTRIBUTION, POOLED OVER FIVE EVENTS (N=115)")*

| System | F1 | MCC | Specificity | Recall | Traceability |
|---|---|---|---|---|---|
| causal-graphrag | 0.795 | **+0.203** | 0.387 | 0.81 | ~0.90 |
| entity-graphrag | **0.844** | 0.000 | 0.000 | 1.00 | 0 |
| vector-rag | 0.096 | −0.497 | 0.516 | 0.06 | 0 |

Key sentence for the rewrite: *the entity baseline wins F1 but has zero skill (MCC = 0) because it predicts almost every province flooded; the causal system is the only one with MCC > 0 and the only one whose predictions are traceable.*
Per-event causal MCC: 2021 +0.47, 2022 +0.52, 2023 +0.04, 2024 +0.37, 2025 +0.17 (report all five; 2023 is weak — do not hide it).

### [Heading2] B. Mechanism necessity and sufficiency (PNS)
*(Table III)*

| Mechanism | Necessity | Sufficiency | ΔRecall if removed |
|---|---|---|---|
| Fluvial (2-yr stage) | 0.35 | 0.79 | −0.29 |
| Pluvial 30-day | 0.21 | 0.77 | −0.17 |
| Pluvial 3-day | 0.00 | 0.85 | 0.00 |

Precision by number of agreeing mechanisms: ≥1 → 0.782 (recall 0.82); ≥2 → 0.833 (recall 0.36); ≥3 → 0.667. Sentence: *agreement among independent causal mechanisms increases precision — a traceable confidence signal the baselines cannot provide.* The 3-day term is redundant (necessity 0) but precise; the 30-day term recovers prolonged-rain events.

### [Heading2] C. Early-warning extension (optional section — keep or move to appendix)
Binary warning skill POD 0.81, FAR 0.218, CSI 0.660. Probability calibration by causal-hop shows a small Brier skill score over climatology (≈ +0.04) that is **not statistically significant** (event-level cluster bootstrap 95% CI [−0.54, 0.16]; p = 0.26; five events). Report this as not significant.

## [Heading1] VI. Discussion

### [Heading2] A. F1 is misleading at high base rate
At a 73% flood base rate, "predict every province" earns F1 0.844 with MCC 0. Hence F1 rewards over-prediction; MCC, specificity, and traceability are the criteria that separate a system that *reasons* from one that *guesses*. This is the operational meaning of "correctness is not faithfulness" [arXiv:2412.18004] in our setting.

### [Heading2] B. A predictability ceiling that is in the data, not the method
Three tests converge on MCC ≈ 0.20 (report the actual numbers): (1) a learned logistic combiner over the continuous signal ratios collapses to predict-all (in-sample and leave-one-event-out MCC = 0.0) at this base rate — no combination beats the rule; (2) principled rule variants cluster at MCC 0.13–0.19 (removing the redundant 3-day term changes nothing, consistent with PNS); (3) a ground-truth cutoff sweep (≥10k to ≥200k rai) does not raise MCC (0.21 → 0.14–0.17), so the limit is not merely base rate — the signals do not separate severity.

### [Heading2] C. What the residual misses are (hypothesis, not asserted)
The false negatives concentrate in 2023 and 2024 mainstem provinces. A soil-moisture probe (ERA5-Land root zone) shows these provinces were *not* soil-saturated (median event percentile 28% in 2023 and 38% in 2024; Nakhon Sawan at the 0–7th percentile), so the misses are **not** saturation floods. This is consistent with hydraulic backwater at confluences and floodplain inundation below the main-channel bank. *State this as a hypothesis:* raising the ceiling likely requires a hydrodynamic model or denser confluence gauging — new data, not a better combiner — rather than asserting the mechanism as proven.

### [Heading2] D. Honest correction (integrity)
An earlier version of this evaluation used a coarser "any sub-basin gauge over-bank" gate that over-flagged and reported F1 ≈ 0.9. That gate did not reproduce under the committed per-reach gate and was inconsistent with the physical record (the mainstem gauge at Nakhon Sawan never exceeded its bank in 2021–2025). We replaced it with the de-circularized per-reach gate and report the honest numbers here (F1 0.548 for the corrected gate before, and 0.795 after the survey-grounded refinements). We report old and new numbers together.

## [Heading1] VII. Conclusion and Future Work

- The causal-chain GraphRAG is the only compared system that is both faithful (100% traceable) and skillful (MCC > 0) for provincial flood attribution; F1 alone is misleading here.
- H1 supported (traceability/MCC gap that baselines cannot close by construction); H2 supported (hop-invariant prediction footprint).
- The ~0.20 MCC is a data/signal ceiling. Future work: hydrodynamic modeling / denser confluence gauges to capture backwater; district-level resolution to lower the base rate; more events for significance; other basins.

## [Heading5] Acknowledgment

*(Use the disclosure verbatim from the integrity guide; the advisor must approve the wording. Keep it in the blind version — it names no person or institution.)*

> The authors used a large language model (Claude, Anthropic) to assist in drafting and editing the English text and to build verification and analysis scripts. The system design, causal-graph construction, data, experiments, metric choices, and interpretation of results are the authors' own work, and the authors reviewed and take full responsibility for all content.

## [References] (numbered `[1]` in order of first appearance — replace with your final list; verify each against docs/REFERENCES.md; do NOT invent)

- [1] GraphRAG / multi-hop retrieval survey — arXiv:2502.11371
- [2] "Correctness is not Faithfulness in RAG Attributions" — arXiv:2412.18004
- [3] D. Chicco and G. Jurman, "The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy…," BMC Genomics, 2020
- [4] Feature Attribution with Necessity and Sufficiency (FANS) — arXiv:2402.08845 (and Pearl, Causality, for PNS)
- [5] L. B. Leopold, A View of the River, 1994 (bankfull recurrence)
- [6] Gale & Saunders, "The 2011 Thailand flood: climate causes and return periods," Weather, 2013
- [7] A. Niculescu-Mizil and R. Caruana, "Predicting good probabilities with supervised learning," ICML 2005
- [8] causal river-network model (Danube) — arXiv:1907.03555
- [9] flood knowledge graph + LLM + GIS — IJGIS 2024
- [10] Shin et al., 2020 — gauge-to-reach snapping (NHDPlus)
*(Add: GISTDA, thaiwater/HII, ERA5-Land/open-meteo, Copernicus GLO-90, GADM data citations.)*

---

## [Appendix N — DO NOT PUBLISH; author's working aid] Numbers traceability table

Per SKILL.md §3: every number above must trace to a result file. Fill/verify before writing.

| Value in paper | Correct value | Source file |
|---|---|---|
| Events / provinces / cases | 5 / 23 / 115 | `data/processed/ground_truth_*.json`, `web/ui_data_*.json` |
| Base rate | ~0.73 | `web/ui_data_*.json` (gold/universe) |
| causal F1 / MCC / spec / recall | 0.795 / +0.203 / 0.387 / 0.81 | `web/ui_data_*.json` confusion; `data/processed/pns_ablation.json` (full_model) |
| causal traceability | ~0.90 (0.74–0.94) | `web/ui_data_*.json` results.traceability |
| entity F1 / MCC / spec | 0.844 / 0.000 / 0.000 | `web/ui_data_*.json` confusion |
| vector F1 / MCC | 0.096 / −0.497 | `web/ui_data_*.json` confusion |
| per-event causal MCC | .47/.52/.04/.37/.17 | `web/ui_data_{2021..2025}.json` |
| PNS necessity/sufficiency | see Table III | `data/processed/pns_ablation.json` (pns) |
| PR by #mechanisms | 0.782 / 0.833 / 0.667 | `data/processed/pns_ablation.json` (pr_by_mechanism_count) |
| B POD/FAR/CSI | 0.81 / 0.218 / 0.660 | `data/processed/case_bank.json` (cumulative_scored) |
| B BSS / p | ≈+0.04 / 0.26 | `data/processed/warning_verification.json` (skill_significance) |
| ceiling: learned MCC | 0.0 | `data/processed/ceiling_analysis.json` (learned_combiner) |
| ceiling: rule variants | 0.13–0.19 | `data/processed/ceiling_analysis.json` (rule_variants) |
| ceiling: cutoff sweep | 0.21→0.14–0.17 | `data/processed/ceiling_analysis.json` (cutoff_sweep) |
| soil-moisture FN percentile | 28% (2023) / 38% (2024); NakhonSawan 0–7% | HISTORY.md (soil-moisture test) |
| honest F1 journey | 0.9(artifact)→0.548→0.795 | `docs/HISTORY.md` |

**Reconciliation to close before submission:** confusion counts must satisfy TP+FP+FN+TN = 115 for each system (causal: 68+19+16+12 = 115 ✔). Verify against `web/ui_data_*.json`.
