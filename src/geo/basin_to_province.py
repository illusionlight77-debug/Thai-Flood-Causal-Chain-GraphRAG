"""เฟส 2 — GeoPandas point-in-polygon: ปลายลำน้ำ (reach outlet) → จังหวัดท้ายน้ำ
→ สร้าง INUNDATES edges (+evidence). และ overlay flood extent → gold provinces.

กติกาเหล็ก (skill geo-basin-to-province):
  reproject ทุกชั้นเป็น CRS เดียว (EPSG:32647) ก่อน sjoin — CRS ไม่ตรง = จับจังหวัดผิด.
ทุก INUNDATES edge แนบ evidence = {station_id: reach_id, timestamp: layer_date, dataset: D4/D3}.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd

from src.config import settings

CRS = settings.project_crs  # EPSG:32647 (UTM 47N)


def _load(name: str) -> gpd.GeoDataFrame:
    path = settings.data_processed_dir / name
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")  # fixture เป็น lat/lon
    return gdf.to_crs(CRS)


def reach_to_province() -> gpd.GeoDataFrame:
    """sjoin จุดปลายน้ำ → จังหวัด (predicate='within'). คืน mapping reach→province."""
    outlets = _load("reach_outlets.geojson")
    provinces = _load("provinces.geojson")[["prov_id", "name_en", "geometry"]]
    pip = gpd.sjoin(outlets, provinces, how="left", predicate="within")
    # กติกา skill: ห้ามมี reach ที่ join แล้วได้ province = NaN (จุดหลุดขอบเขต = CRS/geom พัง)
    unresolved = pip[pip["prov_id"].isna()]
    if len(unresolved):
        raise ValueError(f"{len(unresolved)} reach outlet หลุด polygon จังหวัด — ตรวจ CRS/geometry")
    return pip


def build_inundates_edges() -> list[dict]:
    """(:RiverReach)-[:INUNDATES {threshold, evidence}]->(:Province)."""
    pip = reach_to_province()
    edges: list[dict] = []
    for _, row in pip.iterrows():
        edges.append({
            "type": "INUNDATES",
            "src": str(row["reach_id"]),
            "dst": str(row["prov_id"]),
            "threshold": float(row["threshold"]),
            "evidence": {"station_id": str(row["reach_id"]), "timestamp": str(row["layer_date"]),
                         "dataset": "D4/basin+province PIP + D3/GISTDA extent"},
        })
    return edges


def gold_provinces_from_flood() -> set[str]:
    """overlay GISTDA flood extent (D3) × province → set จังหวัด gold สำหรับ eval."""
    # เอาเฉพาะ geometry ของ flood เพื่อเลี่ยงชื่อคอลัมน์ชนกัน (prov_id มีทั้งสองชั้น)
    flood = _load("gistda_flood_extent.geojson")[["geometry"]]
    provinces = _load("provinces.geojson")[["prov_id", "name_en", "geometry"]].copy()
    provinces["prov_area"] = provinces.geometry.area
    hit = gpd.overlay(provinces, flood, how="intersection", keep_geom_type=True)
    # จังหวัด "ท่วม" = พื้นที่ที่ทับ flood extent >= 50% ของพื้นที่จังหวัด
    #   (กัน sliver ตามแนวเขตแดนของ polygon จริงที่อยู่ติดกัน — 1 m² น้อยเกินสำหรับ geom จริง)
    hit["frac"] = hit.geometry.area / hit["prov_area"]
    flooded = hit[hit["frac"] >= 0.5]
    return {str(x) for x in flooded["prov_id"].unique()}


def main() -> Path:
    edges = build_inundates_edges()
    out = settings.data_processed_dir / "inundates_edges.json"
    out.write_text(json.dumps(edges, ensure_ascii=False, indent=2), "utf-8")
    gold = sorted(gold_provinces_from_flood())
    (settings.data_processed_dir / "gold_provinces.json").write_text(
        json.dumps(gold, ensure_ascii=False, indent=2), "utf-8")
    print(f"INUNDATES edges={len(edges)}  gold_provinces={gold}")
    return out


if __name__ == "__main__":
    main()
