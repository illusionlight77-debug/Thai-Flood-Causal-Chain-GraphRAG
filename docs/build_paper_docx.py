# -*- coding: utf-8 -*-
"""Build the IEEE conference paper .docx on top of the provided Strict-OOXML template.
Tables follow IEEE practice: three-line rules (no vertical lines), centered, 8pt styles,
widths in pt to match the template's measurement convention."""
import os, re, shutil, zipfile

BASE = r"C:/Users/Illus/AppData/Local/Temp/claude/E--Thai-Flood-Causal-Chain-GraphRAG/32b7184a-a00b-47b8-892d-f8a82fa7165b/scratchpad/ieee"
U = os.path.join(BASE, "unpacked")
A = "http://purl.oclc.org/ooxml/drawingml/main"
PIC = "http://purl.oclc.org/ooxml/drawingml/picture"
RID_IMG = "rId100"
FIG_W, FIG_H = 1200, 1690          # px
COL_PT = 240                        # single-column table/figure width (pt)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

PG = ('<w:pgSz w:w="595.30pt" w:h="841.90pt" w:code="9"/>'
      '<w:pgMar w:top="54pt" w:right="44.65pt" w:bottom="72pt" w:left="44.65pt" '
      'w:header="36pt" w:footer="36pt" w:gutter="0pt"/><w:docGrid w:linePitch="360"/>')

def sect(cols):
    c = '<w:cols w:space="36pt"/>' if cols == 1 else '<w:cols w:num="2" w:space="18pt"/>'
    return '<w:type w:val="continuous"/>' + PG + c

def sectbreak(cols):
    return '<w:p><w:pPr><w:sectPr>' + sect(cols) + '</w:sectPr></w:pPr></w:p>'

def run(t, b=False, i=False):
    rpr = ''
    if b or i:
        rpr = '<w:rPr>' + ('<w:b/>' if b else '') + ('<w:i/>' if i else '') + '</w:rPr>'
    return '<w:r>' + rpr + '<w:t xml:space="preserve">' + esc(t) + '</w:t></w:r>'

def para(style, runs, jc=None):
    if isinstance(runs, str):
        runs = [run(runs)]
    j = '<w:jc w:val="%s"/>' % jc if jc else ''
    return '<w:p><w:pPr><w:pStyle w:val="%s"/>%s</w:pPr>%s</w:p>' % (style, j, ''.join(runs))

def h(style, txt):
    return para(style, [run(txt)])

def bt(txt):
    return para("BodyText", [run(txt)])

# ---------------- figure (inline, single column) ----------------
CX = int(COL_PT / 72 * 914400)
CY = int(CX * FIG_H / FIG_W)

def figpara():
    draw = ('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            '<wp:docPr id="1" name="Figure1"/><wp:cNvGraphicFramePr/>'
            '<a:graphic xmlns:a="%s"><a:graphicData uri="%s">'
            '<pic:pic xmlns:pic="%s"><pic:nvPicPr><pic:cNvPr id="1" name="fig.png"/>'
            '<pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>') % (
        CX, CY, A, PIC, PIC, RID_IMG, CX, CY)
    return '<w:p><w:pPr><w:pStyle w:val="figurecaption"/><w:jc w:val="center"/></w:pPr>' + draw + '</w:p>'

# ---------------- IEEE three-line table ----------------
def _cell(w_pt, style, txt, jc, header=False, bold=False):
    bord = ('<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tcBorders>'
            if header else '')
    return ('<w:tc><w:tcPr><w:tcW w:w="%dpt" w:type="dxa"/>%s<w:vAlign w:val="center"/></w:tcPr>'
            '<w:p><w:pPr><w:pStyle w:val="%s"/><w:jc w:val="%s"/></w:pPr>%s</w:p></w:tc>'
            ) % (w_pt, bord, style, jc, run(txt, b=bold))

def table(widths_pt, header, rows):
    """IEEE style: rules above/below header and at the bottom only; no vertical rules."""
    borders = ('<w:tblBorders>'
               '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
               '<w:start w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
               '<w:end w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
               '</w:tblBorders>')
    tblpr = ('<w:tblPr><w:tblW w:w="0pt" w:type="dxa"/><w:jc w:val="center"/>' + borders +
             '<w:tblLayout w:type="fixed"/>'
             '<w:tblLook w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" '
             'w:noHBand="0" w:noVBand="0"/></w:tblPr>')
    grid = '<w:tblGrid>' + ''.join('<w:gridCol w:w="%dpt"/>' % w for w in widths_pt) + '</w:tblGrid>'
    hr = ('<w:tr><w:trPr><w:cantSplit/><w:tblHeader/><w:jc w:val="center"/></w:trPr>' +
          ''.join(_cell(widths_pt[i], "tablecolhead", c, "center", header=True)
                  for i, c in enumerate(header)) + '</w:tr>')
    body = ''
    for r in rows:
        tcs = ''.join(_cell(widths_pt[i], "tablecopy", c, "start" if i == 0 else "center")
                      for i, c in enumerate(r))
        body += '<w:tr><w:trPr><w:cantSplit/><w:jc w:val="center"/></w:trPr>' + tcs + '</w:tr>'
    return '<w:tbl>' + tblpr + grid + hr + body + '</w:tbl>'

def tcaption(txt):
    # style 'tablehead' is centered + smallCaps + 8pt (IEEE caption above the table)
    return para("tablehead", [run(txt)])

# ================= CONTENT =================
P = []
P.append(h("papertitle", "Verifiable, Not Just Accurate: Faithfulness and a Predictability Ceiling in Causal-Chain GraphRAG for Provincial Flood Attribution"))
P.append(para("Author", [run("First Author"), run("   dept. / organization   city, country   email  ")]))
P.append(sectbreak(1))

P.append(para("Abstract", [run("Abstract\u2014", b=True), run("Retrieval-augmented systems for flood question answering are usually judged by predictive accuracy, but a correct answer is not necessarily a verifiable one. We study whether a GraphRAG system that traverses a real hydrological causal chain (rainfall to reservoir to river reach to downstream province) produces flood explanations that are more traceable to evidence than an entity-relation graph baseline and a vector-retrieval baseline over news. On five real Chao Phraya flood events (2021-2025; 23 provinces; 115 province-cases) scored against GISTDA satellite ground truth, the causal system attains a Matthews correlation coefficient (MCC) of +0.203 and near-complete evidence traceability (about 0.90), and is the only system with skill above chance: the entity baseline reaches a higher F1 (0.844 vs. 0.795) purely by predicting almost every province flooded, yet its MCC is 0.000 and its specificity is 0. Using a de-circularized gate whose thresholds come from gauge and rainfall climatology rather than the ground truth, a counterfactual necessity and sufficiency analysis quantifies each causal mechanism, and agreement among mechanisms raises precision from 0.782 to 0.833. Three tests and a soil-moisture probe show that the MCC of about 0.20 is a data ceiling, not a method ceiling. We report where our method loses, and we disclose the correction of an earlier evaluation artifact that had inflated F1.")]))
P.append(para("Keywords", [run("Keywords\u2014", b=True), run("GraphRAG; flood attribution; causal graph; faithfulness; Matthews correlation coefficient; de-circularized evaluation; probability of necessity and sufficiency; Chao Phraya basin")]))

P.append(h("Heading1", "Introduction"))
P.append(bt("Flood question-answering and early-warning systems are typically evaluated on predictive accuracy such as F1 or the critical success index. For decision support, however, the verifiability of an explanation matters as much as its correctness: an operator or a thesis committee needs to trace the answer to the question why is this province predicted to flood back to concrete evidence. Recent work argues that correctness is not the same as faithfulness in retrieval-augmented generation: a system can be right for reasons it cannot expose."))
P.append(bt("We present a causal-chain GraphRAG for provincial flood attribution in which every graph edge carries an explicit evidence property, so every prediction is traceable to a gauge, a dataset, and a timestamp. Fig. 1 summarizes the system. Our contributions are: first, a causal-chain GraphRAG with complete edge-level evidence traceability; second, an evaluation showing that at high flood base rates F1 is gamed by a trivial predict-all baseline, so MCC, specificity, and traceability are the appropriate criteria; third, a counterfactual necessity and sufficiency analysis of each hydrological mechanism; fourth, an empirical demonstration that the achievable skill of about 0.20 MCC is a data ceiling; and fifth, a transparent account of correcting an over-flagging evaluation artifact. We test two hypotheses: H1, that causal traversal yields more verifiable explanations than the baselines; and H2, that quality does not degrade with causal-chain length."))

P.append(figpara())
P.append(para("figurecaption", [run("Fig. 1. "), run("System overview. Real, de-circularized data feed a causal graph whose edges carry evidence; a two-signal gate (fluvial 2-year return stage; pluvial multi-duration rainfall) predicts provincial flooding; evaluation uses MCC, traceability, and a necessity and sufficiency analysis.")], jc="both"))

P.append(h("Heading1", "Related Work"))
P.append(bt("GraphRAG and multi-hop retrieval have been surveyed extensively, and faithfulness or attribution evaluation distinguishes an answer grounded in retrieved evidence from one that is merely correct. Causal graphs over river networks and flood knowledge graphs combined with language models and GIS provide the hydrological modeling context. For imbalanced classification, the Matthews correlation coefficient is preferred over F1 and accuracy. Counterfactual notions of necessity and sufficiency, and feature-attribution methods built on them, motivate our mechanism analysis. On the hydrology side, bankfull discharge recurs about every 1.5 to 2 years, return-period rainfall is estimated by Gumbel frequency analysis, the 2011 Chao Phraya flood had an estimated return period of 10 to 20 years, and probability calibration is unreliable with few samples."))

P.append(h("Heading1", "System and Method"))
P.append(h("Heading2", "Causal Graph"))
P.append(bt("The graph has five node types (RainStation, Reservoir, RiverReach, Confluence, Province) and directed edges that follow the direction of water flow (FEEDS, RUNOFF_TO, OVERFLOWS_TO, FLOWS_TO, INUNDATES). Every edge stores an evidence property recording its source station, dataset, and timestamp; this is the basis of the traceability claim. Hop count is the length of the shortest causal path from a rainfall source. The graph covers eight Chao Phraya sub-basins and 23 provinces."))
P.append(h("Heading2", "De-circularized Prediction Gate"))
P.append(bt("A province is predicted to flood if a fluvial or a pluvial signal fires and the province is not dike-protected. The fluvial signal snaps each reach to the gauge physically located on it and declares the reach over-topped when its 95th-percentile stage exceeds the gauge two-year return stage, estimated as the leave-one-event-out median annual maximum; this reflects bankfull onset, which recurs about every 1.5 to 2 years, and is lower than the high main-channel bank the river rarely reaches. The pluvial signal fires when a province peak 3-day or 30-day accumulated rainfall exceeds its own 10-year Gumbel return level, the 3-day term capturing cloudbursts and the 30-day term prolonged, saturating rain. Crucially, the ground truth is satellite flood extent while the gate uses river gauges and reanalysis rainfall, and every threshold is derived from the signal own climatology rather than from the ground truth; evaluation is leave-one-event-out."))
P.append(h("Heading2", "Baselines and Metrics"))
P.append(bt("Two baselines share the same province universe and evaluation set: an entity-relation graph retriever and a TF-IDF character n-gram retriever over a real Thai news corpus. We report traceability (the fraction of an explanation claims that trace to graph evidence, zero for both baselines by construction), MCC as the primary metric, and precision, recall, specificity, and F1. For each mechanism we compute a probability of necessity (the fraction of true positives lost when the mechanism is removed by intervention) and a probability of sufficiency (its precision when it fires), together with precision as a function of the number of agreeing mechanisms."))

P.append(h("Heading1", "Experimental Setup"))
P.append(bt("We evaluate on five Chao Phraya floods from 2021 to 2025, each over the same 23 provinces, for 115 province-cases in total. Ground truth is the per-province satellite flooded area with a fixed cutoff of 10,000 rai; the base rate of flooding is about 0.73. Data sources are GISTDA satellite (ground truth), thaiwater river gauges (fluvial signal), ERA5-Land rainfall via the open-meteo archive (pluvial signal), GADM 4.1 (geometry), and the Copernicus GLO-90 DEM (independent flow-direction validation). No structural parameters are learned; all thresholds are climatological and fixed before scoring."))

P.append(h("Heading1", "Results"))
P.append(tcaption("Table I.  Provincial Flood Attribution, Pooled Over Five Events (N = 115)"))
P.append(table([76, 30, 36, 32, 30, 36],
               ["System", "F1", "MCC", "Spec.", "Rec.", "Trace."],
               [["causal-graphrag", "0.795", "+0.203", "0.387", "0.81", "~0.90"],
                ["entity-graphrag", "0.844", "0.000", "0.000", "1.00", "0"],
                ["vector-rag", "0.096", "\u22120.497", "0.516", "0.06", "0"]]))
P.append(bt("Table I gives the pooled comparison. The entity baseline wins F1 but has zero skill (MCC = 0) because it predicts almost every province flooded (specificity 0); the causal system is the only one with MCC above zero and the only one whose predictions are traceable. Per-event causal MCC is +0.47, +0.52, +0.04, +0.37, and +0.17 for 2021 to 2025; we report all five, including the weak 2023 value."))
P.append(tcaption("Table II.  Mechanism Necessity and Sufficiency (Counterfactual Analysis)"))
P.append(table([96, 50, 46, 48],
               ["Mechanism", "Necessity", "Suffic.", "\u0394Recall"],
               [["Fluvial (2-yr stage)", "0.35", "0.79", "\u22120.29"],
                ["Pluvial 30-day", "0.21", "0.77", "\u22120.17"],
                ["Pluvial 3-day", "0.00", "0.85", "0.00"]]))
P.append(bt("Table II quantifies each mechanism by intervention. The fluvial signal is the most necessary and the 30-day term recovers prolonged-rain events; the 3-day term is redundant (necessity 0) but precise. Precision rises with agreement among mechanisms: 0.782 for at least one firing, 0.833 for at least two, and 0.667 for all three. Agreement among independent causal mechanisms is thus a traceable confidence signal the baselines cannot provide. As an early-warning extension, binary warning skill is POD 0.81, FAR 0.218, and CSI 0.660; a hop-based probability calibration shows a small Brier skill score over climatology (about +0.04) that is not statistically significant (event-level cluster bootstrap 95% CI from -0.54 to 0.16; p = 0.26; five events)."))

P.append(h("Heading1", "Discussion"))
P.append(h("Heading2", "F1 is misleading at high base rate"))
P.append(bt("At a 73% flood base rate, predicting every province earns F1 0.844 with MCC 0. F1 therefore rewards over-prediction, while MCC, specificity, and traceability separate a system that reasons from one that guesses. This is the operational meaning, in our setting, of the distinction between correctness and faithfulness."))
P.append(h("Heading2", "A ceiling in the data, not the method"))
P.append(tcaption("Table III.  Predictability-Ceiling Tests (Pooled MCC)"))
P.append(table([150, 90],
               ["Test", "MCC"],
               [["Learned logistic combiner (in-sample; LOEO)", "0.000; 0.000"],
                ["Principled rule variants (four rules)", "0.13 to 0.19"],
                ["Ground-truth cutoff sweep (10k to 200k rai)", "0.21 to 0.14"],
                ["Full model (fluvial and pluvial)", "+0.203"]]))
P.append(bt("Table III summarizes three tests that converge on an MCC of about 0.20. First, a learned logistic combiner over the continuous signal ratios collapses to predict-all (in-sample and leave-one-event-out MCC 0.0) at this base rate, so no learned combination beats the rule. Second, principled rule variants cluster at MCC 0.13 to 0.19, and removing the redundant 3-day term changes nothing, consistent with the necessity analysis. Third, a ground-truth cutoff sweep from 10,000 to 200,000 rai does not raise MCC, so the limit is not merely the base rate: the signals do not separate severity."))
P.append(h("Heading2", "What the residual misses are"))
P.append(bt("The false negatives concentrate in the 2023 and 2024 mainstem provinces. A soil-moisture probe (ERA5-Land root zone) shows these provinces were not soil-saturated (median event percentile 28% in 2023 and 38% in 2024, with Nakhon Sawan at the 0 to 7th percentile), so the misses are not saturation floods. This is consistent with hydraulic backwater at confluences and floodplain inundation below the main-channel bank; we state this as a hypothesis rather than a verified mechanism. Raising the ceiling would likely require a hydrodynamic model or denser confluence gauging, that is, new data rather than a better combiner."))
P.append(h("Heading2", "Honest correction"))
P.append(bt("An earlier version of this evaluation used a coarser gate that flagged a whole sub-basin whenever any of its gauges over-topped. That gate over-flagged and reported an F1 near 0.9, but it did not reproduce under the committed per-reach gate and was inconsistent with the physical record, since the mainstem gauge at Nakhon Sawan never exceeded its bank in 2021 to 2025. We replaced it with the de-circularized per-reach gate; the corrected gate scored F1 0.548, and the survey-grounded refinements raised it to 0.795. We report the old and new numbers together."))

P.append(h("Heading1", "Conclusion and Future Work"))
P.append(bt("The causal-chain GraphRAG is the only compared system that is both faithful (fully traceable) and skillful (MCC above zero) for provincial flood attribution; F1 alone is misleading here. H1 is supported by a traceability and MCC gap the baselines cannot close by construction, and H2 by a hop-invariant prediction footprint. The achievable skill is a data ceiling; future work includes hydrodynamic modeling and denser confluence gauging to capture backwater, district-level resolution to lower the base rate, more events for statistical significance, and other basins."))

P.append(h("Heading5", "Acknowledgment"))
P.append(bt("The authors used a large language model (Claude, Anthropic) to assist in drafting and editing the English text and to build verification and analysis scripts. The system design, causal-graph construction, data, experiments, metric choices, and interpretation of results are the authors own work, and the authors reviewed and take full responsibility for all content."))

P.append(h("Heading1", "References"))
refs = [
    "D. Edge et al., From local to global: A GraphRAG approach to query-focused summarization, arXiv:2404.16130, 2024.",
    "Correctness is not faithfulness in RAG attributions, arXiv:2412.18004, 2024.",
    "D. Chicco and G. Jurman, The advantages of the Matthews correlation coefficient over F1 score and accuracy in binary classification evaluation, BMC Genomics, vol. 21, no. 6, 2020.",
    "Feature attribution with necessity and sufficiency, arXiv:2402.08845, 2024; J. Pearl, Causality, 2nd ed., Cambridge Univ. Press, 2009.",
    "L. B. Leopold, A View of the River, Harvard Univ. Press, 1994.",
    "S. J. Gale and M. A. Saunders, The 2011 Thailand flood: climate causes and return periods, Weather, vol. 68, no. 9, 2013.",
    "A. Niculescu-Mizil and R. Caruana, Predicting good probabilities with supervised learning, in Proc. ICML, 2005.",
    "(Add GISTDA, thaiwater/HII, ERA5-Land/open-meteo, Copernicus GLO-90, and GADM data citations; verify every reference before submission.)",
]
for i, r in enumerate(refs, 1):
    P.append(para("BodyText", [run("[%d]  " % i), run(r)]))

BODY = ''.join(P) + '<w:sectPr>' + sect(2) + '</w:sectPr>'
docpath = os.path.join(U, "word", "document.xml")
doc = open(docpath, encoding="utf-8").read()
new = re.sub(r'<w:body>.*</w:body>', '<w:body>' + BODY + '</w:body>', doc, flags=re.S)
open(docpath, "w", encoding="utf-8").write(new)

os.makedirs(os.path.join(U, "word", "media"), exist_ok=True)
shutil.copy(os.path.join(BASE, "fig.png"), os.path.join(U, "word", "media", "image1.png"))
relf = os.path.join(U, "word", "_rels", "document.xml.rels")
rels = open(relf, encoding="utf-8").read()
if RID_IMG not in rels:
    imgrel = ('<Relationship Id="%s" Type="http://purl.oclc.org/ooxml/officeDocument/relationships/image" '
              'Target="media/image1.png"/>') % RID_IMG
    rels = rels.replace('</Relationships>', imgrel + '</Relationships>')
    open(relf, "w", encoding="utf-8").write(rels)
ctf = os.path.join(U, "[Content_Types].xml")
ct = open(ctf, encoding="utf-8").read()
if 'Extension="png"' not in ct:
    ct = ct.replace('<Default Extension="xml"',
                    '<Default Extension="png" ContentType="image/png"/><Default Extension="xml"')
    open(ctf, "w", encoding="utf-8").write(ct)

out = os.path.join(BASE, "paper.docx")
if os.path.exists(out):
    os.remove(out)
zf = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
for root, _, files in os.walk(U):
    for fn in files:
        fp = os.path.join(root, fn)
        zf.write(fp, os.path.relpath(fp, U).replace("\\", "/"))
zf.close()
print("wrote", out, "| blocks:", len(P), "| fig", CX, CY)
