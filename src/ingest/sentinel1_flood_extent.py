"""Item 3a — Sentinel-1 SAR flood mapping ผ่าน Google Earth Engine (UN-SPIDER workflow).

สคริปต์นี้ *พร้อมรัน* แต่ต้องมี Google Earth Engine account ก่อน (ดู SETUP ด้านล่าง) —
environment ของ Claude Code รันไม่ได้เพราะไม่มี OAuth/บัญชี GEE. เมื่อรันสำเร็จจะได้
พื้นที่น้ำท่วมรายจังหวัด (ไร่) แบบเดียวกับ ground_truth_2022.json → เสียบเข้า pipeline ได้ทันที.

────────────────────────────────────────────────────────────────────────────
SETUP (ทำครั้งเดียว บนเครื่องผู้ใช้ ~15 นาที + รออนุมัติโปรเจกต์ ~1 วัน):
  1) สมัคร Google Earth Engine ฟรี: https://earthengine.google.com/signup  (เลือก noncommercial)
  2) สร้าง/เลือก Google Cloud project แล้วผูกกับ Earth Engine
  3) pip install earthengine-api geemap
  4) earthengine authenticate          # เปิด browser ให้ล็อกอิน (OAuth)
  5) แก้ EE_PROJECT ด้านล่างเป็น project id ของคุณ แล้ว:  python -m src.ingest.sentinel1_flood_extent
────────────────────────────────────────────────────────────────────────────

วิธี (UN-SPIDER "Recommended Practice: Flood Mapping with Sentinel-1"):
  ก่อนเหตุการณ์ vs หลังเหตุการณ์ → อัตราส่วน backscatter (after/before) สูง = น้ำท่วมใหม่
  → กรอง speckle, ตัดน้ำถาวร (JRC GSW), ตัดพื้นที่ลาดชัน (HydroSHEDS) → flood extent
  → รวมพื้นที่ต่อจังหวัด (GADM) เป็น "ไร่".
อ้างอิง: https://un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping
"""
from __future__ import annotations

import json

from src.config import settings

# ── config เหตุการณ์ (แก้ได้) ─────────────────────────────────────
EE_PROJECT = "YOUR_GEE_PROJECT_ID"          # <-- แก้เป็น project id ของคุณ
AOI_BBOX = [98.5, 13.4, 101.0, 19.5]         # ลุ่มเจ้าพระยา (lon/lat)
BEFORE = ("2022-08-15", "2022-09-10")        # ก่อนเหตุการณ์ (แล้งกว่า)
AFTER = ("2022-09-28", "2022-10-14")         # ช่วง NORU 2565 (ตรงกับ ground_truth_2022)
DIFF_THRESHOLD = 1.25                         # after/before ratio ที่ถือว่าน้ำท่วม (ปรับ 1.2–1.5)
RAI_PER_SQM = 1 / 1600.0                      # 1 ไร่ = 1,600 ตร.ม.
OUT = settings.data_processed_dir / "sentinel1_flood_2022.json"

# prov_id → GADM NAME_1 (ให้ตรงกับ src/ingest/fixtures.GADM_NAME)
GADM_NAME = {
    "TAK": "Tak", "PHITSANULOK": "Phitsanulok", "NAKHONSAWAN": "NakhonSawan",
    "CHAINAT": "ChaiNat", "SINGBURI": "SingBuri", "ANGTHONG": "AngThong",
    "AYUTTHAYA": "PhraNakhonSiAyutthaya", "PATHUMTHANI": "PathumThani",
    "NONTHABURI": "Nonthaburi", "BANGKOK": "BangkokMetropolis",
}


def run() -> dict:
    import ee

    ee.Initialize(project=EE_PROJECT)
    aoi = ee.Geometry.Rectangle(AOI_BBOX)

    def s1_mosaic(start, end):
        col = (ee.ImageCollection("COPERNICUS/S1_GRD")
               .filterBounds(aoi).filterDate(start, end)
               .filter(ee.Filter.eq("instrumentMode", "IW"))
               .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
               .select("VH"))
        return col.mosaic().clip(aoi).focal_median(50, "circle", "meters")  # speckle filter

    before = s1_mosaic(*BEFORE)
    after = s1_mosaic(*AFTER)
    ratio = after.divide(before)
    flood = ratio.gt(DIFF_THRESHOLD)

    # ตัดน้ำถาวร (JRC Global Surface Water: seasonality >= 5 เดือน/ปี)
    perm = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("seasonality").gte(5)
    flood = flood.where(perm, 0)
    # ตัดพื้นที่ลาดชัน > 5 องศา (น้ำไม่ขังจริง)
    slope = ee.Terrain.slope(ee.Image("WWF/HydroSHEDS/03VFDEM"))
    flood = flood.updateMask(slope.lt(5)).selfMask()

    provinces = ee.FeatureCollection("projects/sat-io/open-datasets/gadm/gadm41_1") \
        .filter(ee.Filter.eq("GID_0", "THA"))
    area_img = flood.multiply(ee.Image.pixelArea())  # ตร.ม. ต่อ pixel ที่ท่วม

    result: dict[str, float] = {}
    for pid, gadm in GADM_NAME.items():
        prov = provinces.filter(ee.Filter.eq("NAME_1", gadm)).geometry()
        sqm = area_img.reduceRegion(ee.Reducer.sum(), prov, scale=30,
                                    maxPixels=1e13).get("VH")
        result[pid] = round(ee.Number(sqm).getInfo() * RAI_PER_SQM)
    return result


def main() -> None:
    try:
        import ee  # noqa: F401
    except ImportError:
        print(__doc__)
        print("\n[!] ยังไม่ได้ติดตั้ง earthengine-api — ทำตาม SETUP ด้านบนก่อน.")
        return
    try:
        areas = run()
    except Exception as exc:  # noqa: BLE001
        print(f"[!] รัน GEE ไม่สำเร็จ: {exc}\n    ตรวจ SETUP (authenticate + EE_PROJECT).")
        return
    OUT.write_text(json.dumps({"flooded_area_rai": areas,
                               "source": "Sentinel-1 SAR via GEE (UN-SPIDER)",
                               "before": BEFORE, "after": AFTER,
                               "diff_threshold": DIFF_THRESHOLD}, ensure_ascii=False, indent=2), "utf-8")
    print(f"เขียนพื้นที่ท่วมรายจังหวัด (Sentinel-1) → {OUT}")
    for pid, rai in sorted(areas.items(), key=lambda x: -x[1]):
        print(f"  {pid:12s} {rai:>10,} ไร่")
    print("\nเทียบกับ data/processed/ground_truth_2022.json (GISTDA) เพื่อ cross-validate ได้.")


if __name__ == "__main__":
    main()
