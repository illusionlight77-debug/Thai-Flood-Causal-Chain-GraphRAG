"""Plan A — counterfactual necessity/sufficiency (PNS) + per-mechanism ablation.

ยกระดับ traceability ของ causal-graphrag จาก "0/1 vs baseline" เป็นการวัดเชิงปริมาณว่า
*แต่ละกลไก (mechanism) จำเป็น/เพียงพอ* แค่ไหนต่อคำทำนายที่ถูก — ด้วย counterfactual intervention
(ตัดสัญญาณออกทีละตัว แล้วดูว่าคำทำนายเปลี่ยนไหม). กรอบ: Pearl's Probability of Necessity/Sufficiency
(PNS); FANS (arXiv:2402.08845); "Correctness is not Faithfulness in RAG" (arXiv:2412.18004).

3 กลไก de-circularized ของโมเดล A:
  • fluvial   = แม่น้ำ/ลำน้ำล้น (reach p95 stage > 2-yr return, river_reach_overbank_*.json)
  • pluvial3  = ฝนกระหน่ำ (peak 3-day >= Gumbel T10, local_rain_*.json by_duration[3])
  • pluvial30 = ฝนตกยาว/ดินอิ่ม (peak 30-day >= Gumbel T10, local_rain_*.json by_duration[30])
คำทำนาย = (fluvial ∪ pluvial3 ∪ pluvial30) AND NOT protected.

นิยาม (pooled 5 เหตุการณ์, เทียบ GISTDA gold):
  • Necessity(m)  = สัดส่วน TP ที่ "หาย" เมื่อตัด m ออก = |TP_full − TP_without_m| / |TP_full|
                    (ยิ่งสูง = กลไกนี้ยิ่งจำเป็นต่อคำทำนายที่ถูก)
  • Sufficiency(m) = precision ของ m เดี่ยว ๆ = P(gold | m ยิงคนเดียว) (ยิ่งสูง = ยิงแล้วมักถูก)
  • Marginal ablation = ΔF1/ΔMCC/Δrecall เมื่อตัด m ออก

Usage: python -m src.eval.pns_ablation
"""
from __future__ import annotations

import json
import math

from src.config import settings

_PROC = settings.data_processed_dir
_WEB = settings.data_processed_dir.parent.parent / "web"
EVENTS = ["2021", "2022", "2023", "2024", "2025"]
PROTECTED = {"BANGKOK", "NONTHABURI"}

_EN = {"TAK": "Tak", "KAMPHAENGPHET": "Kamphaeng Phet", "SUKHOTHAI": "Sukhothai",
       "UTTARADIT": "Uttaradit", "PHITSANULOK": "Phitsanulok", "PHICHIT": "Phichit",
       "NAKHONSAWAN": "Nakhon Sawan", "UTHAITHANI": "Uthai Thani", "CHAINAT": "Chai Nat",
       "SINGBURI": "Sing Buri", "ANGTHONG": "Ang Thong", "AYUTTHAYA": "Ayutthaya",
       "LOPBURI": "Lopburi", "SARABURI": "Saraburi", "PHETCHABUN": "Phetchabun",
       "SUPHANBURI": "Suphan Buri", "NAKHONPATHOM": "Nakhon Pathom", "PATHUMTHANI": "Pathum Thani",
       "NONTHABURI": "Nonthaburi", "BANGKOK": "Bangkok", "CHIANGMAI": "Chiang Mai",
       "LAMPANG": "Lampang", "LAMPHUN": "Lamphun"}
_norm = lambda s: "".join(str(s).split()).lower()
_EN2PID = {_norm(v): k for k, v in _EN.items()}


def _reach_inundation() -> dict[str, list[str]]:
    """reach -> [pid] จาก fixtures (ภูมิศาสตร์จริง)."""
    import src.ingest.fixtures as fx
    out: dict[str, list[str]] = {}
    for r, lst in fx.REACH_INUNDATION.items():
        out[r] = [pid for pid, _ in lst]
    return out


def _event_signals(year: str, reach_inun: dict) -> tuple[set, dict, set, set]:
    """คืน (all_pids, gold, mechanism-fire-sets, ...) ต่อเหตุการณ์ (PID space)."""
    rb = json.loads((_PROC / f"river_reach_overbank_{year}.json").read_text("utf-8"))["overflow"]
    lr = json.loads((_PROC / f"local_rain_{year}.json").read_text("utf-8"))["local_rain"]
    gt = set(json.loads((_PROC / f"ground_truth_{year}.json").read_text("utf-8"))["gold_flooded"])
    allp = set(_EN)
    fluvial = {pid for r, on in rb.items() if on for pid in reach_inun.get(r, [])}

    def _dur(v, n):  # รองรับทั้ง over_{n}day และ by_duration[str(n)].over
        if f"over_{n}day" in v:
            return bool(v[f"over_{n}day"])
        return bool(v.get("by_duration", {}).get(str(n), {}).get("over"))

    pluvial3 = {pid for pid, v in lr.items() if _dur(v, 3)}
    pluvial30 = {pid for pid, v in lr.items() if _dur(v, 30)}
    return allp, gt, {"fluvial": fluvial, "pluvial3": pluvial3, "pluvial30": pluvial30}, allp


def _pred(mech_sets: dict, use: set[str]) -> set:
    p = set()
    for m in use:
        p |= mech_sets[m]
    return {x for x in p if x not in PROTECTED}


def _confusion(pred: set, gold: set, allp: set) -> tuple[int, int, int, int]:
    tp = len(pred & gold); fp = len(pred - gold); fn = len(gold - pred); tn = len(allp - gold - pred)
    return tp, fp, fn, tn


def _f1(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def _mcc(tp, fp, fn, tn):
    d = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / d if d else 0.0


def run() -> dict:
    reach_inun = _reach_inundation()
    mechs = ["fluvial", "pluvial3", "pluvial30"]
    # pooled counters
    agg_full = [0, 0, 0, 0]
    agg_abl = {m: [0, 0, 0, 0] for m in mechs}         # ablate m (use others)
    nec = {m: {"tp_full": 0, "tp_lost": 0} for m in mechs}
    suf = {m: {"alone_pred": 0, "alone_gold": 0} for m in mechs}   # m fires (alone-attributable)
    # PR curve by mechanism-count score
    score_rows = []   # (score = #mechanisms firing, is_gold)

    for y in EVENTS:
        allp, gold, ms, _ = _event_signals(y, reach_inun)
        full = _pred(ms, set(mechs))
        tp, fp, fn, tn = _confusion(full, gold, allp)
        for i, v in enumerate((tp, fp, fn, tn)):
            agg_full[i] += v
        for m in mechs:
            others = _pred(ms, set(mechs) - {m})
            for i, v in enumerate(_confusion(others, gold, allp)):
                agg_abl[m][i] += v
            # necessity: TP lost when m removed
            tp_full = full & gold
            tp_wo = others & gold
            nec[m]["tp_full"] += len(tp_full)
            nec[m]["tp_lost"] += len(tp_full - tp_wo)
            # sufficiency: precision of provinces where m fires (not protected)
            fires = {x for x in ms[m] if x not in PROTECTED}
            suf[m]["alone_pred"] += len(fires)
            suf[m]["alone_gold"] += len(fires & gold)
        # PR score rows
        for pid in allp:
            if pid in PROTECTED:
                continue
            sc = sum(pid in ms[m] for m in mechs)
            score_rows.append((sc, pid in gold))

    full_metrics = {"f1": round(_f1(*agg_full[:3]), 3), "mcc": round(_mcc(*agg_full), 3),
                    "recall": round(agg_full[0] / (agg_full[0] + agg_full[2]), 3) if agg_full[0] + agg_full[2] else 0,
                    "specificity": round(agg_full[3] / (agg_full[3] + agg_full[1]), 3) if agg_full[3] + agg_full[1] else 0}

    pns = {}
    for m in mechs:
        n = nec[m]["tp_lost"] / nec[m]["tp_full"] if nec[m]["tp_full"] else 0.0
        s = suf[m]["alone_gold"] / suf[m]["alone_pred"] if suf[m]["alone_pred"] else 0.0
        a = agg_abl[m]
        pns[m] = {"necessity": round(n, 3), "sufficiency": round(s, 3),
                  "pns": round(n * s, 3),
                  "ablated_f1": round(_f1(*a[:3]), 3), "ablated_mcc": round(_mcc(*a), 3),
                  "ablated_recall": round(a[0] / (a[0] + a[2]), 3) if a[0] + a[2] else 0,
                  "delta_f1": round(_f1(*a[:3]) - _f1(*agg_full[:3]), 3),
                  "delta_mcc": round(_mcc(*a) - _mcc(*agg_full), 3),
                  "delta_recall": round((a[0] / (a[0] + a[2]) if a[0] + a[2] else 0)
                                        - (agg_full[0] / (agg_full[0] + agg_full[2]) if agg_full[0] + agg_full[2] else 0), 3)}

    # PR curve: threshold on #mechanisms >= k for k=1,2,3
    pr = []
    tot_gold = sum(g for _, g in score_rows)
    for k in (1, 2, 3):
        tp = sum(1 for sc, g in score_rows if sc >= k and g)
        fp = sum(1 for sc, g in score_rows if sc >= k and not g)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / tot_gold if tot_gold else 0.0
        pr.append({"min_mechanisms": k, "precision": round(prec, 3), "recall": round(rec, 3),
                   "n_predicted": tp + fp})

    return {"note": "Counterfactual necessity/sufficiency (PNS) + per-mechanism ablation of causal-graphrag. "
            "Refs: Pearl PNS; FANS (2402.08845); correctness!=faithfulness (2412.18004).",
            "mechanisms": mechs, "full_model": full_metrics, "pns": pns, "pr_by_mechanism_count": pr}


def main() -> None:
    res = run()
    out = _PROC / "pns_ablation.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    fm = res["full_model"]
    print(f"full model: F1={fm['f1']} MCC={fm['mcc']} recall={fm['recall']} spec={fm['specificity']}")
    print(f"{'mechanism':11s} necessity suffic  PNS  | ablate -> dF1   dMCC  dRecall")
    for m, v in res["pns"].items():
        print(f"{m:11s}  {v['necessity']:.2f}     {v['sufficiency']:.2f}  {v['pns']:.2f} |"
              f"          {v['delta_f1']:+.3f} {v['delta_mcc']:+.3f} {v['delta_recall']:+.3f}")
    print("PR by #mechanisms firing:")
    for row in res["pr_by_mechanism_count"]:
        print(f"  >={row['min_mechanisms']}: precision={row['precision']} recall={row['recall']} (n={row['n_predicted']})")


if __name__ == "__main__":
    main()
