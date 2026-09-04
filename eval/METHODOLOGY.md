# METHODOLOGY — Thai Flood Causal-Chain GraphRAG (frozen rules)

This file states the evaluation rules that are **held constant** across every run and
every code change. It exists so results cannot be quietly reshaped to look better. The
sibling repos (thai-legal-temporal-graphrag, thai-graphrag-benchmark,
thai-multiteacher-opd) each freeze their methodology before reporting; this does the same.

> Honest scope note: this document was written alongside the 2026-09-03 basin expansion,
> not before the very first fixture run months earlier. What it freezes is the **rule set**
> (below), each of which was in force during the runs it governs. The full honest history
> of every number change is in `README.md` → Experiment Report (old-vs-new reported side
> by side, never overwritten).

## 1. The question and the metric
Measure whether a retriever that traverses a **real causal chain**
(rain → reservoir/runoff → river reach → province) explains provincial flooding more
**verifiably** than entity-relation GraphRAG or vector RAG. Primary reported quantities:
- **F1** of the predicted flooded-province set vs the GISTDA satellite gold set.
- **F1 by causal-hop length** (buckets 2/3/4/5) — the H2 (hop-robustness) test.
- **Traceability** = fraction of answers whose every edge carries source `evidence`.
- **Specificity** (negative control) = ability to correctly say a province did NOT flood.
- **Bootstrap 95% CI** on F1 and on the paired causal−entity difference, per event and
  **pooled across events** (`src/eval/pooled_significance.py`, N=46 (event,province) cases).
- **McNemar's exact paired test** (`src/eval/mcnemar.py`) — the appropriate small-N test for
  two classifiers on the same provinces; reported two-sided AND one-sided (H1 is directional:
  causal ≥ entity). Pooled across events.
- **Explanation faithfulness** (`src/eval/faithfulness.py`) — deterministic grounding check
  that the causal LLM explanation names only geography in its own chain (no cross-basin
  hallucination). Reproducible; no second LLM as judge.
- **Topology validity** (4 independent methods) — DAG + reachability + sub-basin consistency
  (`validate_topology.py`); every FLOWS_TO edge downhill on a real DEM (`dem_topology.py`);
  flow-accumulation grows downstream (`dem_flow_accumulation.py`, pysheds); D8 flow-routing
  reproduces the main-stem edges (`dem_route_check.py`). All four agree, incl. flagging Tha
  Chin as a distributary. Not yet a full 30 m auto-delineation (future work).
- **Discrimination analysis** (`src/eval/discrimination.py`) — reports that causal's advantage
  requires the event to have real negatives; a near-universal flood (2011) is non-discriminating.
  Used to justify NOT adding 2011 as a scored event (would also break the total-flood-area
  metric and the 23-province universe — see the 2011 artifact's note).
- **Lead-time validation + warning skill** (`src/eval/lead_validation.py`) — predicted lead vs
  the observed 2011 progression (timing only, not scored): Spearman ρ, calibrated R², raw
  MAE/RMSE, lead adequacy, plus POD/FAR/CSI/missed-rate (NOAA glossary) from the scored-event
  confusion. The raw magnitude error is reported honestly (2011 was a ~5.7× slow-fill outlier),
  never tuned away.
- **Probabilistic + risk layer** (`src/eval/risk_warning.py`) — warnings are wrapped with a
  calibrated probability = the *measured* precision (not invented), a lead window, and
  Risk = Hazard × Exposure × Vulnerability (UNDRR/IPCC; population from NSO census). No new
  predictor is trained.
- **Blind / out-of-sample** (`src/eval/blind_test.py`) — the model has zero learned
  parameters (structure from hydrology, gate from independent RID gauges; gold only scores),
  so every event is out-of-sample by construction and gold-leakage is structurally impossible;
  the Mekong/NE live event is a prospective blind test.

## 2. Ground truth (never the model's own graph)
Gold = **GISTDA satellite (Sentinel-1) flood-area** per province, published via thaiwater,
with a fixed **≥10,000-rai** significance cutoff. The cutoff is the same one used by the
original 10-province ground truth and is **not changed per event or per result**. Ground
truth is defined independently of the causal graph and of the gate signal (§4).

## 3. The province universe (fixed, not cherry-picked)
Universe = the **23 provinces of the Chao Phraya basin** (8 sub-basins), listed in
`data/processed/chao_phraya_basin_provinces.json` by geography, **before** looking at any
result. Provinces outside the basin are out of the graph's scope and excluded. A province's
gold/negative label is decided **only** by the §2 cutoff applied to the GISTDA table — the
label is never hand-edited to help or hurt a system. The earlier 10-province universe is
frozen as `ground_truth_{year}_core10_frozen.json`; README reports old (N=10) vs new (N=23)
side by side.

## 4. De-circularization — gate signal ≠ ground truth
`RiverReach.overflow` (the gate that lets the causal system predict a province) comes from
**river-gauge / over-bank assessments**, an instrument **independent** of the satellite gold:
- 2022: RID SWOC bulletin 21-10-2565 (`river_reach_overbank_2022.json`) — high confidence.
- 2021: inferred from the Dianmu mechanism + `river_gauges_2021.json` — **medium confidence,
  labelled as such**, and deliberately **not** flipped to catch a province just because it
  flooded (e.g. Kamphaeng Phet stays an honest false-negative).
Dam `spillway`/`active` come from `dam_specs.json` (EGAT/RID). No gate value is ever set
from the flood outcome it is later scored against.

## 5. Fair comparison
All three retrievers share the same eval set, the same question set, the same LLM/prompt
where an LLM is used, and the same province universe. `entity-graphrag` is an
undirected-traversal baseline (no flow direction, no evidence); `vector-rag` is TF-IDF over
the same news corpus. The causal system's only structural advantages are flow direction,
the overflow gate, the protection flag, and the runoff path — exactly what the ablation
(`src/eval/ablation.py`) turns off one at a time.

## 6. Hard rules (inherited from the project's standing instructions)
1. **Report every number change old + new together.** Never silently replace an old number.
2. **Never edit the eval set / gold to make results look better.** Expanding N with more
   real data under the *same* cutoff rule is allowed and must be disclosed; tuning labels is not.
3. **Never hardcode research conclusions.** Every number comes from `python -m` runs.
4. If a data source is unreachable, log it as a Bug (with a "affects results?" note) — do
   not fabricate or silently skip.
5. Unflattering results (false positives, false negatives, non-significant gaps, drops) are
   reported, not dropped.

## 7. What "correct / miss / false-positive" mean
- **TP**: system predicts flood, GISTDA ≥ cutoff.
- **FP**: system predicts flood, GISTDA < cutoff (e.g. Pathum Thani).
- **FN**: system does not predict, GISTDA ≥ cutoff (e.g. Ping-basin Tak/Kamphaeng Phet,
  which flooded from local rain while the main channel did not over-bank).
- **TN**: system does not predict, GISTDA < cutoff.

## 8. Reproduce
```
# per event: EVENT_ID in {chao_phraya_2022, chao_phraya_2021}
python -m src.ingest.build_ground_truth      # gold from full GISTDA tables + cutoff
EVENT_ID=chao_phraya_2022 python -m src.ingest.fixtures
EVENT_ID=chao_phraya_2022 python -m src.geo.basin_to_province
EVENT_ID=chao_phraya_2022 python -m src.graph.load
EVENT_ID=chao_phraya_2022 python -m src.eval.run          # F1-by-hop, 3 systems
EVENT_ID=chao_phraya_2022 python -m src.eval.ablation     # mechanism ablation
EVENT_ID=chao_phraya_2022 python -m src.eval.build_ui_data # confusion + bootstrap + UI
pytest -q                                                  # 22 tests
```
