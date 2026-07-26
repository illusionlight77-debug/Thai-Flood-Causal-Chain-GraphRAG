"""Connector แหล่งข้อมูลจริง D1–D4 (เฟส 1).

ยืนยัน endpoint แล้ว (2026-07-26):
  D1 data.go.th CKAN            → 200 ✔  (package_search / datastore_search)
  D2 thaiwater dam_daily        → 200 ✔  (www.thaiwater.net/api/v1/.../dam_daily)
                                   (path เดิม api.thaiwater.net/v1 = 404 → ดู README Bugs)
  D3 GISTDA STAC                → ต่อไม่ติด (000/404) → fallback fixture + Bug log
  D4 basin/province geometry    → ใช้ fixture geojson (เฟส 2 PIP)

ทุก connector best-effort + timeout; ล้มเหลว → คืน {} พร้อม flag เพื่อให้ run.py
รายงาน provenance และ pipeline เดินต่อด้วย fixture ได้ (กติกา CLAUDE.md §8).
"""
from __future__ import annotations

from typing import Any

import requests

from src.config import settings

TIMEOUT = 15
THAIWATER_DAM_DAILY = "https://www.thaiwater.net/api/v1/thaiwater/public/dam_daily"


def _get(url: str, **params) -> tuple[bool, Any]:
    try:
        r = requests.get(url, params=params or None, timeout=TIMEOUT,
                         headers={"User-Agent": "thai-flood-graphrag/0.1"})
        r.raise_for_status()
        return True, r.json()
    except Exception as exc:  # noqa: BLE001 — เก็บ error ไปรายงาน provenance
        return False, str(exc)


def ckan_package_search(query: str, rows: int = 5) -> tuple[bool, Any]:
    """D1 — ค้น dataset ที่ data.go.th (CKAN)."""
    ok, data = _get(f"{settings.datagoth_ckan_base}/package_search", q=query, rows=rows)
    if ok and isinstance(data, dict):
        return True, data.get("result", {})
    return ok, data


def thaiwater_dam_daily() -> tuple[bool, Any]:
    """D2 — ระดับน้ำ/การระบายเขื่อนรายวัน (thaiwater)."""
    return _get(THAIWATER_DAM_DAILY)


def gistda_stac_search(bbox: tuple, datetime_range: str) -> tuple[bool, Any]:
    """D3 — GISTDA STAC (flood extent). ยังต่อไม่ติด → คืน fail ให้ fallback fixture."""
    ok, data = _get(f"{settings.gistda_stac_base}/search",
                    bbox=",".join(map(str, bbox)), datetime=datetime_range)
    return ok, data


def probe_sources() -> dict[str, dict]:
    """เช็คสถานะ endpoint ทั้ง 4 → ไปกรอกตาราง provenance + README System All Links."""
    report: dict[str, dict] = {}

    ok, res = ckan_package_search("ระดับน้ำ โทรมาตร", rows=1)
    report["D1_data_go_th_ckan"] = {
        "ok": ok, "endpoint": f"{settings.datagoth_ckan_base}/package_search",
        "detail": (f"count={res.get('count')}" if ok and isinstance(res, dict) else str(res)[:120])}

    ok, res = thaiwater_dam_daily()
    n = len(res.get("data", res)) if ok and isinstance(res, dict) else None
    report["D2_thaiwater_dam_daily"] = {
        "ok": ok, "endpoint": THAIWATER_DAM_DAILY,
        "detail": (f"rows≈{n}" if ok else str(res)[:120])}

    ok, res = gistda_stac_search((99.0, 13.5, 101.0, 17.0), "2022-09-25/2022-10-15")
    report["D3_gistda_stac"] = {
        "ok": ok, "endpoint": f"{settings.gistda_stac_base}/search",
        "detail": ("ok" if ok else f"UNREACHABLE → fixture fallback ({str(res)[:60]})")}

    report["D4_basin_province_geometry"] = {
        "ok": True, "endpoint": "fixture data/processed/*.geojson",
        "detail": "provinces + reach outlets (EPSG:4326) → เฟส 2 PIP"}
    return report
