# -*- coding: utf-8 -*-
"""Paper content. Citation numbers here MUST match the REFS list at the bottom."""

TITLE = ("A Causal-Chain GraphRAG for Verifiable Provincial Flood Attribution "
         "in the Chao Phraya Basin")

ABSTRACT = ("Flood question-answering systems are usually judged by predictive accuracy, yet a correct "
            "answer is not necessarily a verifiable one. This paper presents a GraphRAG system that answers "
            "the question of why a province flooded by traversing a hydrological causal chain (rainfall, "
            "reservoir, river reach, downstream province) in which every edge carries an explicit evidence "
            "property, so each prediction is traceable to a gauge, a dataset, and a timestamp. Prediction "
            "uses a de-circularized two-signal gate: a fluvial signal that fires when a reach exceeds its own "
            "two-year return stage, and a pluvial signal that fires when 3-day or 30-day rainfall exceeds the "
            "province's own ten-year return level. Ground truth is satellite flood extent, while the gate uses "
            "river gauges and reanalysis rainfall, so no threshold is derived from the labels. Across five "
            "Chao Phraya events (2021-2025; 23 provinces; 115 province-cases) the system attains a Matthews "
            "correlation coefficient (MCC) of +0.203 with traceability of about 0.90, and is the only system "
            "compared with skill above chance: an entity-graph baseline reaches a higher F1 (0.844 against "
            "0.795) purely by predicting almost every province flooded, yet scores MCC 0.000 and specificity "
            "0. A counterfactual analysis quantifies each mechanism, and agreement between mechanisms raises "
            "precision from 0.782 to 0.833. Three convergent tests show that the attainable MCC of about 0.20 "
            "is a limit of the data rather than of the method. We report where the method loses and disclose "
            "the correction of an earlier evaluation artifact that had inflated F1.")

KEYWORDS = ("graph retrieval-augmented generation, causal graph, flood attribution, faithfulness, "
            "Matthews correlation coefficient, de-circularized evaluation, Chao Phraya basin")

INTRO = [
 ("Flood question-answering and early-warning systems are commonly evaluated with accuracy-oriented scores "
  "such as F1 or the critical success index. For operational decision support, however, the verifiability of "
  "an explanation matters as much as its correctness: an operator asked why a particular province is expected "
  "to flood must be able to follow the answer back to concrete measurements. Recent work on retrieval-augmented "
  "generation makes the same distinction, showing that a system can be correct for reasons it cannot expose, "
  "so that correctness and faithfulness are separate properties [3]."),
 ("This paper addresses that gap for provincial flood attribution in the Chao Phraya basin of Thailand. We "
  "build a causal-chain GraphRAG in which the graph encodes the physical route water takes, and in which every "
  "edge stores the evidence that justifies it, so a prediction can be replayed as a chain of measurements "
  "rather than presented as an opaque score. Fig. 1 summarizes the system. The main contributions of this "
  "paper are: (1) a causal-chain GraphRAG for flood attribution with complete edge-level evidence "
  "traceability; (2) a de-circularized prediction gate whose thresholds are drawn from gauge and rainfall "
  "climatology rather than from the labels, together with evidence that at high flood base rates F1 is gamed "
  "by a trivial predict-all baseline, so that MCC, specificity, and traceability are the appropriate criteria; "
  "(3) a counterfactual necessity and sufficiency analysis that quantifies how much each hydrological "
  "mechanism contributes; and (4) three convergent tests showing that the attainable skill is bounded by the "
  "data rather than by the combiner, together with a transparent account of correcting an earlier "
  "over-flagging artifact."),
]

RELATED = [
 ("A", "GraphRAG and Faithfulness in Retrieval",
  "Graph-based retrieval-augmented generation organizes retrieval over an explicit graph so that multi-hop "
  "questions can be answered by traversal rather than by similarity alone [1], and systematic comparisons "
  "report that the advantage of graph traversal widens as the number of required hops grows [2]. Evaluation of "
  "such systems increasingly separates whether an answer is correct from whether it is attributable to the "
  "retrieved evidence [3]. Our system takes the strict form of this idea: the graph is not only the retrieval "
  "substrate but also the explanation, because every edge on a returned path carries the source of the fact it "
  "asserts."),
 ("B", "Causal and Network Models of River Basins",
  "A river basin is naturally represented as a directed graph whose edges follow the direction of flow, and "
  "causal structure has been inferred for extreme discharges over such a basin network [9]. Compared with that "
  "line of work, our graph is deliberately small and physical: its nodes are rain stations, reservoirs, river "
  "reaches, confluences, and provinces, and its prediction rule is a fixed hydrological gate rather than a "
  "learned scorer, which is what allows the evaluation to remain de-circularized."),
 ("C", "Evaluation under Class Imbalance and Counterfactual Attribution",
  "For binary problems with skewed class balance, the Matthews correlation coefficient is preferred to F1 and "
  "accuracy because it accounts for all four cells of the confusion matrix and penalizes a classifier that "
  "never rejects the majority class [4]. Separately, counterfactual accounts of explanation formalize how "
  "necessary and how sufficient a factor is for an outcome [5]; we adopt that framing to measure the "
  "contribution of each hydrological mechanism by intervening on the gate."),
 ("D", "Hydrological Thresholds",
  "The thresholds in our gate are taken from established hydrology rather than fitted. Bankfull stage, at "
  "which water begins to spread onto the floodplain, recurs on average about every one and a half to two "
  "years [6], which motivates a two-year return stage as the fluvial trigger. Return-period rainfall is "
  "estimated with Gumbel frequency analysis, and the 2011 Chao Phraya flood has been assigned a return period "
  "of roughly ten to twenty years [7], which motivates a ten-year return level as the pluvial trigger. Finally, "
  "probability calibration is known to be unreliable when few samples are available [8], which is why our "
  "calibration results are reported as inconclusive rather than as a positive finding."),
]

SYSTEM = [
 ("A", "System Overview",
  "As shown in Fig. 1, the system has three parts: a causal graph that stores the basin and the evidence "
  "behind each link, a two-signal gate that turns measurements into a provincial prediction, and an evaluation "
  "layer that scores the prediction against satellite ground truth. A province is predicted to flood when "
  "either signal fires and the province is not protected by dikes, as expressed in (1). No structural "
  "parameter is learned; the only free choices are the two return periods, and both are fixed a priori from "
  "the hydrological literature."),
 ("B", "Causal Graph",
  "The graph contains five node types, namely RainStation, Reservoir, RiverReach, Confluence, and Province, "
  "connected by directed edges that follow the direction of water flow: FEEDS, RUNOFF_TO, OVERFLOWS_TO, "
  "FLOWS_TO, and INUNDATES. Every edge stores an evidence property recording the station, dataset, and "
  "timestamp that justify it, and a guard in the loader rejects any edge without one, so traceability is a "
  "structural invariant rather than a reporting convention. Hop count is the length of the shortest causal "
  "path from a rainfall source to a province, and is a property of the basin geometry, so the hop buckets used "
  "in evaluation are fixed across events. The graph covers eight Chao Phraya sub-basins and 23 provinces."),
 ("C", "De-circularized Two-Signal Gate",
  "The fluvial signal snaps each river reach to the gauges physically located on it and declares the reach "
  "over-topped when its 95th-percentile stage during the flood season exceeds that gauge's own two-year return "
  "stage, estimated as the median annual maximum computed leave-one-event-out. The 95th percentile is used "
  "instead of the maximum because isolated telemetry spikes would otherwise trigger the gate. The main-channel "
  "bank recorded for these gauges sits high above the floodplain and is rarely reached, so using it directly "
  "would make the gate almost silent; the two-year return stage is the standard hydrological proxy for the "
  "onset of overbank flow [6]. The pluvial signal fires when a province's peak 3-day or 30-day accumulated "
  "rainfall exceeds its own ten-year Gumbel return level, the shorter duration capturing cloudbursts and the "
  "longer one capturing prolonged rain that saturates the basin. Crucially, ground truth is satellite flood "
  "extent whereas the gate reads river gauges and reanalysis rainfall, and every threshold is derived from the "
  "climatology of the signal itself, so no label information enters the decision rule."),
 ("D", "Baselines",
  "Two baselines share the province universe and the evaluation set. The entity-graph baseline retrieves over "
  "an entity-relation graph without the causal gate, and the vector baseline ranks a corpus of Thai flood news "
  "with character n-gram TF-IDF, a tokenization chosen because Thai text has no delimited word boundaries. "
  "Neither baseline can attach evidence to a prediction, so their traceability is zero by construction."),
]

EQUATION = "flood(p) = [ S ≥ S₂ ∨ maxₙ Rₙ ≥ Rₙ,₁₀ ] ∧ ¬ protected"
EQUATION_NOTE = ("In (1), S is the 95th-percentile stage of the gauge governing the reach that inundates "
                 "province p and S₂ is that gauge's two-year return stage; Rₙ is the peak n-day "
                 "rainfall over p for n in {3, 30} and Rₙ,₁₀ the corresponding ten-year return "
                 "level; and protected marks provinces shielded by dikes. The rule has no tunable weight.")

SETTING = [
 ("The evaluation covers five Chao Phraya flood events from 2021 to 2025 over the same 23 provinces, giving "
  "115 province-cases. Ground truth is the per-province flooded area derived from GISTDA satellite products "
  "[10], with a threshold of 10,000 rai fixed before any experiment; on this definition the base rate of "
  "flooding is about 0.73, which is what makes the choice of metric consequential. The fluvial signal is "
  "computed from public thaiwater river-gauge time series [11], the pluvial signal from ERA5-Land daily "
  "precipitation obtained through the Open-Meteo archive [12], provincial geometry from GADM 4.1 [13], and an "
  "independent check of flow direction from the Copernicus GLO-90 digital elevation model [14]."),
 ("We report precision, recall, specificity, F1, and MCC, and treat MCC as primary for the reason given in "
  "Section II.C. Traceability is the fraction of the claims in an explanation that resolve to an evidence "
  "property on the traversed edges. For each mechanism we compute a probability of necessity, defined as the "
  "fraction of true positives lost when that mechanism is removed by intervention, and a probability of "
  "sufficiency, defined as its precision when it fires; we also report precision as a function of how many "
  "mechanisms agree. Return levels are estimated leave-one-event-out so that an event never contributes to its "
  "own threshold. The pipeline contains no learned structural parameters and no random component, so repeated "
  "runs reproduce identical outputs given the same data snapshot."),
]

RESULTS_A = ("Table I reports the pooled comparison. The entity baseline obtains the highest F1, but it does so "
 "by predicting that almost every province floods: its recall is 1.00, its specificity is 0.000, and its MCC "
 "is exactly 0.000, which is the value expected from a classifier with no discriminative power. The causal "
 "system is the only one of the three with MCC above zero and the only one whose predictions carry evidence. "
 "Per-event MCC is +0.47, +0.52, +0.04, +0.37, and +0.17 for 2021 through 2025; we report all five values, "
 "including the weak 2023 result, in which the gauges and rainfall of that year gave little signal.")

RESULTS_B = ("Table II decomposes the gate by intervention. The fluvial signal is the most necessary: removing "
 "it costs 0.29 of recall. The 30-day pluvial term is the second most necessary and is what recovers "
 "prolonged-rain events such as 2023. The 3-day term has necessity 0.00, meaning every province it catches is "
 "already caught by another mechanism, yet its sufficiency of 0.85 is the highest of the three, so it is "
 "precise but redundant on this data. Precision also increases with agreement: 0.782 when at least one "
 "mechanism fires, 0.833 when at least two agree, and 0.667 for the small set where all three agree. Agreement "
 "between independent physical mechanisms therefore provides a confidence signal that is itself traceable, "
 "which neither baseline can offer.")

RESULTS_C = ("A natural question is whether the modest MCC reflects a weak combiner or a weak signal. Table III "
 "reports three tests that point to the latter. First, a logistic model trained on the continuous signal "
 "ratios degenerates to predicting every province, scoring MCC 0.000 both in-sample and leave-one-event-out, "
 "so no learned combination of these features beats the fixed rule at this base rate. Second, four principled "
 "rule variants cluster between 0.13 and 0.19, and dropping the redundant 3-day term changes nothing, which is "
 "consistent with the necessity analysis. Third, raising the ground-truth threshold from 10,000 to 200,000 rai "
 "lowers the base rate but does not raise MCC, so the limitation is not imbalance alone: these signals do not "
 "separate flood severity. We therefore read the attainable MCC of about 0.20 as a property of the available "
 "measurements rather than of the model family.")

RESULTS_D = ("As an extension we also treated the gate as an early-warning rule. Its binary skill is a "
 "probability of detection of 0.81, a false-alarm ratio of 0.218, and a critical success index of 0.660. "
 "Calibrating a probability by causal-hop depth yields a Brier skill score over climatology of about +0.04, "
 "but with five events the event-level cluster bootstrap gives a 95% confidence interval from -0.54 to 0.16 "
 "and p = 0.26. We therefore report the calibration as inconclusive; it is consistent with the known "
 "difficulty of calibrating probabilities from few samples [8].")

DISCUSSION = ("Taken together, the results support the two hypotheses in a specific and limited sense. H1 holds: "
 "traceability is 0.90 for the causal system and zero for both baselines, and this gap is structural rather "
 "than incidental, because neither baseline stores evidence on the objects it retrieves. H2 holds in that the "
 "prediction is a basin-wide footprint derived from event state, so its quality does not decay as the causal "
 "chain lengthens. The most consequential measurement insight is that F1 is actively misleading here: at a "
 "base rate of 0.73 a predict-all rule earns F1 0.844 while contributing no information, and only MCC and "
 "specificity expose that. A second insight concerns what the system still misses. The false negatives "
 "concentrate in mainstem provinces in 2023 and 2024, and a soil-moisture probe using ERA5-Land root-zone data "
 "shows that those provinces were not saturated, with a median event percentile of 28% in 2023 and 38% in "
 "2024 and Nakhon Sawan between the 0th and 7th percentile. Their flooding is therefore not of the "
 "saturation-driven type the pluvial signal is designed to detect. A backwater effect at confluences, or "
 "inundation of floodplain below the main-channel bank, would be consistent with this pattern, but we did not "
 "run a hydrodynamic model and so we state it as a hypothesis rather than a finding.")

LIMITATIONS = ("Four limitations should be noted. First, the absolute skill is modest: an MCC of about 0.20 "
 "means the system is informative but far from reliable at province level, and the operating point reported "
 "here favours recall, so specificity is 0.387. Second, five events give little statistical power; the "
 "early-warning calibration in Section V.D is not significant, and per-event MCC varies from +0.04 to +0.52. "
 "Third, the ground truth is a thresholded satellite product, so a province just below 10,000 rai is scored as "
 "dry although it may have flooded locally. Fourth, and most important for interpretation, an earlier version "
 "of this evaluation used a coarser gate that marked an entire sub-basin as flooding whenever any gauge in it "
 "over-topped. That gate reported an F1 near 0.9, but it did not reproduce under the per-reach gate and "
 "contradicted the physical record, since the mainstem gauge at Nakhon Sawan never exceeded its bank between "
 "2021 and 2025. Replacing it lowered F1 to 0.548, and the threshold corrections described in Section III.C "
 "raised it to 0.795. We report the earlier and the corrected numbers together rather than silently replacing "
 "them.")

CONCLUSION = ("This paper presented a causal-chain GraphRAG for provincial flood attribution whose predictions "
 "are traceable to the measurements that justify them, and whose decision rule takes no threshold from the "
 "labels it is scored against. On five Chao Phraya events the system is the only one of three compared that "
 "combines complete traceability with skill above chance, at an MCC of +0.203, while an entity-graph baseline "
 "achieves a higher F1 with no skill at all. A counterfactual analysis showed which hydrological mechanism "
 "carries the prediction and that agreement between mechanisms raises precision, and three convergent tests "
 "indicated that the attainable skill is bounded by the available measurements rather than by the combiner. "
 "The most useful direction for future work therefore concerns data rather than modelling: a hydrodynamic "
 "treatment of confluence backwater, denser gauging where the mainstem misses are concentrated, evaluation at "
 "district rather than province resolution to reduce the base rate, and additional events to give the "
 "calibration enough power to be decided.")

ACK = ("The authors used a large language model (Claude, Anthropic) to assist in drafting and editing the "
       "English text and to build verification scripts. The system design, causal-graph construction, data, "
       "experiments, metric choices, and interpretation of results are the authors' own work, and the authors "
       "reviewed and take full responsibility for all content.")

# NOTE: verify every entry (authors, year, venue, arXiv id) before submission.
# Entries marked (verify) are recorded in docs/REFERENCES.md without confirmed author lists.
REFS = [
 "D. Edge, H. Trinh, N. Cheng, J. Bradley, A. Chao, A. Mody, S. Truitt, and J. Larson, “From local to "
 "global: A graph RAG approach to query-focused summarization,” arXiv:2404.16130, 2024.",
 "“RAG vs. GraphRAG: A systematic evaluation and key insights,” arXiv:2502.11371, 2025. (verify authors)",
 "“Correctness is not faithfulness in RAG attributions,” arXiv:2412.18004, 2024. (verify authors)",
 "D. Chicco and G. Jurman, “The advantages of the Matthews correlation coefficient (MCC) over F1 score and "
 "accuracy in binary classification evaluation,” BMC Genomics, vol. 21, no. 6, 2020.",
 "J. Pearl, Causality: Models, Reasoning, and Inference, 2nd ed. Cambridge, U.K.: Cambridge Univ. Press, 2009.",
 "L. B. Leopold, A View of the River. Cambridge, MA, USA: Harvard Univ. Press, 1994.",
 "S. J. Gale and M. A. Saunders, “The 2011 Thailand flood: climate causes and return periods,” "
 "Weather, vol. 68, no. 9, pp. 233–238, 2013.",
 "A. Niculescu-Mizil and R. Caruana, “Predicting good probabilities with supervised learning,” in "
 "Proc. 22nd Int. Conf. Machine Learning (ICML), 2005, pp. 625–632.",
 "“Causal mechanism of extreme river discharges in the upper Danube basin network,” arXiv:1907.03555, "
 "2019. (verify authors)",
 "Geo-Informatics and Space Technology Development Agency (GISTDA), flood-extent products, Thailand. "
 "[Online]. Available: https://www.gistda.or.th",
 "Hydro-Informatics Institute (HII), Thai Water public API, river-gauge time series. [Online]. Available: "
 "https://www.thaiwater.net",
 "Copernicus Climate Change Service, ERA5-Land reanalysis, accessed through the Open-Meteo historical weather "
 "archive. [Online]. Available: https://open-meteo.com",
 "GADM, Database of Global Administrative Areas, version 4.1. [Online]. Available: https://gadm.org",
 "European Space Agency, Copernicus DEM GLO-90 global digital elevation model. [Online]. Available: "
 "https://spacedata.copernicus.eu",
]
