"""Sentinel-1 SAR flood mapping ผ่าน Copernicus Data Space Ecosystem (openEO) — ไม่ต้องใช้บัตรเครดิต.
ทางเลือกแทน sentinel1_flood_extent.py (GEE) สำหรับคนที่ไม่อยากผูก billing กับ Google Cloud.

ผลลัพธ์: พื้นที่น้ำท่วมรายจังหวัด (ไร่) → data/processed/copernicus_flood_2022.json
เอาไป cross-check กับ ground_truth_2022.json (GISTDA) ได้ทันที.

────────────────────────────────────────────────────────────────────────────
SETUP (ครั้งเดียว ~10 นาที · ฟรี · ไม่ต้องใช้บัตร):
  1) สมัครฟรีที่  https://dataspace.copernicus.eu/  (กด Register — ใช้อีเมล ไม่ขอบัตร)
  2) pip install openeo
  3) รัน: python -m src.ingest.copernicus_flood_extent
     ครั้งแรกจะพิมพ์ URL + code ให้ → เปิดเบราว์เซอร์ล็อกอิน (device flow) → กลับมากด Enter
  (ไม่มีขั้นตอนผูกบัตร/ไม่มี quota เสียเงินสำหรับ openEO free tier)
────────────────────────────────────────────────────────────────────────────

วิธี (UN-SPIDER change-detection บน Sentinel-1 VH):
  ก่อนเหตุการณ์ vs ระหว่างเหตุการณ์ → อัตราส่วน backscatter (after/before) สูง = น้ำท่วมใหม่
  → threshold → mask → aggregate จำนวน pixel น้ำท่วมต่อ polygon จังหวัด (provinces.geojson/GADM) → ไร่.
หมายเหตุ: สคริปต์นี้ "พร้อมรัน" แต่ยังไม่ได้ทดสอบบนบัญชีจริง (ผมไม่มีบัญชี CDSE) — ถ้ารันแล้วติด
error ให้ส่ง log มา เดี๋ยว debug ให้. อาจต้องจูน DIFF_THRESHOLD (1.2–1.5) ตามพื้นที่.
"""
from __future__ import annotations

import json

from src.config import settings

OPENEO_URL = "openeo.dataspace.copernicus.eu"
AOI = {"west": 98.5, "south": 13.4, "east": 101.0, "north": 19.5}   # ลุ่มเจ้าพระยา
BEFORE = ["2022-08-15", "2022-09-10"]     # ก่อนเหตุการณ์ (แล้งกว่า)
AFTER = ["2022-09-28", "2022-10-14"]      # ช่วง NORU 2565 (ตรงกับ ground_truth_2022)
DIFF_THRESHOLD = 1.25                      # after/before ratio ที่ถือว่าน้ำท่วม
S1_PIXEL_M = 10.0                          # Sentinel-1 GRD ~10 m
RAI_PER_SQM = 1 / 1600.0
PROVINCES = settings.data_processed_dir / "provinces.geojson"   # GADM จริง (มี prov_id)
OUT = settings.data_processed_dir / "copernicus_flood_2022.json"


def run() -> dict:
    import openeo

    conn = openeo.connect(OPENEO_URL)
    conn.authenticate_oidc()   # device flow — เปิด browser ล็อกอิน (ไม่ขอบัตร)

    def s1_mean(temporal):
        return (conn.load_collection(
                    "SENTINEL1_GRD", spatial_extent=AOI, temporal_extent=temporal,
                    bands=["VH"])
                .sar_backscatter(coefficient="sigma0-ellipsoid")
                .mean_time())

    before = s1_mean(BEFORE)
    after = s1_mean(AFTER)
    flood = (after / before) > DIFF_THRESHOLD          # boolean mask (1 = น้ำท่วมใหม่)

    provinces = json.loads(PROVINCES.read_text("utf-8"))
    # sum ของ mask ต่อ polygon = จำนวน pixel ที่ท่วม
    agg = flood.aggregate_spatial(geometries=provinces, reducer="sum")
    raw = agg.execute()      # คืน dict/vector-cube

    # จับคู่ค่ากับ prov_id ตามลำดับ feature
    ids = [f["properties"]["prov_id"] for f in provinces["features"]]
    values = _extract_values(raw, len(ids))
    px_area = S1_PIXEL_M * S1_PIXEL_M
    return {pid: round((v or 0) * px_area * RAI_PER_SQM) for pid, v in zip(ids, values)}


def _extract_values(raw, n: int) -> list:
    """ดึงตัวเลขต่อ feature จากผล aggregate_spatial (โครงสร้างต่างกันได้ตามเวอร์ชัน)."""
    if isinstance(raw, dict):
        for key in ("data", "values", "features"):
            if key in raw:
                raw = raw[key]
                break
    out = []
    for item in (raw if isinstance(raw, (list, tuple)) else [raw]):
        while isinstance(item, (list, tuple)) and item:
            item = item[0]
        out.append(item if isinstance(item, (int, float)) else None)
    return (out + [None] * n)[:n]


def main() -> None:
    try:
        import openeo  # noqa: F401
    except ImportError:
        print(__doc__)
        print("\n[!] ยังไม่ได้ติดตั้ง openeo — `pip install openeo` แล้วทำตาม SETUP ด้านบน.")
        return
    try:
        areas = run()
    except Exception as exc:  # noqa: BLE001
        print(f"[!] รัน openEO ไม่สำเร็จ: {exc}\n    ส่ง log นี้มา เดี๋ยว debug ให้ (อาจต้อง authenticate ใหม่).")
        return
    OUT.write_text(json.dumps({"flooded_area_rai": areas,
                               "source": "Sentinel-1 SAR via Copernicus (openEO)",
                               "before": BEFORE, "after": AFTER,
                               "diff_threshold": DIFF_THRESHOLD}, ensure_ascii=False, indent=2), "utf-8")
    print(f"เขียนพื้นที่ท่วมรายจังหวัด (Copernicus) → {OUT}")
    for pid, rai in sorted(areas.items(), key=lambda x: -x[1]):
        print(f"  {pid:12s} {rai:>10,} ไร่")
    print("\nเทียบกับ data/processed/ground_truth_2022.json (GISTDA) เพื่อ cross-validate ได้.")


if __name__ == "__main__":
    main()
