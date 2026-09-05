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

# --mode reach: control/index gauge ต่อ reach (survey: NHDPlus snapping + NWS index gauge;
# C.2 = control หลักเจ้าพระยา). สายหลักที่มี discharge → ใช้ 'discharge > qmax' (qmax = ความจุมาตรฐาน RID,
# เหมือน bulletin C.13≥~2800) เพราะเขื่อนคุมระดับให้ต่ำกว่าหมุดตลิ่งได้แต่ปริมาณน้ำสูง; สาขาที่มีแต่ระดับ → stage>bank.
REACH_GAUGE = {  # reach -> (oldcode, station_id)
    "RR-PING": ("P.7A", 2900), "RR-WANG": ("W.4A", 3018), "RR-YOM": ("Y.16", 2941),
    "RR-NAN": ("N.67", 2821), "RR-SAKAEKRANG": ("SKG002", 595),
    # CP mainstem: ใช้ C.13 (เขื่อนเจ้าพระยา = master control structure, qmax 2720 = operational flood
    # threshold ~ bulletin C.13≥2800) เพราะ C.2 qmax 3735 คือ rated capacity สูงเกินจะเป็น flood onset
    "RR-CP-UPPER": ("C.13", 2744), "RR-CP-L1": ("C.13", 2744), "RR-CP-L2": ("C.35", 2609),
    "RR-CP-L3": ("C.37", 2608), "RR-PASAK": ("S.26", 2624), "RR-THACHIN": ("T.1", 2676),
}


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


def reach_signal(sid: int, start: str, end: str) -> dict | None:
    """control gauge ของ reach: over = (peak discharge > qmax) ถ้ามี, ไม่งั้น (peak stage > min_bank)."""
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
    peak_stage = round(max(stages), 2) if stages else None
    peak_dis = round(max(dis), 0) if dis else None
    if peak_dis is not None and qmax is not None:
        over = peak_dis > float(qmax)
        basis = f"discharge {peak_dis}>{qmax}" if over else f"discharge {peak_dis}<=qmax {qmax}"
    elif peak_stage is not None and mb is not None:
        over = peak_stage > float(mb)
        basis = f"stage {peak_stage}{'>' if over else '<='}bank {mb}"
    else:
        return None
    return {"over_bank": over, "basis": basis, "peak_stage": peak_stage,
            "min_bank": mb, "peak_discharge": peak_dis, "qmax": qmax}


def event_reach_overflow(event: str, start: str, end: str) -> dict:
    """per-reach gate จาก control gauge (survey-grounded). key `reach_overbank` ให้ fixtures อ่าน."""
    reach = {}
    for r, (oldcode, sid) in REACH_GAUGE.items():
        res = reach_signal(sid, start, end)
        time.sleep(0.4)
        reach[r] = {"overflow": bool(res["over_bank"]) if res else False,
                    "gauge": oldcode, **(res or {})}
    return {"_meta": {"description": f"Per-reach over-bank gate for {event} — control/index gauge per "
                      "reach from thaiwater API v3 (main-stream: discharge>qmax; tributary: stage>min_bank). "
                      "Independent of GISTDA gold (de-circularized). Refs: NHDPlus snapping, NWS index gauge.",
                      "source": f"{BASE}waterlevel_graph ({start}..{end})"},
            "reach_overbank": reach,
            "overflow": {r: v["overflow"] for r, v in reach.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--mode", choices=["reach", "subbasin"], default="reach")
    ap.add_argument("--per-sub", type=int, default=8)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
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
