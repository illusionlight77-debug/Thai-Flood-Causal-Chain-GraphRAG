"""GISTDA disaster API — flood features (real-time, Sentinel-1 based) ผ่าน api-gateway.

endpoint (จากคู่มือ manual_api.pdf):
  GET {GATEWAY}/resources/features/flood/{window}?pv_idn=&ap_idn=&tb_idn=&limit=&offset=
  header: API-Key: <GISTDA_DATA_KEY>   → คืน GeoJSON (features มี f_area, pv_tn, ap_tn, …)
window = 1day | 3days | 7days | 30days (พื้นที่น้ำท่วมย้อนหลัง N วันล่าสุด — เป็น "ปัจจุบัน")

หมายเหตุ: นี่คือ flood *ปัจจุบัน* (real-time) ไม่ใช่เหตุการณ์ย้อนหลัง 2564/2565 — ใช้กับ
layer สดในหน้า UI + ต่อยอด early-warning (B2). key อ่านจาก settings (ไม่ hardcode).
"""
from __future__ import annotations

from functools import lru_cache

import requests

from src.config import settings

# รหัสจังหวัด (changwat code) ของ 10 จังหวัดในกราฟ → ใช้ filter pv_idn
PV_IDN = {
    "BANGKOK": 10, "NONTHABURI": 12, "PATHUMTHANI": 13, "AYUTTHAYA": 14,
    "ANGTHONG": 15, "SINGBURI": 17, "CHAINAT": 18, "NAKHONSAWAN": 60,
    "TAK": 63, "PHITSANULOK": 65,
}
WINDOWS = ("1day", "3days", "7days", "30days")


def fetch_flood(window: str = "30days", pv_idn: int | None = None,
                limit: int = 2000, offset: int = 0, timeout: int = 30) -> dict:
    """ดึง flood features (GeoJSON). ต้องมี GISTDA_DATA_KEY ใน .env."""
    key = settings.gistda_data_key
    if not key:
        raise RuntimeError("ไม่มี GISTDA_DATA_KEY ใน .env")
    if window not in WINDOWS:
        raise ValueError(f"window ต้องเป็น {WINDOWS}")
    params = {"limit": limit, "offset": offset}
    if pv_idn is not None:
        params["pv_idn"] = pv_idn
    r = requests.get(f"{settings.gistda_gateway_base}/resources/features/flood/{window}",
                     params=params, headers={"accept": "application/json", "API-Key": key},
                     timeout=timeout)
    r.raise_for_status()
    return r.json()


def summarize_by_province(window: str = "30days") -> list[dict]:
    """รวมพื้นที่น้ำท่วมปัจจุบันต่อจังหวัด (ทั้งประเทศ) → [{pv, area_rai, features}] เรียงมาก→น้อย."""
    gj = fetch_flood(window=window, limit=5000)
    agg: dict[str, dict] = {}
    for f in gj.get("features", []):
        p = f.get("properties", {})
        name = p.get("pv_tn") or p.get("pv_en") or str(p.get("pv_idn", "?"))
        a = agg.setdefault(name, {"pv": name, "area_rai": 0.0, "features": 0})
        a["area_rai"] += float(p.get("f_area") or p.get("_area") or 0)
        a["features"] += 1
    return sorted(agg.values(), key=lambda x: -x["area_rai"])


@lru_cache(maxsize=8)
def current_flood_provinces(window: str = "30days") -> tuple:
    """เซ็ตชื่อจังหวัด (pv_tn) ที่มีน้ำท่วมปัจจุบัน — cache ไว้."""
    return tuple(x["pv"] for x in summarize_by_province(window))


def main() -> None:
    try:
        rows = summarize_by_province("30days")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] เรียก GISTDA flood API ไม่ได้: {exc}")
        return
    print(f"จังหวัดที่มีน้ำท่วมปัจจุบัน (30 วันล่าสุด) = {len(rows)} จังหวัด")
    for r in rows[:15]:
        print(f"  {r['pv']:24s} {r['area_rai']:>14,.0f}  ({r['features']} features)")


if __name__ == "__main__":
    main()
