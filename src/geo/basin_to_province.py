"""ลุ่มน้ำ/ปลายลำน้ำ → จังหวัดท้ายน้ำ (point-in-polygon) → INUNDATES edges.

กติกาเหล็ก (skill geo-basin-to-province): reproject ทุกชั้นเป็น CRS เดียวก่อน sjoin.
CRS ไม่ตรง = จับจังหวัดผิด = บั๊คเงียบที่สุดในงานนี้.
"""
from __future__ import annotations

from src.config import settings

CRS = settings.project_crs  # EPSG:32647 (UTM 47N)


def reach_to_province(reaches, provinces):  # noqa: ANN001 — GeoDataFrame (เฟส 2)
    """sjoin จุดปลายน้ำของ reach → จังหวัด (predicate='within'). คืน mapping."""
    raise NotImplementedError("Phase 2: gpd.sjoin(reaches.to_crs(CRS), provinces.to_crs(CRS))")


def gistda_flood_to_gold(flood, provinces):  # noqa: ANN001
    """overlay flood extent (D3) × province → set จังหวัด gold สำหรับ eval."""
    raise NotImplementedError("Phase 2: gpd.overlay(flood, provinces, how='intersection')")


def main() -> None:
    raise NotImplementedError("Phase 2: build INUNDATES edges from spatial join")


if __name__ == "__main__":
    main()
