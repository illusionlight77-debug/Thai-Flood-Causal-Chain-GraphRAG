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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--per-sub", type=int, default=8)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
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
