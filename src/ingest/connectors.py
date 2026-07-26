"""Connector stubs สำหรับแหล่งข้อมูลจริง D1–D4 (เฟส 1).

แต่ละ connector: ยืนยัน endpoint จริงก่อน → ดึงข้อมูล → คืน record ที่แนบ source
(station_id + timestamp + dataset) เพื่อไปเป็น Evidence.
ถ้า endpoint ล่ม → ทำ fixture เล็ก ๆ ใน data/processed แล้วบันทึกใน README > Bugs.
"""
from __future__ import annotations

from src.config import settings


def fetch_datagoth_water_levels(dataset_id: str) -> list[dict]:
    """D1 — CKAN datastore_search ที่ data.go.th (ระดับน้ำโทรมาตร)."""
    raise NotImplementedError(f"Phase 1: CKAN GET {settings.datagoth_ckan_base}/datastore_search")


def fetch_thaiwater_reservoirs() -> list[dict]:
    """D2 — thaiwater API (ระดับน้ำเขื่อน + spillway)."""
    raise NotImplementedError(f"Phase 1: GET {settings.thaiwater_api_base}/... reservoir")


def fetch_gistda_flood_extent(bbox: tuple, datetime_range: str) -> list[dict]:
    """D3 — GISTDA STAC search (flood extent = ground truth)."""
    raise NotImplementedError(f"Phase 1: STAC search {settings.gistda_stac_base}/search")


def fetch_basin_province_geometry() -> dict:
    """D4 — ขอบเขตลุ่มน้ำ/จังหวัด (shapefile/GeoJSON) สำหรับ geo phase."""
    raise NotImplementedError("Phase 1: download basin + province boundaries (data.go.th/GISTDA)")
