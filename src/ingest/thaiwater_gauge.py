"""Roadmap B — lever 1 (SELF-SERVICE): ดึงระดับน้ำ *ย้อนหลัง* ต่อสถานีจาก thaiwater API v3
→ per-sub-basin over-bank gate (independent of GISTDA satellite gold, de-circularized).

พบว่า SPA thaiwater เรียก API สาธารณะ (ไม่ต้อง key):
  waterlevel_load                → สถานีทั้งหมด (oldcode, id, min_bank, sub-basin)
  waterlevel_graph?station_type=tele_waterlevel&station_id=..&start_date=..&end_date=..
                                 → timeseries + min_bank/warning/critical  ← ย้อนหลังได้!

กฎ gate (เหมือน rid_bulletin.py / gate 2565): สถานีใดในลุ่มน้ำ 'พีค > min_bank' (ล้นตลิ่ง)
→ ลุ่มน้ำนั้น overflow=true. รหัสนำ P/W/Y/N/C/S/T → ปิง/วัง/ยม/น่าน/เจ้าพระยา/ป่าสัก/ท่าจีน.

Usage:
    python -m src.ingest.thaiwater_gauge --event 2024 --start 2024-09-15 --end 2024-10-20 --write
    python -m src.ingest.thaiwater_gauge --event 2025 --start 2025-10-25 --end 2025-11-20 --write
"""
from __future__ import annotations

import argparse
import json
import re
import time

import requests

from src.config import settings

BASE = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/"
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.thaiwater.net/"}
PREFIX = {"P": "Ping", "W": "Wang", "Y": "Yom", "N": "Nan",
          "C": "ChaoPhraya", "S": "Pasak", "T": "ThaChin"}

# --mode reach: control/index gauge ต่อ reach (survey: NHDPlus snapping + NWS index gauge).
# กติกา: reach ล้น = สถานีที่ *อยู่บน reach นั้นจริง* สถานีใดสถานีหนึ่ง peak > ตลิ่ง (stage>min_bank)
# หรือ discharge>qmax. peak ใช้ *95th percentile* กัน sensor spike (เช่น C.3 เด้ง 23 ม. จาก 2 ม.).
#
# แก้บั๊ก mapping (2026-09-06): เดิม RR-CP-UPPER + RR-CP-L1 ชี้ C.13 ทั้งคู่ (เขื่อนเจ้าพระยาจุดเดียว)
# → พลาดสถานีที่อยู่บน reach จริง (นครสวรรค์=C.2, สิงห์บุรี=C.3, อ่างทอง=C.7A, อยุธยา=C.35/36/67).
# ตอนนี้ snap แต่ละ reach เข้ากับสถานีที่ตั้งอยู่บน reach นั้น (ตามที่ตั้งจริง ไม่ได้ดู gold).
REACH_GAUGES = {  # reach -> [(oldcode, station_id), ...] สถานีที่ตั้งอยู่บน reach นั้น
    "RR-PING": [("P.7A", 2900)], "RR-WANG": [("W.4A", 3018)], "RR-YOM": [("Y.16", 2941)],
    "RR-NAN": [("N.67", 2821)], "RR-SAKAEKRANG": [("SKG002", 595)],
    "RR-CP-UPPER": [("C.2", 2795)],                       # ค่ายจิรประวัติ นครสวรรค์
    "RR-CP-L1": [("C.3", 2723), ("C.7A", 2626)],          # บ้านบางพุทรา สิงห์บุรี · บ้านบางแก้ว อ่างทอง
    "RR-CP-L2": [("C.35", 2609), ("C.36", 2611), ("C.67", 1095849)],  # ป้อมเพชร/บางหลวงโดด/หัวเวียง อยุธยา
    "RR-CP-L3": [("C.12", 2599), ("C.37", 2608)],         # สามเสน กทม. · บ้านบางบาล (ท้ายอยุธยา)
    "RR-PASAK": [("S.26", 2624)], "RR-THACHIN": [("T.1", 2676)],
}
# backward-compat: reach -> control gauge เดี่ยว (ตัวแรกของ list) สำหรับโค้ดเก่าที่อ้าง REACH_GAUGE
REACH_GAUGE = {r: gs[0] for r, gs in REACH_GAUGES.items()}


def station_index() -> dict[str, list[dict]]:
    """{subbasin: [{oldcode, id, min_bank}]} จาก waterlevel_load (สถานีในลุ่มเจ้าพระยา 7 สาขา)."""
    d = requests.get(BASE + "waterlevel_load", headers=H, timeout=60).json()
    idx: dict[str, list[dict]] = {}
    for x in d["waterlevel_data"]["data"]:
        s = x.get("station") or {}
        oc = s.get("tele_station_oldcode") or ""
        m = re.match(r"^([A-Z])\.", oc)
        if not m or m.group(1) not in PREFIX:
            continue
        idx.setdefault(PREFIX[m.group(1)], []).append(
            {"oldcode": oc, "id": s.get("id"), "min_bank": s.get("min_bank")})
    return idx


def peak_over_bank(station_id: int, start: str, end: str) -> dict | None:
    """คืน {peak, min_bank, over_bank, peak_dt} หรือ None ถ้าไม่มีข้อมูล."""
    try:
        r = requests.get(BASE + "waterlevel_graph", headers=H, timeout=60,
                         params={"station_type": "tele_waterlevel", "station_id": station_id,
                                 "start_date": start, "end_date": end})
        d = r.json().get("data") or {}
    except Exception:  # noqa: BLE001
        return None
    g = [p for p in (d.get("graph_data") or []) if p.get("value") is not None]
    mb = d.get("min_bank")
    if not g or mb is None:
        return None
    pk = max(g, key=lambda p: float(p["value"]))
    return {"peak": round(float(pk["value"]), 2), "min_bank": float(mb),
            "over_bank": float(pk["value"]) > float(mb), "peak_dt": pk["datetime"]}


def event_overflow(event: str, start: str, end: str, per_sub: int = 8) -> dict:
    idx = station_index()
    subs: dict[str, dict] = {}
    for sub, stations in idx.items():
        cur = {"overflow": False, "stations": []}
        for st in stations[:per_sub]:
            if st["id"] is None:
                continue
            res = peak_over_bank(st["id"], start, end)
            time.sleep(0.4)
            if not res:
                continue
            cur["overflow"] = cur["overflow"] or res["over_bank"]
            cur["stations"].append({"station": st["oldcode"], **res})
        subs[sub] = cur
    return {"_meta": {"description": f"Sub-basin over-bank gate for {event} — from thaiwater API v3 "
                      "river-gauge timeseries (peak vs min_bank), independent of GISTDA satellite gold.",
                      "source": f"{BASE}waterlevel_graph ({start}..{end})",
                      "rule": "any station in a sub-basin with peak > min_bank -> overflow"},
            # key ที่ fixtures.py อ่าน: subbasin_overbank[sub].overflow
            "subbasin_overbank": {k: {"overflow": v["overflow"], "stations": v["stations"]}
                                  for k, v in subs.items()},
            "overflow": {k: v["overflow"] for k, v in subs.items()}}


def _p95(vals: list[float]) -> float | None:
    """95th-percentile peak (กัน sensor spike แทน max())."""
    if not vals:
        return None
    s = sorted(vals)
    k = max(0, int(round(0.95 * (len(s) - 1))))
    return s[k]


def reach_signal(sid: int, start: str, end: str) -> dict | None:
    """สถานีเดี่ยว: over = (p95 discharge > qmax) ถ้ามี, ไม่งั้น (p95 stage > min_bank). ใช้ p95 กัน spike."""
    try:
        d = requests.get(BASE + "waterlevel_graph", headers=H, timeout=60,
                         params={"station_type": "tele_waterlevel", "station_id": sid,
                                 "start_date": start, "end_date": end}).json().get("data") or {}
    except Exception:  # noqa: BLE001
        return None
    g = d.get("graph_data") or []
    stages = [float(p["value"]) for p in g if p.get("value") is not None]
    dis = [float(p["discharge"]) for p in g if p.get("discharge") is not None]
    mb, qmax = d.get("min_bank"), d.get("qmax")
    peak_stage = round(_p95(stages), 2) if stages else None
    peak_dis = round(_p95(dis), 0) if dis else None
    # ตลิ่ง (stage>min_bank) เป็นเกณฑ์หลัก (ตรงกับ "ล้นตลิ่ง"); discharge>qmax เป็น fallback ถ้าไม่มีระดับ
    if peak_stage is not None and mb is not None:
        over = peak_stage > float(mb)
        basis = f"stage {peak_stage}{'>' if over else '<='}bank {mb}"
    elif peak_dis is not None and qmax is not None:
        over = peak_dis > float(qmax)
        basis = f"discharge {peak_dis}{'>' if over else '<='}qmax {qmax}"
    else:
        return None
    return {"over_bank": over, "basis": basis, "peak_stage": peak_stage,
            "min_bank": mb, "peak_discharge": peak_dis, "qmax": qmax}


def event_reach_overflow(event: str, start: str, end: str) -> dict:
    """per-reach gate: reach ล้น = สถานีที่อยู่บน reach นั้น *สถานีใดสถานีหนึ่ง* ล้นตลิ่ง (p95>bank).
    key `reach_overbank` ให้ fixtures อ่าน. de-circularized (ไม่ดู gold), snap สถานีตามที่ตั้งจริง."""
    reach = {}
    for r, gauges in REACH_GAUGES.items():
        stations = []
        over_any = False
        for oldcode, sid in gauges:
            res = reach_signal(sid, start, end)
            time.sleep(0.35)
            if res:
                stations.append({"gauge": oldcode, **res})
                over_any = over_any or bool(res["over_bank"])
        fired = next((s for s in stations if s["over_bank"]), stations[0] if stations else {})
        reach[r] = {"overflow": over_any, "gauge": fired.get("gauge"),
                    "basis": fired.get("basis"), "stations": stations}
    return {"_meta": {"description": f"Per-reach over-bank gate for {event} — gauges snapped to each reach "
                      "(thaiwater API v3): reach overflows if ANY on-reach gauge p95-stage>min_bank. "
                      "p95 guards sensor spikes. Independent of GISTDA gold (de-circularized). "
                      "Refs: NHDPlus snapping, NWS index gauge. Fixed 2026-09-06: per-reach snapping "
                      "(was C.13 for all CP mainstem).",
                      "source": f"{BASE}waterlevel_graph ({start}..{end})"},
            "reach_overbank": reach,
            "overflow": {r: v["overflow"] for r, v in reach.items()}}


def _p95_season(sid: int, year: int) -> float | None:
    try:
        d = requests.get(BASE + "waterlevel_graph", headers=H, timeout=60,
                         params={"station_type": "tele_waterlevel", "station_id": sid,
                                 "start_date": f"{year}-08-01", "end_date": f"{year}-11-15"}).json().get("data") or {}
    except Exception:  # noqa: BLE001
        return None
    return _p95([float(p["value"]) for p in d.get("graph_data", []) if p.get("value") is not None])


def build_returnperiod_gates(events: list[int], clim_years: list[int]) -> None:
    """gate ต่อ reach จาก **2-yr return stage** (median annual-max p95, leave-one-event-out).
    flood-onset = bankfull recurrence ~1.5–2 ปี (Leopold 1994) — ต่ำกว่าหมุดตลิ่งช่องหลักที่สูง (levee).
    de-circularized (stage climatology, ไม่ดู gold), prequential (LOEO). ดู docs/HISTORY (2026-09-06)."""
    import statistics as _stat
    # p95 stage ต่อ (reach, gauge) ต่อปี
    hist: dict[str, dict[int, float]] = {}
    for r, gauges in REACH_GAUGES.items():
        for oc, sid in gauges:
            yr = {}
            for y in sorted(set(clim_years) | set(events)):
                pk = _p95_season(sid, y)
                time.sleep(0.3)
                if pk is not None:
                    yr[y] = pk
            hist[f"{r}|{oc}"] = yr
    for Y in events:
        reach = {}
        for r, gauges in REACH_GAUGES.items():
            over = False
            stations = []
            fired = None
            for oc, sid in gauges:
                yr = hist.get(f"{r}|{oc}", {})
                others = [yr[y] for y in yr if y != Y]
                if len(others) >= 2 and Y in yr:
                    thr = round(_stat.median(others), 2)   # ~2-yr return (bankfull)
                    ov = yr[Y] > thr
                    st = {"gauge": oc, "peak_stage": round(yr[Y], 2), "threshold_2yr_stage": thr,
                          "over_bank": ov, "basis": f"stage {round(yr[Y], 2)}{'>' if ov else '<='}"
                          f"2yr-return {thr} (bankfull, LOEO)"}
                    stations.append(st)
                    over = over or ov
                    if ov and fired is None:
                        fired = st
            base = fired or (stations[0] if stations else {})
            reach[r] = {"overflow": over, "gauge": base.get("gauge"),
                        "basis": base.get("basis"), "stations": stations}
        doc = {"_meta": {"description": f"Per-reach over-bank gate {Y} — event p95 stage > gauge's own "
               "2-yr return stage (median annual-max, LOEO). Flood-onset = bankfull recurrence ~1.5-2yr "
               "(Leopold 1994), lower than the high main-channel bank. De-circularized (stage climatology, "
               "not gold), prequential (LOEO). p95 guards spikes.",
               "source": f"{BASE}waterlevel_graph (Aug1-Nov15)"},
               "reach_overbank": reach,
               "overflow": {r: v["overflow"] for r, v in reach.items()}}
        (settings.data_processed_dir / f"river_reach_overbank_{Y}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
        print(f"[{Y}] return-period gate over={[r for r, v in reach.items() if v['overflow']]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--mode", choices=["reach", "subbasin", "returnperiod"], default="reach")
    ap.add_argument("--clim-years", nargs="+", type=int,
                    default=[2020, 2021, 2022, 2023, 2024, 2025], help="years for LOEO 2-yr stage")
    ap.add_argument("--per-sub", type=int, default=8)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    if a.mode == "returnperiod":
        build_returnperiod_gates([int(a.event)], a.clim_years)
        return
    if a.mode == "reach":
        res = event_reach_overflow(a.event, a.start, a.end)
        over = [k for k, v in res["overflow"].items() if v]
        print(f"[{a.event}] over-bank reaches: {over or 'none'}")
        for r, v in res["reach_overbank"].items():
            print(f"  {r:14s} {v['gauge']:7s} overflow={v['overflow']} · {v.get('basis','no data')}")
        if a.write:
            out = settings.data_processed_dir / f"river_reach_overbank_{a.event}.json"
            out.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
            print(f"wrote {out}")
        return
    res = event_overflow(a.event, a.start, a.end, a.per_sub)
    over = [k for k, v in res["overflow"].items() if v]
    print(f"[{a.event}] over-bank sub-basins: {over or 'none'}")
    for sub, v in res["subbasin_overbank"].items():
        obs = [f"{s['station']}={s['peak']}/{s['min_bank']}{'(OVER)' if s['over_bank'] else ''}"
               for s in v["stations"]]
        print(f"  {sub:11s} overflow={v['overflow']} · {', '.join(obs) or 'no data'}")
    if a.write:
        out = settings.data_processed_dir / f"river_reach_overbank_{a.event}.json"
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
