# -*- coding: utf-8 -*-
"""Build the IEEE conference paper .docx on the provided Strict-OOXML template.
Structure and conventions follow the reference IEEE paper supplied by the author.
Tables use IEEE three-line rules (no vertical lines), widths in pt."""
import os, re, shutil, zipfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content as C

BASE = os.path.dirname(os.path.abspath(__file__))
U = os.path.join(BASE, "unpacked")
A = "http://purl.oclc.org/ooxml/drawingml/main"
PIC = "http://purl.oclc.org/ooxml/drawingml/picture"
RID_IMG = "rId100"
FIG_W, FIG_H = 1200, 1690
COL_PT = 240

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
    return '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>' + draw + '</w:p>'

def _cell(w_pt, style, txt, jc, header=False):
    bord = ('<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tcBorders>'
            if header else '')
    return ('<w:tc><w:tcPr><w:tcW w:w="%dpt" w:type="dxa"/>%s<w:vAlign w:val="center"/></w:tcPr>'
            '<w:p><w:pPr><w:pStyle w:val="%s"/><w:jc w:val="%s"/></w:pPr>%s</w:p></w:tc>'
            ) % (w_pt, bord, style, jc, run(txt))

def table(widths_pt, header, rows):
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

# ================= ASSEMBLE =================
P = []
P.append(h("papertitle", C.TITLE))
P.append(para("Author", [run("Anonymous Authors")]))
P.append(para("Author", [run("Affiliation omitted for blind review")]))
P.append(sectbreak(1))

P.append(para("Abstract", [run("Abstract—", b=True), run(C.ABSTRACT)]))
P.append(para("Keywords", [run("Keywords—", b=True), run(C.KEYWORDS)]))

P.append(h("Heading1", "Introduction"))
for p in C.INTRO:
    P.append(bt(p))

P.append(figpara())
P.append(para("figurecaption", [run("System overview: de-circularized data sources, the causal graph whose "
                                    "edges carry evidence, the two-signal gate, and the evaluation layer.")],
              jc="both"))

P.append(h("Heading1", "Related Work"))
for letter, title, body in C.RELATED:
    P.append(h("Heading2", title))
    P.append(bt(body))

P.append(h("Heading1", "Proposed System"))
for letter, title, body in C.SYSTEM:
    P.append(h("Heading2", title))
    P.append(bt(body))
    if letter == "C":
        P.append('<w:p><w:pPr><w:pStyle w:val="BodyText"/>'
                 '<w:tabs><w:tab w:val="center" w:pos="118pt"/><w:tab w:val="right" w:pos="240pt"/></w:tabs>'
                 '<w:ind w:firstLine="0pt"/></w:pPr>'
                 '<w:r><w:tab/></w:r>' + run(C.EQUATION) + '<w:r><w:tab/></w:r>' + run("(1)") + '</w:p>')
        P.append(bt(C.EQUATION_NOTE))

P.append(h("Heading1", "Experimental Setting"))
for p in C.SETTING:
    P.append(bt(p))

P.append(h("Heading1", "Results and Discussion"))
P.append(h("Heading2", "Main Comparison"))
P.append(para("tablehead", [run("Provincial Flood Attribution, Pooled Over Five Events (N = 115)")]))
P.append(table([76, 30, 36, 32, 30, 36],
               ["System", "F1", "MCC", "Spec.", "Rec.", "Trace."],
               [["causal-graphrag", "0.795", "+0.203", "0.387", "0.81", "~0.90"],
                ["entity-graphrag", "0.844", "0.000", "0.000", "1.00", "0"],
                ["vector-rag", "0.096", "−0.497", "0.516", "0.06", "0"]]))
P.append(bt(C.RESULTS_A))

P.append(h("Heading2", "Mechanism Necessity and Sufficiency"))
P.append(para("tablehead", [run("Mechanism Necessity and Sufficiency under Intervention")]))
P.append(table([96, 50, 46, 48],
               ["Mechanism", "Necessity", "Suffic.", "ΔRecall"],
               [["Fluvial (2-yr stage)", "0.35", "0.79", "−0.29"],
                ["Pluvial 30-day", "0.21", "0.77", "−0.17"],
                ["Pluvial 3-day", "0.00", "0.85", "0.00"]]))
P.append(bt(C.RESULTS_B))

P.append(h("Heading2", "A Ceiling in the Data, Not the Method"))
P.append(para("tablehead", [run("Predictability-Ceiling Tests (Pooled MCC)")]))
P.append(table([150, 90],
               ["Test", "MCC"],
               [["Learned logistic combiner (in-sample; LOEO)", "0.000; 0.000"],
                ["Four principled rule variants", "0.13 to 0.19"],
                ["Ground-truth threshold sweep (10k to 200k rai)", "0.21 to 0.14"],
                ["Proposed gate (fluvial and pluvial)", "+0.203"]]))
P.append(bt(C.RESULTS_C))

P.append(h("Heading2", "Early-Warning Extension"))
P.append(bt(C.RESULTS_D))

P.append(h("Heading2", "Discussion and Limitations"))
P.append(bt(C.DISCUSSION))
P.append(bt(C.LIMITATIONS))

P.append(h("Heading1", "Conclusion"))
P.append(bt(C.CONCLUSION))

P.append(h("Heading5", "Acknowledgment"))
P.append(bt(C.ACK))

P.append(h("Heading5", "References"))
def refrun(t):
    return ('<w:r><w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
            '<w:t xml:space="preserve">' + esc(t) + '</w:t></w:r>')
for i, r in enumerate(C.REFS, 1):
    P.append('<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:jc w:val="start"/>'
             '<w:tabs><w:tab w:val="left" w:pos="22pt"/></w:tabs>'
             '<w:ind w:left="22pt" w:hanging="22pt"/></w:pPr>'
             + refrun("[%d]" % i) + '<w:r><w:tab/></w:r>' + refrun(r) + '</w:p>')

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
words = sum(len(x.split()) for x in
            ([C.ABSTRACT] + C.INTRO + [b for _, _, b in C.RELATED] + [b for _, _, b in C.SYSTEM] +
             C.SETTING + [C.RESULTS_A, C.RESULTS_B, C.RESULTS_C, C.RESULTS_D, C.DISCUSSION,
                          C.LIMITATIONS, C.CONCLUSION, C.ACK]))
print("wrote", out, "| blocks:", len(P), "| body words ~", words)
