# fix.md — Rewrite worksheet for PAPER_IEEE.docx (overlap step 2)

> Per `research-paper-integrity` SKILL §2: the .docx (`docs/PAPER_IEEE.docx`) holds the **AI first draft**.
> Rewrite **each paragraph in your own words from the FACTS below — do NOT look at the draft sentence while
> you write.** Then measure 5-gram overlap (target < 20%, and again excluding proper nouns / numbers / terms).
> Keep every number and term in the "must not change" column verbatim. The AI draft of each paragraph is
> collapsed in `<details>` so you write from facts, not from the draft's word order.
>
> **Rule:** never rephrase a *correct* sentence just to move the overlap number. Edit only to be more accurate,
> clearer, or more your own voice. Fix your own typos even if overlap rises; then re-measure excluding
> proper nouns/numbers/terms.

Legend — **Facts** = what the paragraph must say · **Keep** = terms/numbers that must stay exact · **Trap** = what NOT to claim.

---

### P1 — Abstract
- **Facts:** evaluation is usually accuracy-based; verifiability matters too; we compare causal-chain GraphRAG vs entity-graph and vector-RAG baselines; 5 events, 23 provinces, 115 cases; causal MCC +0.203, traceability ~0.90, only system with skill; entity has higher F1 (0.844 vs 0.795) but MCC 0.000, specificity 0; de-circularized gate; PNS; mechanism agreement raises precision 0.782→0.833; MCC ~0.20 is a **data** ceiling; we report where we lose; we disclose an inflated-F1 artifact correction.
- **Keep:** MCC; +0.203; 0.90; 0.844; 0.795; 0.000; 0.782; 0.833; 0.20; 115; 23; five events; GISTDA; Chao Phraya.
- **Trap:** do NOT say "more accurate". Say "more verifiable / only system with skill above chance".

### P2 — Introduction ¶1
- **Facts:** flood QA/warning judged on F1/CSI; for decision support the explanation must be traceable ("why this province?"); correctness ≠ faithfulness in RAG.
- **Keep:** F1; CSI; correctness; faithfulness.
- **Trap:** don't overclaim novelty of the causal idea; frame around verifiability.

### P3 — Introduction ¶2 (contributions + hypotheses)
- **Facts:** every edge carries an `evidence` property → traceable; 5 contributions (traceability; F1-is-gamed→MCC; PNS; data-ceiling; artifact-correction); H1 (more verifiable), H2 (hop-invariant).
- **Keep:** evidence; MCC; PNS; H1; H2; 0.20 MCC.
- **Trap:** state H2 as "does not degrade with chain length", not "improves".

### P4 — Related Work
- **Facts:** GraphRAG/multi-hop; faithfulness/attribution eval; causal river-network graphs + flood KG+LLM+GIS; MCC > F1 for imbalance; PNS / necessity-sufficiency attribution; bankfull recurs ~1.5–2 yr; Gumbel return-period rainfall; 2011 Chao Phraya ~10–20 yr; calibration unreliable with few samples.
- **Keep:** Matthews correlation coefficient; Gumbel; 1.5–2 yr; 10–20 yr; every citation must exist in the reference list. **Verify each citation's authors/year/DOI before use — do not keep a citation you cannot check.**
- **Trap:** don't cite anything you haven't verified.

### P5 — Method: Causal Graph
- **Facts:** 5 node types; directed flow edges (5 types); every edge has an `evidence` property (station/dataset/timestamp); hop = shortest causal path from a rainfall source; 8 sub-basins, 23 provinces.
- **Keep:** RainStation/Reservoir/RiverReach/Confluence/Province; FEEDS/RUNOFF_TO/OVERFLOWS_TO/FLOWS_TO/INUNDATES; 8; 23.
- **Trap:** —

### P6 — Method: De-circularized gate
- **Facts:** flood if (fluvial ∪ pluvial) AND not protected; fluvial = reach's p95 stage > its own 2-yr return stage (LOEO median annual max), bankfull onset ~1.5–2 yr, lower than the high main-channel bank; pluvial = province's peak 3-day OR 30-day rain > its 10-yr Gumbel level; **ground truth = satellite, gate = gauges + reanalysis rain (different sources); thresholds from the signal's own climatology, never from gold; LOEO evaluation.**
- **Keep:** p95; 2-year return; 1.5–2 yr; 3-day; 30-day; 10-year Gumbel; leave-one-event-out; de-circularized.
- **Trap:** emphasize the de-circularization sentence — it is the integrity core. Don't imply thresholds were tuned.

### P7 — Method: Baselines & Metrics
- **Facts:** entity-graph + TF-IDF char n-gram vector-RAG over Thai news; same universe/eval set; traceability (baselines = 0 by construction); MCC primary; also precision/recall/specificity/F1; PNS = necessity (TP lost when a mechanism is removed by intervention) + sufficiency (its precision when it fires) + precision vs #agreeing mechanisms.
- **Keep:** TF-IDF; MCC; necessity; sufficiency; 0 (baseline traceability).
- **Trap:** —

### P8 — Experimental Setup
- **Facts:** 5 events 2021–2025; 23 provinces; 115 cases; gold = satellite flooded area, cutoff ≥ 10,000 rai (fixed); base rate ≈ 0.73; sources (GISTDA / thaiwater / ERA5-Land via open-meteo / GADM 4.1 / Copernicus GLO-90); 0 learned structural params; thresholds fixed before scoring.
- **Keep:** 10,000 rai; 0.73; 115; 2021–2025; ERA5-Land; open-meteo; Copernicus GLO-90; GADM 4.1.
- **Trap:** —

### P9 — Results ¶1 (Table I)
- **Facts:** entity wins F1 (0.844) but MCC 0, specificity 0 (predict-all); causal only one with MCC>0 and traceable; per-event causal MCC +0.47/+0.52/+0.04/+0.37/+0.17 (report all five incl. weak 2023).
- **Keep:** 0.795/+0.203/0.387/0.81/~0.90 (causal); 0.844/0.000/0.000 (entity); 0.096/−0.497 (vector); the five per-event MCCs.
- **Trap:** don't hide the weak 2023 value; report all five.

### P10 — Results ¶2 (Table II, PNS + warning)
- **Facts:** fluvial most necessary; 30-day recovers prolonged rain; 3-day redundant (necessity 0) but precise (0.85); precision 0.782(≥1)/0.833(≥2)/0.667(≥3) = agreement is a traceable confidence signal; warning extension POD 0.81/FAR 0.218/CSI 0.660; calibration BSS ≈ +0.04 **not significant** (event-level CI [−0.54, 0.16]; p=0.26; N=5).
- **Keep:** 0.35/0.79/−0.29; 0.21/0.77/−0.17; 0.00/0.85/0.00; 0.782/0.833/0.667; 0.81/0.218/0.660; +0.04; p=0.26.
- **Trap:** state the BSS as **not significant**; do not imply calibration works.

### P11 — Discussion: F1 misleading
- **Facts:** at 73% base rate predict-all gets F1 0.844, MCC 0; MCC/specificity/traceability separate reasoning from guessing = correctness ≠ faithfulness in our setting.
- **Keep:** 73%; 0.844; MCC 0.
- **Trap:** —

### P12 — Discussion: data ceiling
- **Facts:** 3 tests → MCC ~0.20: (1) learned logistic combiner collapses to predict-all (in-sample & LOEO MCC 0.0); (2) rule variants 0.13–0.19, dropping redundant 3-day changes nothing; (3) cutoff sweep 10k→200k rai does not raise MCC (0.21→0.14–0.17) — signals don't separate severity.
- **Keep:** 0.20; 0.0; 0.13–0.19; 10,000; 200,000; 0.21; 0.14–0.17.
- **Trap:** conclude the ceiling is in the **data/signals**, not the method.

### P13 — Discussion: residual misses (HYPOTHESIS)
- **Facts:** FN concentrate in 2023/2024 mainstem; soil-moisture probe shows they were NOT saturated (median percentile 28%/38%; Nakhon Sawan 0–7th) → not saturation floods; **consistent with** hydraulic backwater (state as hypothesis, not proven); raising the ceiling needs a hydrodynamic model / denser confluence gauging = new data.
- **Keep:** 28%; 38%; 0–7th; Nakhon Sawan.
- **Trap:** 🔴 state backwater as a **hypothesis** ("consistent with", "likely") — do NOT assert it as verified (you did not run a hydrodynamic model).

### P14 — Discussion: honest correction
- **Facts:** earlier "any sub-basin gauge over-bank" gate over-flagged (F1 ≈ 0.9); did not reproduce under the per-reach gate; inconsistent with physics (Nakhon Sawan mainstem never exceeded bank 2021–2025); replaced by de-circularized per-reach gate; corrected F1 0.548 → 0.795 after refinements; report old+new together.
- **Keep:** 0.9; 0.548; 0.795; 2021–2025; Nakhon Sawan.
- **Trap:** report old **and** new; do not delete the old number.

### P15 — Conclusion
- **Facts:** causal is the only system both faithful (traceable) and skillful (MCC>0); H1 supported (traceability/MCC gap baselines cannot close); H2 supported (hop-invariant footprint); ~0.20 is a data ceiling; future work = hydrodynamic model / denser confluence gauges (backwater), district resolution (lower base rate), more events (significance), other basins.
- **Keep:** MCC>0; H1; H2; 0.20.
- **Trap:** don't claim better accuracy; claim faithful + skillful.

### P16 — Acknowledgment
- Use the disclosure **as written** (it is already truthful and 44-word style). Change "assisted in drafting" only if you rewrote everything → then "help improve the wording and grammar". **Advisor must approve this wording.** Keep it in the blind version.

---

## Numbers traceability (verify every number against these files before submission)
| Number | Value | File |
|---|---|---|
| causal F1/MCC/spec/recall | 0.795 / +0.203 / 0.387 / 0.81 | `web/ui_data_*.json`, `data/processed/pns_ablation.json` |
| traceability | ~0.90 (0.74–0.94 per event) | `web/ui_data_*.json` results.traceability |
| entity / vector | 0.844,0.000,0.000 / 0.096,−0.497 | `web/ui_data_*.json` confusion |
| per-event MCC | +.47/+.52/+.04/+.37/+.17 | `web/ui_data_{2021..2025}.json` |
| PNS | Table II values | `data/processed/pns_ablation.json` |
| PR by #mech | 0.782/0.833/0.667 | `data/processed/pns_ablation.json` |
| warning POD/FAR/CSI | 0.81/0.218/0.660 | `data/processed/case_bank.json` |
| BSS / p | +0.04 / 0.26 | `data/processed/warning_verification.json` |
| ceiling tests | 0.0 / 0.13–0.19 / 0.21→0.14–0.17 | `data/processed/ceiling_analysis.json` |
| soil-moisture percentiles | 28% / 38% / 0–7% | `docs/HISTORY.md` |

**Reconciliation:** each system's TP+FP+FN+TN must equal 115 (causal 68+19+16+12 = 115 ✔). Verify from `web/ui_data_*.json`.

## Before submission (from the integrity checklist)
- [ ] Rewrote every paragraph from facts; measured 5-gram overlap (recorded), and again excluding proper nouns/numbers/terms.
- [ ] Every number traces to a result file (table above); reconciliation closes.
- [ ] Backwater stated as hypothesis, not asserted.
- [ ] Limitations declared incl. where we lose (entity beats F1; B not significant).
- [ ] Every citation verified and appears in the reference list both ways.
- [ ] Figure text ≥ 8 pt at final size: `pt = (font_px / 1200) × display_width_in × 72`. Fig. 1 is **vertical, single-column** (1200 × 1690 px placed at 240 pt = 3.33 in); its smallest font is 40 px → **exactly 8.0 pt** ✔ — this is at the limit, so **do not shrink the figure**; if you narrow the column, enlarge the fonts in `docs/fig_system_overview.png` first.
- [ ] Tables follow IEEE **three-line** style (rule above header, below header, at bottom; **no vertical rules**), centered, 8 pt, header row repeats. Keep it that way if you edit them.
- [ ] Acknowledgment approved by advisor; blind version keeps it; metadata cleared with the word processor's own inspector — never forge Producer/Creator.
- [ ] Page count checked on the exported PDF.
