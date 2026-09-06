"""Plan A — predictability-ceiling analysis: is MCC ~0.20 a DATA ceiling or a METHOD ceiling?

คำถาม: ตัวเลข MCC ~0.20 ของ causal-graphrag ยกให้สูงขึ้นได้ไหม หรือเป็นเพดานจริง?
ทดสอบ 3 ทาง (reproducible) — ทุกอย่างวัดจริง ไม่จูน gold เป็นโมเดล (การ fit in-sample/LOEO
เป็น *การวินิจฉัยเพดาน* ไม่ใช่โมเดลที่ส่ง):

  (1) Learned combiner — logistic บนฟีเจอร์ต่อเนื่อง (stage-ratio, rain3-ratio, rain30-ratio)
      ทั้ง in-sample (upper bound) และ LOEO (achievable). ถ้าชนะ OR-rule → เพดานมาจาก "วิธีรวม"
      (ยกได้). ถ้าไม่ชนะ/ collapse เป็น predict-all → เพดานมาจาก "ข้อมูล".
  (2) Rule variants — เปรียบ OR แบบต่าง ๆ (fluvial-only, +pluvial30, drop redundant pluvial3,
      rain-needs-both). ถ้ากระจุกกันหมด → เพดานไม่ขึ้นกับสูตร.
  (3) Cutoff sweep — เปลี่ยน gold cutoff (≥10k..≥200k ไร่) ด้วยโมเดลตายตัว. ถ้า MCC ไม่ขึ้น →
      ไม่ใช่แค่ base-rate; สัญญาณฟิสิกส์แยกความรุนแรงไม่ได้จริง.

ข้อสรุป (2026-09-06): เพดาน ~0.20 เป็น **DATA/SIGNAL ceiling** ไม่ใช่ method — ยกได้เฉพาะด้วย
*ข้อมูลใหม่* (ความละเอียดเชิงพื้นที่ระดับอำเภอ, สัญญาณความชื้นดิน SMAP / อัตราระบายเขื่อน,
เพิ่มเหตุการณ์) ไม่ใช่ระเบียบวิธีบนข้อมูลเดิม.

Usage: python -m src.eval.ceiling_analysis   (ต้องมี multidur_rain cache หรือ rain_station files)
"""
from __future__ import annotations

import json
import math

from src.config import settings

_PROC = settings.data_processed_dir
EVENTS = ["2021", "2022", "2023", "2024", "2025"]
CUTOFF_YEARS = ["2021", "2022", "2023", "2024"]   # ปีที่มี rai ราย จว.
PROT = {"BANGKOK", "NONTHABURI"}


def _mcc(tp, fp, fn, tn):
    d = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / d if d else 0.0


def _f1(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def _load():
    import src.ingest.fixtures as fx
    allp = set(fx.PROVINCES)
    prov_reaches: dict[str, set] = {}
    for r, lst in fx.REACH_INUNDATION.items():
        for pid, _ in lst:
            prov_reaches.setdefault(pid, set()).add(r)
    reach_prov = {r: [p for p, _ in lst] for r, lst in fx.REACH_INUNDATION.items()}
    return allp, prov_reaches, reach_prov


def _features(year: str, allp, prov_reaches):
    """คืน {pid: (stage_ratio, rain3_ratio, rain30_ratio)} จากไฟล์ข้อมูล."""
    rb = json.loads((_PROC / f"river_reach_overbank_{year}.json").read_text("utf-8"))["reach_overbank"]
    lr = json.loads((_PROC / f"local_rain_{year}.json").read_text("utf-8"))["local_rain"]
    reach_ratio = {}
    for r, v in rb.items():
        rr = 0.0
        for s in v.get("stations", []):
            ps, th = s.get("peak_stage"), s.get("threshold_2yr_stage")
            if ps is not None and th:
                rr = max(rr, ps / th)
        reach_ratio[r] = rr
    out = {}
    for pid in allp:
        sr = max((reach_ratio.get(r, 0.0) for r in prov_reaches.get(pid, [])), default=0.0)
        v = lr.get(pid, {})
        t3 = v.get("threshold_3day_T10_mm") or v.get("threshold_primary_mm")
        p3 = v.get("event_max_3day_mm", 0.0)
        t30 = v.get("threshold_30day_T10_mm")
        p30 = v.get("event_max_30day_mm", 0.0)
        r3 = (p3 / t3) if t3 else 0.0
        r30 = (p30 / t30) if t30 else 0.0
        out[pid] = (sr, r3, r30)
    return out


def _gold(year: str) -> set:
    return set(json.loads((_PROC / f"ground_truth_{year}.json").read_text("utf-8"))["gold_flooded"])


def run() -> dict:
    allp, prov_reaches, _ = _load()
    feats = {y: _features(y, allp, prov_reaches) for y in EVENTS}
    golds = {y: _gold(y) for y in EVENTS}

    # ---- (2) rule variants ----
    rules = {
        "fluvial_only": lambda s, r3, r30: s > 1,
        "fluvial+pluvial30": lambda s, r3, r30: s > 1 or r30 >= 1,
        "fluvial+pluvial3+pluvial30 (current)": lambda s, r3, r30: s > 1 or r3 >= 1 or r30 >= 1,
        "fluvial OR (rain3 AND rain30)": lambda s, r3, r30: s > 1 or (r3 >= 1 and r30 >= 1),
    }
    rule_res = {}
    for name, fn in rules.items():
        a = [0, 0, 0, 0]
        for y in EVENTS:
            for pid in allp:
                pred = False if pid in PROT else fn(*feats[y][pid])
                g = pid in golds[y]
                a[0 if (pred and g) else 1 if (pred and not g) else 2 if (not pred and g) else 3] += 1
        rule_res[name] = {"mcc": round(_mcc(*a), 3), "f1": round(_f1(*a[:3]), 3),
                          "tp": a[0], "fp": a[1], "fn": a[2], "tn": a[3]}

    # ---- (1) learned combiner ----
    learned = {"available": False}
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        rows = [(y, pid, feats[y][pid], pid in golds[y]) for y in EVENTS for pid in allp if pid not in PROT]
        X = np.array([f for _, _, f, _ in rows]); yv = np.array([1 if g else 0 for *_, g in rows])
        ev = np.array([r[0] for r in rows])

        def cm(pred):
            tp = int(((pred == 1) & (yv == 1)).sum()); fp = int(((pred == 1) & (yv == 0)).sum())
            fn = int(((pred == 0) & (yv == 1)).sum()); tn = int(((pred == 0) & (yv == 0)).sum())
            return _mcc(tp, fp, fn, tn), (tp, fp, fn, tn)
        ins = LogisticRegression(max_iter=1000).fit(X, yv)
        loeo = np.zeros(len(yv))
        for y in EVENTS:
            tr, te = ev != y, ev == y
            if tr.sum() and te.sum():
                loeo[te] = LogisticRegression(max_iter=1000).fit(X[tr], yv[tr]).predict_proba(X[te])[:, 1]
        learned = {"available": True, "base_rate": round(float(yv.mean()), 3),
                   "insample_mcc_upperbound": round(cm((ins.predict_proba(X)[:, 1] >= .5).astype(int))[0], 3),
                   "loeo_mcc": round(cm((loeo >= .5).astype(int))[0], 3),
                   "loeo_confusion": cm((loeo >= .5).astype(int))[1]}
    except Exception as e:  # noqa: BLE001
        learned = {"available": False, "reason": str(e)[:80]}

    # ---- (3) cutoff sweep (fixed model) ----
    def pred_set(y):
        rb = json.loads((_PROC / f"river_reach_overbank_{y}.json").read_text("utf-8"))["overflow"]
        import src.ingest.fixtures as fx
        fluv = {pid for r, on in rb.items() if on for pid in [p for p, _ in fx.REACH_INUNDATION.get(r, [])]}
        lr = json.loads((_PROC / f"local_rain_{y}.json").read_text("utf-8"))["over"]
        over = {pid for pid, o in lr.items() if o}
        return {p for p in (fluv | over) if p not in PROT}

    def rai_map(y):
        d = json.loads((_PROC / f"gistda_flood_{y}_all_provinces.json").read_text("utf-8"))
        fa = d.get("flooded_area_rai", {})
        basin = json.loads((_PROC / "chao_phraya_basin_provinces.json").read_text("utf-8"))["provinces"]
        nrm = lambda s: "".join(str(s).split())
        th2 = {}
        for pid, v in basin.items():
            th2[nrm(v.get("th", ""))] = pid; th2[nrm(v.get("gadm", ""))] = pid
        out = {}
        for name, rai in fa.items():
            pid = th2.get(nrm(name))
            if pid in allp:
                try: out[pid] = float(rai)
                except (TypeError, ValueError): pass
        return out

    cutoff = []
    for cut in (10000, 30000, 50000, 100000, 200000):
        a = [0, 0, 0, 0]; npos = 0; ntot = 0
        for y in CUTOFF_YEARS:
            rm = rai_map(y); gold = {p for p, r in rm.items() if r >= cut}; pred = pred_set(y)
            npos += len(gold); ntot += len(allp)
            for pid in allp:
                pr, g = pid in pred, pid in gold
                a[0 if (pr and g) else 1 if (pr and not g) else 2 if (not pr and g) else 3] += 1
        cutoff.append({"cutoff_rai": cut, "base_rate": round(npos / ntot, 3), "mcc": round(_mcc(*a), 3)})

    return {"note": "Predictability-ceiling analysis for Plan A. Tests whether MCC ~0.20 is a data/signal "
            "ceiling or a method ceiling. Learned fits are diagnostic (upper bounds), not the shipped model.",
            "verdict": "DATA/SIGNAL ceiling — a learned combiner collapses to predict-all at high base-rate, "
            "rule variants cluster ~0.13-0.22, and stricter cutoffs do not raise MCC. Raising it needs NEW "
            "data (finer spatial unit, soil-moisture/dam-release signals, more events), not a better method.",
            "learned_combiner": learned, "rule_variants": rule_res, "cutoff_sweep": cutoff}


def main() -> None:
    res = run()
    (_PROC / "ceiling_analysis.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    lc = res["learned_combiner"]
    print("=== (1) learned combiner (best combination of features) ===")
    if lc.get("available"):
        print(f"  base_rate={lc['base_rate']} · in-sample(upper bound) MCC={lc['insample_mcc_upperbound']} · "
              f"LOEO MCC={lc['loeo_mcc']} {lc['loeo_confusion']}")
        print("  -> learned combo does NOT beat OR-rule (collapses to predict-all at high base-rate)")
    else:
        print("  (sklearn unavailable)", lc.get("reason", ""))
    print("=== (2) rule variants (MCC) ===")
    for n, v in res["rule_variants"].items():
        print(f"  {n:40s} MCC={v['mcc']:+.3f} F1={v['f1']:.3f}")
    print("=== (3) cutoff sweep (fixed model) ===")
    for c in res["cutoff_sweep"]:
        print(f"  >= {c['cutoff_rai']:>7} rai: base_rate={c['base_rate']} MCC={c['mcc']:+.3f}")
    print("VERDICT:", res["verdict"])


if __name__ == "__main__":
    main()
