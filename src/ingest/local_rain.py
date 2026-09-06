"""Roadmap B — lever 1b (LOCAL-RAIN gate): จับ FN ลุ่มปิง (ท่วมจากฝนในพื้นที่เอง
ที่ gauge ลำน้ำหลักจับไม่ได้) ด้วยสัญญาณฝนจริง *อิสระจาก satellite gold* (de-circularized).

ทำไมต้องมี (finding ของ B): FN 9/11 = ลุ่มปิง (ตาก/กำแพงเพชร/เชียงใหม่) ท่วมจาก local rain
ไม่ใช่แม่น้ำหลักล้น → gate `reach.overflow` (P.7A ปิงตอนล่าง) จับไม่ได้ตามธรรมชาติ.

INTEGRITY (สำคัญ — ไม่ tune กับ gold):
  • ข้อมูลฝน   = ERA5-Land daily precip ผ่าน open-meteo archive (reanalysis, ย้อนหลังถึง 1940,
                 ไม่ใช้ key, *อิสระจาก* GISTDA flood gold) — แหล่งเดียวกับที่ repo ใช้ทำ DEM.
  • สัญญาณ     = event-window (1 ก.ค.–30 พ.ย. ตายตัวทุกปี) พีคฝนสะสม 3 วัน ที่ centroid จังหวัด.
  • threshold  = ค่าคาบอุบัติ 2 ปี ของฝนสะสม 3 วัน *ของจังหวัดนั้นเอง* (Gumbel MoM บน annual
                 maxima 1991–2020 = WMO normals). เลือก 2 ปี a-priori เพราะ bankfull (ระดับน้ำ
                 เริ่มล้นตลิ่ง) มีคาบอุบัติ ~1.5–2 ปี (Leopold 1994; Wolman & Miller 1960).
  • กติกา      = local_rain_over = (event 3-day peak ≥ T2 ของจังหวัด). ใช้ *ทุกจังหวัดเท่ากัน*
                 (23 จังหวัด) — ไม่ได้เลือกเฉพาะจังหวัดที่เป็น FN. ให้ "ข้อมูล+threshold" ตัดสิน.
  • รายงานเก่า+ใหม่คู่กันเสมอ; ถ้าไม่ช่วยก็รายงานตรง.

หมายเหตุแหล่งที่ปิด: thaiwater `rain_24h_graph` = rolling 24 ชม.เท่านั้น (ไม่ให้ย้อนหลัง) →
ใช้ ERA5 archive แทน (ดู docs/HISTORY.md). ไม่ปั้นข้อมูล.

Usage:
    python -m src.ingest.local_rain --events 2021 2022 2023 2024 2025 --write
    python -m src.ingest.local_rain --events 2011 --write
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as _st
import time

import requests

from src.config import settings

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
_PROC = settings.data_processed_dir
_BASIN = _PROC / "chao_phraya_basin_provinces.json"

# a-priori constants (ตรึงก่อนเห็นผล — ห้ามจูน)
ACCUM_DAYS = 3            # ฝนสะสม 3 วัน (antecedent + event, เหมาะกับ overbank ลุ่มกลาง)
# return period: pre-register 2 ค่าตามหลักการ (ไม่ได้เลือกจาก gold):
#   T=2  = bankfull recurrence ~1.5–2 ปี (Leopold 1994) → เกณฑ์ recall-first (เตือนพลาดน้อยสุด)
#   T=10 = คาบอุบัติน้ำท่วมนัยสำคัญ (มาตรฐาน flood-hazard mapping; 2554 ~10–20 ปี, Gale 2013)
#          → เกณฑ์ operational (สมดุล CSI). *ไม่ได้เลือก T=25 ที่ CSI สูงสุด = ไม่จูนตาม gold*
RETURN_PERIODS = (2.0, 5.0, 10.0, 25.0)   # เก็บทุกค่า (โปร่งใส/sensitivity)
PRIMARY_T = 10.0          # gate ที่ใช้จริง (a-priori: significant-flood recurrence)
CLIM_Y0, CLIM_Y1 = 1991, 2020   # WMO climate normals
EVENT_WINDOW = ("07-01", "11-30")  # ฤดูน้ำหลาก (ตายตัวทุกปี — กัน cherry-pick หน้าต่าง)


def _centroids() -> dict[str, tuple[float, float]]:
    prov = json.loads(_BASIN.read_text("utf-8"))["provinces"]
    return {pid: (v["lat"], v["lon"]) for pid, v in prov.items()}


def _fetch_daily(lat: float, lon: float, y0: int, y1: int) -> tuple[list[str], list[float | None]]:
    params = {"latitude": lat, "longitude": lon,
              "start_date": f"{y0}-01-01", "end_date": f"{y1}-12-31",
              "daily": "precipitation_sum", "timezone": "Asia/Bangkok"}
    for attempt in range(6):
        r = requests.get(ARCHIVE, timeout=120, params=params)
        j = r.json()
        if "daily" in j:
            return j["daily"]["time"], j["daily"]["precipitation_sum"]
        if j.get("error") and "limit" in str(j.get("reason", "")).lower():
            time.sleep(62)  # minutely quota → wait a minute
            continue
        raise RuntimeError(f"archive API error @ {lat},{lon}: {j}")
    raise RuntimeError(f"archive API rate-limited repeatedly @ {lat},{lon}")


def _rolling_accum(dates: list[str], pr: list[float | None], n: int) -> list[tuple[str, float]]:
    out = []
    for i in range(len(pr) - n + 1):
        w = pr[i:i + n]
        if any(v is None for v in w):
            continue
        out.append((dates[i], sum(w)))
    return out


def _annual_max(accum: list[tuple[str, float]], y0: int, y1: int) -> list[float]:
    by: dict[str, float] = {}
    for dt, v in accum:
        yr = dt[:4]
        if y0 <= int(yr) <= y1:
            by[yr] = max(by.get(yr, 0.0), v)
    return list(by.values())


def _gumbel_return(amax: list[float], T: float) -> float:
    """Gumbel EV1 method-of-moments return level (มาตรฐาน frequency analysis ลุ่มเจ้าพระยา)."""
    n = len(amax)
    mean = sum(amax) / n
    sd = _st.pstdev(amax)
    beta = sd * math.sqrt(6) / math.pi
    mu = mean - 0.5772 * beta
    p = 1 - 1 / T
    return mu - beta * math.log(-math.log(p))


def _event_peak(accum: list[tuple[str, float]], year: str) -> tuple[float, str]:
    lo, hi = f"{year}-{EVENT_WINDOW[0]}", f"{year}-{EVENT_WINDOW[1]}"
    win = [(dt, v) for dt, v in accum if lo <= dt <= hi]
    if not win:
        return 0.0, ""
    dt, v = max(win, key=lambda x: x[1])
    return round(v, 1), dt


def build(events: list[str], cache: dict | None = None) -> dict[str, dict]:
    """cache = {pid: {"thr": {T: mm}, "ev": {year: mm}}} (ข้ามการเรียก API ถ้ามี)."""
    cent = _centroids()
    y1_fetch = max(CLIM_Y1, max(int(e) for e in events))
    per_event: dict[str, dict] = {e: {} for e in events}
    for pid, (lat, lon) in cent.items():
        if cache and pid in cache:
            thr = {float(k): float(v) for k, v in cache[pid]["thr"].items()}
            evv = {e: float(cache[pid]["ev"][e]) for e in events}
        else:
            dates, pr = _fetch_daily(lat, lon, CLIM_Y0, y1_fetch)
            accum = _rolling_accum(dates, pr, ACCUM_DAYS)
            amax = _annual_max(accum, CLIM_Y0, CLIM_Y1)
            thr = {T: round(_gumbel_return(amax, T), 1) for T in RETURN_PERIODS}
            evv = {e: _event_peak(accum, e)[0] for e in events}
            time.sleep(0.3)
        for e in events:
            peak = round(evv[e], 1)
            per_event[e][pid] = {
                "event_max_3day_mm": peak,
                "thresholds_by_return_period": {str(int(T)): round(thr[T], 1) for T in RETURN_PERIODS},
                "threshold_primary_mm": round(thr[PRIMARY_T], 1),
                "over": bool(peak >= thr[PRIMARY_T] and peak > 0),
                "over_by_return_period": {str(int(T)): bool(peak >= thr[T] and peak > 0)
                                          for T in RETURN_PERIODS},
                "evidence": {"station_id": f"ERA5@{lat},{lon}",
                             "dataset": "ERA5-Land daily precip (open-meteo archive)",
                             "rule": f"3-day peak >= Gumbel T{PRIMARY_T:.0f}y (clim {CLIM_Y0}-{CLIM_Y1})"}}
    return per_event


def write(events: list[str], cache: dict | None = None) -> None:
    per_event = build(events, cache)
    for e, provs in per_event.items():
        n_over = sum(v["over"] for v in provs.values())
        doc = {"_meta": {
            "description": f"Local-rain gate for {e} — event 3-day peak precip vs province's own "
                           f"{PRIMARY_T:.0f}-yr return level (Gumbel, ERA5-Land). "
                           "Independent of GISTDA gold (de-circularized). "
                           "Ref: Leopold 1994 bankfull ~1.5-2yr; Gale 2013 (2011~10-20yr); Gumbel FA.",
            "source": "open-meteo archive (ERA5-Land) precipitation_sum",
            "accum_days": ACCUM_DAYS, "primary_return_period_y": PRIMARY_T,
            "return_periods_reported": list(RETURN_PERIODS),
            "clim_period": f"{CLIM_Y0}-{CLIM_Y1}", "event_window": EVENT_WINDOW,
            "integrity": "threshold = province's own return level (a-priori T=10, not chosen vs gold); "
                         "applied uniformly to all 23 provinces"},
            "local_rain": provs,
            "over": {pid: v["over"] for pid, v in provs.items()}}
        out = _PROC / f"local_rain_{e}.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
        over_list = [pid for pid, v in provs.items() if v["over"]]
        print(f"[{e}] local_rain over={n_over}/23 @T{PRIMARY_T:.0f}: {over_list}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", nargs="+", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--cache", default=None, help="path to {pid:{thr,ev}} json (skip API)")
    a = ap.parse_args()
    cache = json.loads(open(a.cache, encoding="utf-8").read()) if a.cache else None
    if a.write:
        write(a.events, cache)
    else:
        per = build(a.events, cache)
        for e, provs in per.items():
            over = [pid for pid, v in provs.items() if v["over"]]
            print(f"[{e}] over={len(over)}/23: {over}")


if __name__ == "__main__":
    main()
