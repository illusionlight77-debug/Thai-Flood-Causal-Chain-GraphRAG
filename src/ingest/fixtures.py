"""สร้างกราฟเหตุ-ผลลุ่มเจ้าพระยา (ขยายเป็น 8 ลุ่มน้ำสาขา · 23 จังหวัด).

**อัปเดต 2026-09-03 (ขยาย N + ลด fixture):** เดิมกราฟมี 4 reach / 10 จังหวัด (hand-built).
ตอนนี้ขยายเป็นโครงลุ่มเจ้าพระยาจริง 8 ลุ่มน้ำสาขา — ปิง/วัง/ยม/น่าน/สะแกกรัง/ป่าสัก/ท่าจีน/
เจ้าพระยา — ครอบคลุม 23 จังหวัดในลุ่มน้ำ (ดู chao_phraya_basin_provinces.json).

ที่มาของแต่ละส่วน (ทำไม *ไม่ใช่ค่าที่ตั้งให้เข้ากับผล*):
  • จังหวัด + ลุ่มน้ำสาขา     ← chao_phraya_basin_provinces.json (ภูมิศาสตร์จริง)
  • geometry                 ← GADM4.1 (จริง)
  • gold (จังหวัดท่วม)        ← ground_truth_{year}.json (GISTDA satellite ≥10,000 ไร่)
  • reach.overflow           ← river_reach_overbank_{year}.json (RID SWOC gauge, *อิสระจาก satellite gold*)
  • dam spillway/active      ← dam_specs.json (EGAT/RID)
โครง node/edge = hand-built จาก topology ลุ่มน้ำจริง (ทิศการไหลจริง) — evidence ชี้กลับแหล่งทุกเส้น.

EVENT_ID เลือกเหตุการณ์ (chao_phraya_2022 / chao_phraya_2021). โครงกราฟ + universe จังหวัด
เหมือนกันทุกเหตุการณ์ (เทียบ cross-event ยุติธรรม); เปลี่ยนเฉพาะ gold + reach.overflow ต่อปี.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from src.config import settings

# ── event-parameterized ──────────────────────────────────────────
EVENT_ID = os.environ.get("EVENT_ID", "chao_phraya_2022")
_YEAR = EVENT_ID.rsplit("_", 1)[-1]
_EVENT_DATES = {
    "2022": ("2022-09-25/2022-10-15", "2022-10-10"),
    "2021": ("2021-09-24/2021-10-05", "2021-10-01"),
    "2024": ("2024-08/2024-10 (ทั้งปี)", "2024-09-15"),
    "2023": ("2023-08/2023-10 (ทั้งปี)", "2023-09-15"),
}
EVENT_PERIOD, LAYER_DATE = _EVENT_DATES.get(_YEAR, (f"{_YEAR}-09/{_YEAR}-10", f"{_YEAR}-10-01"))

_PROC = settings.data_processed_dir

# ── จังหวัด (23) — โหลดจาก basin membership (ภูมิศาสตร์จริง) ─────────
_BASIN_PATH = _PROC / "chao_phraya_basin_provinces.json"
_BASIN = json.loads(_BASIN_PATH.read_text("utf-8"))["provinces"] if _BASIN_PATH.exists() else {}

# PROVINCES: pid -> (lon, lat, ชื่อไทย, ชื่ออังกฤษ)  (คงรูปทูเพิลเดิมเพื่อ backward-compat)
_EN = {  # pid -> English display name (GISTDA/GADM style with spaces)
    "TAK": "Tak", "KAMPHAENGPHET": "Kamphaeng Phet", "SUKHOTHAI": "Sukhothai",
    "UTTARADIT": "Uttaradit", "PHITSANULOK": "Phitsanulok", "PHICHIT": "Phichit",
    "NAKHONSAWAN": "Nakhon Sawan", "UTHAITHANI": "Uthai Thani", "CHAINAT": "Chai Nat",
    "SINGBURI": "Sing Buri", "ANGTHONG": "Ang Thong", "AYUTTHAYA": "Ayutthaya",
    "LOPBURI": "Lopburi", "SARABURI": "Saraburi", "PHETCHABUN": "Phetchabun",
    "SUPHANBURI": "Suphan Buri", "NAKHONPATHOM": "Nakhon Pathom", "PATHUMTHANI": "Pathum Thani",
    "NONTHABURI": "Nonthaburi", "BANGKOK": "Bangkok", "CHIANGMAI": "Chiang Mai",
    "LAMPANG": "Lampang", "LAMPHUN": "Lamphun",
}
PROVINCES: dict[str, tuple[float, float, str, str]] = {
    pid: (v["lon"], v["lat"], v["th"], _EN.get(pid, pid)) for pid, v in _BASIN.items()
}
GADM_NAME = {pid: v["gadm"] for pid, v in _BASIN.items()}
PROV_SUBBASIN = {pid: v["subbasin"] for pid, v in _BASIN.items()}
HALF = 0.05

# ── โครงลุ่มน้ำ (8 สาขา) → reach + INUNDATES (ภูมิศาสตร์จริง: reach ไหลผ่านจังหวัดใด) ──
REACH_INUNDATION: dict[str, list[tuple[str, float]]] = {
    "RR-PING":       [("TAK", 8.0), ("KAMPHAENGPHET", 8.0), ("CHIANGMAI", 8.0), ("LAMPHUN", 8.0)],
    "RR-WANG":       [("LAMPANG", 8.0)],
    "RR-YOM":        [("SUKHOTHAI", 8.0), ("PHICHIT", 8.0)],
    "RR-NAN":        [("UTTARADIT", 8.0), ("PHITSANULOK", 8.0), ("PHICHIT", 8.0)],
    "RR-SAKAEKRANG": [("UTHAITHANI", 8.0)],
    "RR-CP-UPPER":   [("NAKHONSAWAN", 8.0), ("CHAINAT", 9.0)],
    # #3 แกนเจ้าพระยาตอนล่างซอยเป็น 3 ช่วงตามสถานีวัดจริง (C.3/C.35/C.29) → lead-time รายจังหวัด
    "RR-CP-L1":      [("SINGBURI", 7.0), ("ANGTHONG", 7.0)],           # ชัยนาท–สิงห์บุรี–อ่างทอง (C.3)
    "RR-CP-L2":      [("AYUTTHAYA", 7.5)],                             # อ่างทอง–อยุธยา (C.35/ป้อมเพชร)
    "RR-CP-L3":      [("PATHUMTHANI", 8.0), ("NONTHABURI", 9.0), ("BANGKOK", 9.5)],  # อยุธยา–กรุงเทพ (C.29)
    "RR-PASAK":      [("PHETCHABUN", 8.0), ("LOPBURI", 8.0), ("SARABURI", 8.0)],
    "RR-THACHIN":    [("SUPHANBURI", 8.0), ("NAKHONPATHOM", 8.0)],
}
REACH_SUBBASIN = {
    "RR-PING": "Ping", "RR-WANG": "Wang", "RR-YOM": "Yom", "RR-NAN": "Nan",
    "RR-SAKAEKRANG": "SakaeKrang", "RR-CP-UPPER": "ChaoPhraya",
    "RR-CP-L1": "ChaoPhraya", "RR-CP-L2": "ChaoPhraya", "RR-CP-L3": "ChaoPhraya",
    "RR-PASAK": "Pasak", "RR-THACHIN": "ThaChin",
}
REACH_META = {  # reach -> (ชื่อ, basin, stream order)
    "RR-PING": ("ปิงท้ายเขื่อนภูมิพล", "Ping", 4),
    "RR-WANG": ("แม่น้ำวัง", "Wang", 4),
    "RR-YOM": ("แม่น้ำยม (ไม่มีเขื่อนใหญ่)", "Yom", 4),
    "RR-NAN": ("น่านท้ายเขื่อนสิริกิติ์", "Nan", 4),
    "RR-SAKAEKRANG": ("แม่น้ำสะแกกรัง", "SakaeKrang", 4),
    "RR-CP-UPPER": ("เจ้าพระยาตอนบน (ปากน้ำโพ–ชัยนาท)", "ChaoPhraya", 6),
    "RR-CP-L1": ("เจ้าพระยา ชัยนาท–สิงห์บุรี–อ่างทอง (C.3)", "ChaoPhraya", 7),
    "RR-CP-L2": ("เจ้าพระยา อ่างทอง–อยุธยา (C.35)", "ChaoPhraya", 7),
    "RR-CP-L3": ("เจ้าพระยา อยุธยา–กรุงเทพ (C.29)", "ChaoPhraya", 8),
    "RR-PASAK": ("แม่น้ำป่าสัก (เขื่อนป่าสักฯ)", "Pasak", 5),
    "RR-THACHIN": ("แม่น้ำท่าจีน (แยกจากเจ้าพระยาที่ชัยนาท)", "ThaChin", 6),
}
REACH_LEVEL = {r: 8.0 for r in REACH_META}  # nominal (gate ใช้ overflow ไม่ใช่ level แล้ว)

# ── เขื่อน: spillway + active จาก dam_specs.json (จริง) ─────────────
_DAM_SPECS_PATH = _PROC / "dam_specs.json"
_FALLBACK_SPILLWAY = {"RES-BHUMIBOL": 260.0, "RES-SIRIKIT": 162.0,
                      "RES-CHAOPHRAYA": 16.5, "RES-PASAK": 42.0}
_FALLBACK_ACTIVE = {"RES-BHUMIBOL": True, "RES-SIRIKIT": True,
                    "RES-CHAOPHRAYA": True, "RES-PASAK": True}
_DAM_META = {  # rid -> (ชื่อ, capacity_mcm, lat, lon, basin)
    "RES-BHUMIBOL": ("เขื่อนภูมิพล (Bhumibol)", 13462, 17.24, 98.97, "Ping"),
    "RES-SIRIKIT": ("เขื่อนสิริกิติ์ (Sirikit)", 9510, 17.76, 100.56, "Nan"),
    "RES-PASAK": ("เขื่อนป่าสักชลสิทธิ์ (Pasak Jolasid)", 960, 15.06, 101.06, "Pasak"),
    "RES-CHAOPHRAYA": ("เขื่อนเจ้าพระยา (Chao Phraya Dam)", 0, 15.16, 100.18, "ChaoPhraya"),
}


def _load_dam_specs() -> dict:
    if _DAM_SPECS_PATH.exists():
        return json.loads(_DAM_SPECS_PATH.read_text("utf-8"))
    print(f"[fixtures] WARNING: {_DAM_SPECS_PATH.name} หาย → ใช้ fallback")
    return {}


def _spillway_level(specs: dict, rid: str) -> float:
    s = specs.get(rid, {})
    lvl = s.get("full_supply_level_m_msl", s.get("normal_upstream_retention_m_msl"))
    return float(lvl) if lvl is not None else _FALLBACK_SPILLWAY[rid]


def _is_active(specs: dict, rid: str) -> bool:
    obs = specs.get(rid, {}).get(f"observed_{_YEAR}", specs.get(rid, {}).get("observed_2022"))
    if obs is None:
        return _FALLBACK_ACTIVE[rid]
    return bool(obs.get(f"spilled_via_spillway_{_YEAR}") or obs.get("spilled_via_spillway_2022")
                or obs.get(f"passed_flood_flow_{_YEAR}") or obs.get("passed_flood_flow_2022"))


_SPECS = _load_dam_specs()
RESERVOIR_SPILLWAY = {rid: _spillway_level(_SPECS, rid) for rid in _FALLBACK_SPILLWAY}
RESERVOIR_ACTIVE = {rid: _is_active(_SPECS, rid) for rid in _FALLBACK_ACTIVE}

# ── reach.overflow ← river_reach_overbank_{year}.json (RID gauge, อิสระจาก satellite) ──
_OVERBANK_PATH = _PROC / f"river_reach_overbank_{_YEAR}.json"
_GAUGES_PATH = _PROC / f"river_gauges_{_YEAR}.json"


def _load_reach_overflow() -> dict:
    if _OVERBANK_PATH.exists():
        sub = json.loads(_OVERBANK_PATH.read_text("utf-8")).get("subbasin_overbank", {})
        return {r: bool(sub.get(REACH_SUBBASIN[r], {}).get("overflow", False)) for r in REACH_META}
    if _GAUGES_PATH.exists():  # fallback: reach-level gauge file (เหตุการณ์เดิม)
        g = json.loads(_GAUGES_PATH.read_text("utf-8")).get("reach_gauge", {})
        return {r: bool(g.get(r, {}).get("overflow", False)) for r in REACH_META}
    print(f"[fixtures] WARNING: ไม่มี overbank/gauge ของ {_YEAR} → overflow=False ทุก reach")
    return {r: False for r in REACH_META}


REACH_OVERFLOW = _load_reach_overflow()

# ── สถานีฝน (1 ต่อลุ่มน้ำต้นน้ำ) — active ทั้งหมด (ฝนกระจายทั้งลุ่ม = ข้อเท็จจริงของเหตุการณ์) ──
RAIN_STATIONS = {  # rid -> (ชื่อ, lat, lon, basin)
    "RS-PING": ("สถานีฝนปิงตอนบน (Ping upper)", 18.79, 98.98, "Ping"),
    "RS-WANG": ("สถานีฝนวังตอนบน (Wang upper)", 18.29, 99.49, "Wang"),
    "RS-YOM": ("สถานีฝนยมตอนบน (Yom upper)", 18.14, 100.14, "Yom"),
    "RS-NAN": ("สถานีฝนน่านตอนบน (Nan upper)", 19.19, 100.78, "Nan"),
    "RS-SAKAEKRANG": ("สถานีฝนสะแกกรัง (Sakae Krang)", 15.38, 99.87, "SakaeKrang"),
    "RS-PASAK": ("สถานีฝนป่าสักตอนบน (Pasak upper)", 16.42, 101.16, "Pasak"),
}
RAIN_ACTIVE = {rid: True for rid in RAIN_STATIONS}

# ── จังหวัดที่มีคันกั้นน้ำป้องกัน (ไม่ท่วมแม้ reach ล้น) — King's Dyke กทม./ปริมณฑล ──
PROTECTED_PROVINCES = {"BANGKOK", "NONTHABURI"}

# ── gold ← ground_truth_{year}.json (GISTDA จริง) ───────────────────
_FALLBACK_GOLD = ["NAKHONSAWAN", "CHAINAT", "SINGBURI", "ANGTHONG", "AYUTTHAYA"]
_GROUND_TRUTH_PATH = _PROC / f"ground_truth_{_YEAR}.json"


def _load_gold() -> list[str]:
    if _GROUND_TRUTH_PATH.exists():
        return list(json.loads(_GROUND_TRUTH_PATH.read_text("utf-8")).get("gold_flooded", _FALLBACK_GOLD))
    print(f"[fixtures] WARNING: {_GROUND_TRUTH_PATH.name} หาย → gold fallback")
    return _FALLBACK_GOLD


GOLD_FLOODED = _load_gold()

# ── geometry จริง: GADM level-1 ────────────────────────────────────
_GADM_PATH = _PROC.parent / "raw" / "gadm41_THA_1.json"


def _load_gadm_geoms() -> dict:
    if not _GADM_PATH.exists():
        return {}
    d = json.loads(_GADM_PATH.read_text("utf-8"))
    by_name = {f["properties"].get("NAME_1"): f["geometry"] for f in d["features"]}
    return {pid: by_name[name] for pid, name in GADM_NAME.items() if name in by_name}


_GADM_GEOMS = _load_gadm_geoms()
USE_REAL_GEOM = len(_GADM_GEOMS) == len(GADM_NAME) and bool(GADM_NAME)

# ── FLOWS_TO topology (ทิศการไหลจริงของลุ่มเจ้าพระยา) ────────────────
CONFLUENCE = ("CONF-PAKNAMPHO", "ปากน้ำโพ (Pak Nam Pho)", 15.70, 100.12)
# lag_hours ของแกนหลักตั้งจาก "ระยะลำน้ำจริง / ความเร็วคลื่นน้ำท่วม (~1.5 ม./วิ)" ไม่ใช่จากวันน้ำท่วม
# (กันไม่ให้ circular กับ lead-time validation): ชัยนาท→สิงห์บุรี ~40 กม.≈24ชม.,
# อ่างทอง→อยุธยา ~40 กม.≈24ชม., อยุธยา→กรุงเทพ ~90 กม.≈48ชม.
FLOWS = [  # (src, dst, lag_hours)
    ("RR-WANG", "RR-PING", 24),               # วัง → ปิง
    ("RR-PING", "CONF-PAKNAMPHO", 36),
    ("RR-YOM", "CONF-PAKNAMPHO", 36),
    ("RR-NAN", "CONF-PAKNAMPHO", 36),
    ("CONF-PAKNAMPHO", "RR-CP-UPPER", 12),
    ("RR-CP-UPPER", "RR-CP-L1", 24),          # ชัยนาท → สิงห์บุรี/อ่างทอง
    ("RR-CP-L1", "RR-CP-L2", 24),             # อ่างทอง → อยุธยา
    ("RR-CP-L2", "RR-CP-L3", 48),             # อยุธยา → ปทุม/นนท์/กรุงเทพ
    ("RR-CP-UPPER", "RR-THACHIN", 96),        # ท่าจีน = distributary ยาว ~325 กม. ลาดชันต่ำ → ช้ามาก (นครปฐมท่วมท้าย)
    ("RR-SAKAEKRANG", "RR-CP-L1", 18),        # สะแกกรังเข้าเจ้าพระยาที่ชัยนาท
    ("RR-PASAK", "RR-CP-L2", 18),             # ป่าสักเข้าเจ้าพระยาที่อยุธยา
]


def _ev(station_id: str, dataset: str, timestamp: str = LAYER_DATE) -> dict:
    return {"station_id": station_id, "timestamp": timestamp, "dataset": dataset}


def build_nodes() -> list[dict]:
    nodes: list[dict] = []
    for rid, (name, lat, lon, basin) in RAIN_STATIONS.items():
        nodes.append({"label": "RainStation", "id": rid, "name": name,
                      "active": RAIN_ACTIVE[rid], "lat": lat, "lon": lon, "basin": basin})
    for rid, (name, cap, lat, lon, basin) in _DAM_META.items():
        nodes.append({"label": "Reservoir", "id": rid, "name": name, "capacity_mcm": cap,
                      "spillway_level": RESERVOIR_SPILLWAY[rid], "active": RESERVOIR_ACTIVE[rid],
                      "lat": lat, "lon": lon, "basin": basin})
    for rid, (name, basin, order) in REACH_META.items():
        nodes.append({"label": "RiverReach", "id": rid, "name": name, "basin": basin,
                      "order": order, "level": REACH_LEVEL[rid], "overflow": REACH_OVERFLOW[rid],
                      "subbasin": REACH_SUBBASIN[rid]})
    cid, cname, clat, clon = CONFLUENCE
    nodes.append({"label": "Confluence", "id": cid, "name": cname, "lat": clat, "lon": clon})
    for pid, (lon, lat, th, en) in PROVINCES.items():
        nodes.append({"label": "Province", "id": pid, "name_th": th, "name_en": en,
                      "lat": lat, "lon": lon, "protected": pid in PROTECTED_PROVINCES})
    return nodes


def build_causal_edges() -> list[dict]:
    edges: list[dict] = []
    dam_of = {"RS-PING": "RES-BHUMIBOL", "RS-NAN": "RES-SIRIKIT", "RS-PASAK": "RES-PASAK"}
    reach_of = {"RS-PING": "RR-PING", "RS-WANG": "RR-WANG", "RS-YOM": "RR-YOM", "RS-NAN": "RR-NAN",
                "RS-SAKAEKRANG": "RR-SAKAEKRANG", "RS-PASAK": "RR-PASAK"}
    # FEEDS (ฝน → เขื่อน) + RUNOFF_TO (ฝน → ลำน้ำ bypass เขื่อน)
    for rs in RAIN_STATIONS:
        if rs in dam_of:
            edges.append({"type": "FEEDS", "src": rs, "dst": dam_of[rs], "lag_hours": 48,
                          "evidence": _ev(rs, "D1/data.go.th telemetry")})
        edges.append({"type": "RUNOFF_TO", "src": rs, "dst": reach_of[rs], "lag_hours": 24,
                      "evidence": _ev(rs, "D1/data.go.th rain→runoff")})
    # OVERFLOWS_TO (เขื่อน → ลำน้ำ)
    dam_reach = {"RES-BHUMIBOL": "RR-PING", "RES-SIRIKIT": "RR-NAN",
                 "RES-PASAK": "RR-PASAK", "RES-CHAOPHRAYA": "RR-CP-L1"}
    for dam, reach in dam_reach.items():
        edges.append({"type": "OVERFLOWS_TO", "src": dam, "dst": reach,
                      "spillway": RESERVOIR_SPILLWAY[dam],
                      "evidence": _ev(dam, "D2/dam_specs.json (EGAT/RID)")})
    # FLOWS_TO (ลำน้ำ/จุดบรรจบ ตามทิศการไหลจริง)
    for src, dst, lag in FLOWS:
        edges.append({"type": "FLOWS_TO", "src": src, "dst": dst, "lag_hours": lag,
                      "evidence": _ev(src, "D1/RID river network (flow direction)")})
    return edges


def _box(lon: float, lat: float) -> list:
    return [[[lon - HALF, lat - HALF], [lon + HALF, lat - HALF],
             [lon + HALF, lat + HALF], [lon - HALF, lat + HALF], [lon - HALF, lat - HALF]]]


def _prov_geometry(pid: str) -> dict:
    if pid in _GADM_GEOMS:
        return _GADM_GEOMS[pid]
    lon, lat, *_ = PROVINCES[pid]
    return {"type": "Polygon", "coordinates": _box(lon, lat)}


def _outlet_point(pid: str) -> list:
    if pid in _GADM_GEOMS:
        from shapely.geometry import shape
        p = shape(_GADM_GEOMS[pid]).representative_point()
        return [p.x, p.y]
    lon, lat, *_ = PROVINCES[pid]
    return [lon, lat]


def build_provinces_geojson() -> dict:
    feats = []
    for pid, (lon, lat, th, en) in PROVINCES.items():
        feats.append({"type": "Feature",
                      "properties": {"prov_id": pid, "name_th": th, "name_en": en,
                                     "geom_source": "GADM4.1" if pid in _GADM_GEOMS else "box"},
                      "geometry": _prov_geometry(pid)})
    return {"type": "FeatureCollection", "features": feats}


def build_reach_outlets_geojson() -> dict:
    feats = []
    for reach, targets in REACH_INUNDATION.items():
        for pid, threshold in targets:
            feats.append({"type": "Feature",
                          "properties": {"reach_id": reach, "threshold": threshold,
                                         "expected_prov": pid, "layer_date": LAYER_DATE},
                          "geometry": {"type": "Point", "coordinates": _outlet_point(pid)}})
    return {"type": "FeatureCollection", "features": feats}


def build_flood_extent_geojson() -> dict:
    feats = []
    for pid in GOLD_FLOODED:
        if pid not in PROVINCES:
            continue
        feats.append({"type": "Feature",
                      "properties": {"event": EVENT_ID, "prov_id": pid,
                                     "source": "GISTDA satellite (thaiwater) + GADM4.1 geometry",
                                     "layer_date": LAYER_DATE},
                      "geometry": _prov_geometry(pid)})
    return {"type": "FeatureCollection", "features": feats}


def build_event_state() -> dict:
    return {"event_id": EVENT_ID, "period": EVENT_PERIOD, "layer_date": LAYER_DATE,
            "reservoir_active": RESERVOIR_ACTIVE, "reach_overflow": REACH_OVERFLOW,
            "gold_flooded": GOLD_FLOODED, "n_provinces": len(PROVINCES)}


def build_news_corpus() -> list[dict]:
    """ข่าวน้ำท่วม (vector-rag). coverage bias เหมือนข่าวจริง: จังหวัดใหญ่ถูกรายงานหนัก."""
    return [
        {"id": "N1", "date": "2022-10-01",
         "text": "สถานการณ์น้ำเจ้าพระยายังวิกฤต น้ำท่วมพระนครศรีอยุธยาขยายวงกว้าง "
                 "หลายชุมชนริมแม่น้ำถูกน้ำท่วมสูง เฝ้าระวังกรุงเทพมหานครและปริมณฑล"},
        {"id": "N2", "date": "2022-10-02",
         "text": "เขื่อนเจ้าพระยาเพิ่มการระบายน้ำ กระทบพื้นที่ท้ายน้ำ อยุธยา และเขตเศรษฐกิจ "
                 "กรุงเทพมหานคร ประชาชนเตรียมรับมือ"},
        {"id": "N3", "date": "2022-10-03",
         "text": "น้ำเหนือหลากลงนครสวรรค์ ระดับน้ำปากน้ำโพสูงขึ้นต่อเนื่อง น้ำท่วมนครสวรรค์หลายอำเภอ"},
        {"id": "N4", "date": "2022-10-05",
         "text": "อยุธยาอ่วม น้ำท่วมโบราณสถาน นักท่องเที่ยวลด ขณะกรุงเทพยังเฝ้าระวังน้ำทะเลหนุน"},
        {"id": "N5", "date": "2022-10-06",
         "text": "รายงานพิเศษ: ทำไมกรุงเทพจึงเสี่ยงน้ำท่วมทุกปี ระบบระบายน้ำและคันกั้นน้ำเจ้าพระยา"},
        {"id": "N6", "date": "2022-10-07",
         "text": "น้ำท่วมสิงห์บุรีบางพื้นที่ริมเจ้าพระยา ชาวบ้านขนของหนีน้ำ"},
        {"id": "N7", "date": "2022-10-08",
         "text": "ชัยนาทเฝ้าระวังน้ำล้นตลิ่ง หลังเขื่อนเจ้าพระยาระบายเพิ่ม พื้นที่การเกษตรได้รับผลกระทบ"},
        {"id": "N8", "date": "2022-10-09",
         "text": "ภาพรวมลุ่มเจ้าพระยา: น้ำจากเขื่อนภูมิพลและสิริกิติ์ไหลรวมที่ปากน้ำโพ ก่อนลงเจ้าพระยาตอนล่าง"},
        {"id": "N9", "date": "2022-10-04",
         "text": "แม่น้ำยมล้นตลิ่งท่วมสุโขทัยและพิจิตร พื้นที่การเกษตรเสียหายหนัก"},
        {"id": "N10", "date": "2022-10-05",
         "text": "น้ำท่าจีนเอ่อล้นท่วมสุพรรณบุรีและนครปฐม เร่งระบายน้ำ"},
        {"id": "N11", "date": "2022-10-06",
         "text": "แม่น้ำป่าสักหนุนสูง น้ำท่วมลพบุรี สระบุรี และเพชรบูรณ์"},
    ]


def build_deprecated_fixture_flood_extent() -> dict:
    polys = []
    for pid in _FALLBACK_GOLD:
        if pid in PROVINCES:
            lon, lat, *_ = PROVINCES[pid]
            polys.append(_box(lon, lat))
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature",
         "properties": {"event": EVENT_ID, "source": "DEPRECATED fixture (box, tuned gold)",
                        "layer_date": LAYER_DATE},
         "geometry": {"type": "MultiPolygon", "coordinates": polys}}]}


def write_all(out_dir: Path | None = None) -> Path:
    out = out_dir or settings.data_processed_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph_nodes.json").write_text(json.dumps(build_nodes(), ensure_ascii=False, indent=2), "utf-8")
    (out / "graph_edges.json").write_text(json.dumps(build_causal_edges(), ensure_ascii=False, indent=2), "utf-8")
    (out / "provinces.geojson").write_text(json.dumps(build_provinces_geojson(), ensure_ascii=False, indent=2), "utf-8")
    (out / "reach_outlets.geojson").write_text(json.dumps(build_reach_outlets_geojson(), ensure_ascii=False, indent=2), "utf-8")
    (out / "gistda_flood_extent.geojson").write_text(json.dumps(build_flood_extent_geojson(), ensure_ascii=False, indent=2), "utf-8")
    (out / "gistda_flood_extent_fixture_deprecated.geojson").write_text(
        json.dumps(build_deprecated_fixture_flood_extent(), ensure_ascii=False, indent=2), "utf-8")
    (out / "event_state.json").write_text(json.dumps(build_event_state(), ensure_ascii=False, indent=2), "utf-8")
    (out / "news_corpus.json").write_text(json.dumps(build_news_corpus(), ensure_ascii=False, indent=2), "utf-8")
    return out


if __name__ == "__main__":
    p = write_all()
    print(f"fixtures written to {p}  ({len(PROVINCES)} provinces, {len(REACH_META)} reaches, "
          f"event={EVENT_ID}, gold={len(GOLD_FLOODED)})")
