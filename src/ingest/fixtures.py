"""สร้าง fixture ลุ่มเจ้าพระยา เหตุการณ์น้ำท่วม ก.ย.–ต.ค. 2022 (พ.ศ. 2565).

ทำไมต้องมี fixture: causal chain ที่ *coherent* (lag/spillway/threshold/geometry ตรงกัน)
ประกอบจาก API สดตรง ๆ ไม่ได้ในรอบเดียว + GISTDA STAC ต่อไม่ติด (ดู README > Bugs).
ค่าต่าง ๆ อิงเหตุการณ์จริง (เขื่อนภูมิพล/สิริกิติ์/เจ้าพระยา, ปากน้ำโพ) แต่เป็น
demonstration dataset — ตัวเลข eval ที่ได้จึงเป็น "on fixture" ระบุชัดใน README.

ผลลัพธ์เขียนลง data/processed/:
  graph_nodes.json      nodes ทั้งหมด
  graph_edges.json      causal edges (FEEDS/OVERFLOWS_TO/FLOWS_TO) + evidence
                        (INUNDATES สร้างในเฟส 2 จาก point-in-polygon)
  provinces.geojson     polygon จังหวัด (EPSG:4326)
  reach_outlets.geojson จุดปลายน้ำของ reach + threshold (สำหรับ PIP → INUNDATES)
  gistda_flood_extent.geojson  ground truth (gold) — พื้นที่น้ำท่วม
  event_state.json      สถานะเหตุการณ์ (เขื่อนล้น + ระดับน้ำ reach)
  news_corpus.json      ข่าวน้ำท่วม (สำหรับ vector-rag)
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config import settings

EVENT_ID = "chao_phraya_2022"
EVENT_PERIOD = "2022-09-25/2022-10-15"
LAYER_DATE = "2022-10-10"

# ── จังหวัด: (lon, lat, ชื่อไทย, ชื่ออังกฤษ) ─────────────────────
PROVINCES: dict[str, tuple[float, float, str, str]] = {
    "TAK":        (99.13, 16.87, "ตาก", "Tak"),
    "PHITSANULOK":(100.27, 16.82, "พิษณุโลก", "Phitsanulok"),
    "NAKHONSAWAN":(100.14, 15.70, "นครสวรรค์", "Nakhon Sawan"),
    "CHAINAT":    (100.13, 15.19, "ชัยนาท", "Chai Nat"),
    "SINGBURI":   (100.40, 14.89, "สิงห์บุรี", "Sing Buri"),
    "ANGTHONG":   (100.46, 14.59, "อ่างทอง", "Ang Thong"),
    "AYUTTHAYA":  (100.58, 14.35, "พระนครศรีอยุธยา", "Ayutthaya"),
    "PATHUMTHANI":(100.53, 14.02, "ปทุมธานี", "Pathum Thani"),
    "NONTHABURI": (100.51, 13.86, "นนทบุรี", "Nonthaburi"),
    "BANGKOK":    (100.52, 13.75, "กรุงเทพมหานคร", "Bangkok"),
}
HALF = 0.05  # ครึ่งความกว้าง box จังหวัด (องศา) — เล็กพอไม่ให้ box จังหวัดที่อยู่ชิดกัน
             # (นนทบุรี/กรุงเทพ ห่างกัน ~0.11°) ทับกัน → point-in-polygon ได้จังหวัดเดียวชัด

# ── RiverReach → [(province_id, threshold_m)] : ใช้สร้าง INUNDATES + PIP ──
REACH_INUNDATION: dict[str, list[tuple[str, float]]] = {
    "RR-PING":     [("TAK", 8.0)],
    "RR-NAN":      [("PHITSANULOK", 8.0)],
    "RR-CP-UPPER": [("NAKHONSAWAN", 8.0), ("CHAINAT", 9.0)],
    "RR-CP-LOWER": [("SINGBURI", 7.0), ("ANGTHONG", 7.0), ("AYUTTHAYA", 7.5),
                    ("PATHUMTHANI", 8.0), ("NONTHABURI", 9.0), ("BANGKOK", 9.5)],
}

# ── สถานะเขื่อน: ดึงจาก dam_specs.json (สเปกจริง + สถานะสังเกตปี 2565) ──────
#   spillway_level, active (เขื่อนล้นสปิลเวย์จริงไหม) มาจากข้อมูลจริง ไม่ใช่ค่าที่ตั้งให้เข้ากับผล
#   (แก้ threshold circularity — ดู README Bugs 2026-07-27)
_DAM_SPECS_PATH = settings.data_processed_dir / "dam_specs.json"

# fallback (ใช้เมื่อ dam_specs.json หาย เพื่อคง reproducibility) = ค่าเดิมก่อน 2026-07-27
_FALLBACK_SPILLWAY = {"RES-BHUMIBOL": 260.0, "RES-SIRIKIT": 162.0, "RES-CHAOPHRAYA": 16.5}
_FALLBACK_ACTIVE = {"RES-BHUMIBOL": True, "RES-SIRIKIT": True, "RES-CHAOPHRAYA": True}


def _load_dam_specs() -> dict:
    if _DAM_SPECS_PATH.exists():
        return json.loads(_DAM_SPECS_PATH.read_text("utf-8"))
    print(f"[fixtures] WARNING: {_DAM_SPECS_PATH.name} หาย → ใช้ fallback (ค่าเดิม tuned)")
    return {}


def _spillway_level(specs: dict, rid: str) -> float:
    s = specs.get(rid, {})
    lvl = s.get("full_supply_level_m_msl", s.get("normal_upstream_retention_m_msl"))
    return float(lvl) if lvl is not None else _FALLBACK_SPILLWAY[rid]


def _is_active(specs: dict, rid: str) -> bool:
    """เขื่อน active = ล้นสปิลเวย์จริง (storage dam) หรือส่งน้ำเกิน flood threshold (barrage)."""
    obs = specs.get(rid, {}).get("observed_2022")
    if obs is None:
        return _FALLBACK_ACTIVE[rid]
    return bool(obs.get("spilled_via_spillway_2022") or obs.get("passed_flood_flow_2022"))


_SPECS = _load_dam_specs()
RESERVOIR_SPILLWAY = {rid: _spillway_level(_SPECS, rid) for rid in _FALLBACK_SPILLWAY}
RESERVOIR_ACTIVE = {rid: _is_active(_SPECS, rid) for rid in _FALLBACK_ACTIVE}
# ผลจริงปี 2565: ภูมิพล/สิริกิติ์ = retaining (ไม่ล้นสปิลเวย์) → active False;
#   เขื่อนเจ้าพระยา (barrage) ส่งน้ำ 3,048 ≥ 2,800 → active True. ดู dam_specs.json.

REACH_LEVEL = {"RR-PING": 5.0, "RR-NAN": 6.0, "RR-CP-UPPER": 9.5, "RR-CP-LOWER": 8.5}
# ⚠️ REACH_LEVEL + INUNDATES threshold ยัง tuned อยู่ (ต้องใช้ river-gauge จริงจึงจะ de-circularize
#    ครบ — ดู README Limitations). Item 1 นี้แก้เฉพาะ spillway + active ให้มาจากสเปกจริง.

# ── ground truth (gold) — จาก GISTDA จริง (Item 3) ผ่าน ground_truth_2022.json ──────
#   fallback = ชุด fixture เดิม เพื่อคง reproducibility ถ้าไฟล์หาย
_FALLBACK_GOLD = ["NAKHONSAWAN", "CHAINAT", "SINGBURI", "ANGTHONG", "AYUTTHAYA", "PATHUMTHANI"]
_GROUND_TRUTH_PATH = settings.data_processed_dir / "ground_truth_2022.json"


def _load_gold() -> list[str]:
    if _GROUND_TRUTH_PATH.exists():
        gt = json.loads(_GROUND_TRUTH_PATH.read_text("utf-8"))
        return list(gt.get("gold_flooded", _FALLBACK_GOLD))
    print(f"[fixtures] WARNING: {_GROUND_TRUTH_PATH.name} หาย → ใช้ gold fixture เดิม")
    return _FALLBACK_GOLD


GOLD_FLOODED = _load_gold()

# ── geometry จริง: GADM level-1 (จังหวัด) — Item 3 แทน box สังเคราะห์ ──────
_GADM_PATH = settings.data_processed_dir.parent / "raw" / "gadm41_THA_1.json"
GADM_NAME = {  # prov_id → GADM NAME_1
    "TAK": "Tak", "PHITSANULOK": "Phitsanulok", "NAKHONSAWAN": "NakhonSawan",
    "CHAINAT": "ChaiNat", "SINGBURI": "SingBuri", "ANGTHONG": "AngThong",
    "AYUTTHAYA": "PhraNakhonSiAyutthaya", "PATHUMTHANI": "PathumThani",
    "NONTHABURI": "Nonthaburi", "BANGKOK": "BangkokMetropolis",
}


def _load_gadm_geoms() -> dict:
    """{prov_id: geojson-geometry} จาก GADM. ว่าง = ใช้ box fallback."""
    if not _GADM_PATH.exists():
        return {}
    d = json.loads(_GADM_PATH.read_text("utf-8"))
    by_name = {f["properties"].get("NAME_1"): f["geometry"] for f in d["features"]}
    out = {}
    for pid, name in GADM_NAME.items():
        if name in by_name:
            out[pid] = by_name[name]
    return out


_GADM_GEOMS = _load_gadm_geoms()
USE_REAL_GEOM = len(_GADM_GEOMS) == len(GADM_NAME)


def _ev(station_id: str, dataset: str, timestamp: str = LAYER_DATE) -> dict:
    return {"station_id": station_id, "timestamp": timestamp, "dataset": dataset}


def build_nodes() -> list[dict]:
    nodes: list[dict] = []
    # RainStation (ต้นน้ำ)
    nodes += [
        {"label": "RainStation", "id": "RS-PING", "name": "สถานีฝนปิงตอนบน (Ping upper)",
         "lat": 18.79, "lon": 98.98, "basin": "Ping"},
        {"label": "RainStation", "id": "RS-NAN", "name": "สถานีฝนน่านตอนบน (Nan upper)",
         "lat": 19.19, "lon": 100.78, "basin": "Nan"},
    ]
    # Reservoir
    nodes += [
        {"label": "Reservoir", "id": "RES-BHUMIBOL", "name": "เขื่อนภูมิพล (Bhumibol)",
         "capacity_mcm": 13462, "spillway_level": RESERVOIR_SPILLWAY["RES-BHUMIBOL"],
         "active": RESERVOIR_ACTIVE["RES-BHUMIBOL"], "lat": 17.24, "lon": 98.97, "basin": "Ping"},
        {"label": "Reservoir", "id": "RES-SIRIKIT", "name": "เขื่อนสิริกิติ์ (Sirikit)",
         "capacity_mcm": 9510, "spillway_level": RESERVOIR_SPILLWAY["RES-SIRIKIT"],
         "active": RESERVOIR_ACTIVE["RES-SIRIKIT"], "lat": 17.76, "lon": 100.56, "basin": "Nan"},
        {"label": "Reservoir", "id": "RES-CHAOPHRAYA", "name": "เขื่อนเจ้าพระยา (Chao Phraya Dam)",
         "capacity_mcm": 0, "spillway_level": RESERVOIR_SPILLWAY["RES-CHAOPHRAYA"],
         "active": RESERVOIR_ACTIVE["RES-CHAOPHRAYA"], "lat": 15.16, "lon": 100.18, "basin": "ChaoPhraya"},
    ]
    # RiverReach (แนบระดับน้ำเหตุการณ์)
    for rid, (name, basin, order) in {
        "RR-PING": ("ปิงท้ายเขื่อนภูมิพล", "Ping", 4),
        "RR-NAN": ("น่านท้ายเขื่อนสิริกิติ์", "Nan", 4),
        "RR-CP-UPPER": ("เจ้าพระยาตอนบน (ปากน้ำโพ–ชัยนาท)", "ChaoPhraya", 6),
        "RR-CP-LOWER": ("เจ้าพระยาตอนล่าง (ชัยนาท–กรุงเทพ)", "ChaoPhraya", 7),
    }.items():
        nodes.append({"label": "RiverReach", "id": rid, "name": name, "basin": basin,
                      "order": order, "level": REACH_LEVEL[rid]})
    # Confluence (จุดบรรจบข้ามลุ่มน้ำ)
    nodes.append({"label": "Confluence", "id": "CONF-PAKNAMPHO",
                  "name": "ปากน้ำโพ (Pak Nam Pho)", "lat": 15.70, "lon": 100.12})
    # Province (geometry มาจาก provinces.geojson ตอนโหลด)
    for pid, (lon, lat, th, en) in PROVINCES.items():
        nodes.append({"label": "Province", "id": pid, "name_th": th, "name_en": en,
                      "lat": lat, "lon": lon})
    return nodes


def build_causal_edges() -> list[dict]:
    """FEEDS / OVERFLOWS_TO / FLOWS_TO (INUNDATES สร้างในเฟส 2)."""
    edges: list[dict] = []
    # FEEDS (ฝน → เขื่อน)
    edges += [
        {"type": "FEEDS", "src": "RS-PING", "dst": "RES-BHUMIBOL", "lag_hours": 48,
         "evidence": _ev("RS-PING", "D1/data.go.th telemetry")},
        {"type": "FEEDS", "src": "RS-NAN", "dst": "RES-SIRIKIT", "lag_hours": 48,
         "evidence": _ev("RS-NAN", "D1/data.go.th telemetry")},
    ]
    # OVERFLOWS_TO (เขื่อน → ลำน้ำ) — spillway ดึงจาก dam_specs.json (สเปกจริง)
    edges += [
        {"type": "OVERFLOWS_TO", "src": "RES-BHUMIBOL", "dst": "RR-PING",
         "spillway": RESERVOIR_SPILLWAY["RES-BHUMIBOL"],
         "evidence": _ev("RES-BHUMIBOL", "D2/dam_specs.json (EGAT/thaiwater 2565)")},
        {"type": "OVERFLOWS_TO", "src": "RES-SIRIKIT", "dst": "RR-NAN",
         "spillway": RESERVOIR_SPILLWAY["RES-SIRIKIT"],
         "evidence": _ev("RES-SIRIKIT", "D2/dam_specs.json (EGAT/thaiwater 2565)")},
        {"type": "OVERFLOWS_TO", "src": "RES-CHAOPHRAYA", "dst": "RR-CP-LOWER",
         "spillway": RESERVOIR_SPILLWAY["RES-CHAOPHRAYA"],
         "evidence": _ev("RES-CHAOPHRAYA", "D2/dam_specs.json (RID C.13 9 ต.ค. 65)")},
    ]
    # FLOWS_TO (ลำน้ำ → จุดบรรจบ/ลำน้ำ)
    edges += [
        {"type": "FLOWS_TO", "src": "RR-PING", "dst": "CONF-PAKNAMPHO", "lag_hours": 36,
         "evidence": _ev("RR-PING", "D1/data.go.th river gauge")},
        {"type": "FLOWS_TO", "src": "RR-NAN", "dst": "CONF-PAKNAMPHO", "lag_hours": 36,
         "evidence": _ev("RR-NAN", "D1/data.go.th river gauge")},
        {"type": "FLOWS_TO", "src": "CONF-PAKNAMPHO", "dst": "RR-CP-UPPER", "lag_hours": 12,
         "evidence": _ev("CONF-PAKNAMPHO", "D1/data.go.th river gauge")},
        {"type": "FLOWS_TO", "src": "RR-CP-UPPER", "dst": "RR-CP-LOWER", "lag_hours": 24,
         "evidence": _ev("RR-CP-UPPER", "D1/data.go.th river gauge")},
    ]
    return edges


def _box(lon: float, lat: float) -> list:
    return [[[lon - HALF, lat - HALF], [lon + HALF, lat - HALF],
             [lon + HALF, lat + HALF], [lon - HALF, lat + HALF], [lon - HALF, lat - HALF]]]


def _prov_geometry(pid: str) -> dict:
    """geometry จริงจาก GADM ถ้ามี; ไม่งั้น box สังเคราะห์ (fallback)."""
    if pid in _GADM_GEOMS:
        return _GADM_GEOMS[pid]
    lon, lat, *_ = PROVINCES[pid]
    return {"type": "Polygon", "coordinates": _box(lon, lat)}


def _outlet_point(pid: str) -> list:
    """จุดตัวแทนภายใน polygon จังหวัด (representative_point) → PIP ตกในจังหวัดแน่นอน."""
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
    """จุดปลายน้ำต่อ (reach, province) วางในจังหวัดปลายทาง → PIP กู้ mapping ได้."""
    feats = []
    for reach, targets in REACH_INUNDATION.items():
        for pid, threshold in targets:
            feats.append({"type": "Feature",
                          "properties": {"reach_id": reach, "threshold": threshold,
                                         "expected_prov": pid, "layer_date": LAYER_DATE},
                          "geometry": {"type": "Point", "coordinates": _outlet_point(pid)}})
    return {"type": "FeatureCollection", "features": feats}


def build_flood_extent_geojson() -> dict:
    """ground truth (gold) — พื้นที่น้ำท่วมจริง = union polygon จังหวัด gold (GADM) จาก GISTDA."""
    feats = []
    for pid in GOLD_FLOODED:
        feats.append({"type": "Feature",
                      "properties": {"event": EVENT_ID, "prov_id": pid,
                                     "source": "GISTDA NORU2022 (thaiwater) + GADM4.1 geometry",
                                     "layer_date": LAYER_DATE},
                      "geometry": _prov_geometry(pid)})
    return {"type": "FeatureCollection", "features": feats}


def build_event_state() -> dict:
    return {"event_id": EVENT_ID, "period": EVENT_PERIOD, "layer_date": LAYER_DATE,
            "reservoir_active": RESERVOIR_ACTIVE, "reach_level": REACH_LEVEL,
            "gold_flooded": GOLD_FLOODED}


def build_news_corpus() -> list[dict]:
    """ข่าวน้ำท่วม (สำหรับ vector-rag). coverage bias เหมือนข่าวจริง:
    อยุธยา/กรุงเทพ/นครสวรรค์ ถูกรายงานหนัก; สิงห์บุรี/อ่างทอง/ชัยนาท/ปทุมฯ เบาบาง —
    สะท้อนว่าข่าว 'เห็น' จังหวัดใหญ่ แต่พลาดจังหวัดเล็กปลายสาย. Bangkok ถูกพูดถึงบ่อย
    (แต่ gold ไม่ท่วม → เป็น false positive ของ vector).
    """
    return [
        {"id": "N1", "date": "2022-10-01",
         "text": "สถานการณ์น้ำเจ้าพระยายังวิกฤต น้ำท่วมพระนครศรีอยุธยาขยายวงกว้าง "
                 "หลายชุมชนริมแม่น้ำถูกน้ำท่วมสูง เฝ้าระวังกรุงเทพมหานครและปริมณฑล"},
        {"id": "N2", "date": "2022-10-02",
         "text": "เขื่อนเจ้าพระยาเพิ่มการระบายน้ำ กระทบพื้นที่ท้ายน้ำ อยุธยา และเขตเศรษฐกิจ "
                 "กรุงเทพมหานคร ประชาชนเตรียมรับมือ"},
        {"id": "N3", "date": "2022-10-03",
         "text": "น้ำเหนือหลากลงนครสวรรค์ ระดับน้ำปากน้ำโพสูงขึ้นต่อเนื่อง "
                 "น้ำท่วมนครสวรรค์หลายอำเภอ"},
        {"id": "N4", "date": "2022-10-05",
         "text": "อยุธยาอ่วม น้ำท่วมโบราณสถาน นักท่องเที่ยวลด เจ้าหน้าที่เร่งสูบน้ำ "
                 "ขณะกรุงเทพยังเฝ้าระวังน้ำทะเลหนุน"},
        {"id": "N5", "date": "2022-10-06",
         "text": "รายงานพิเศษ: ทำไมกรุงเทพจึงเสี่ยงน้ำท่วมทุกปี ระบบระบายน้ำและคันกั้นน้ำ "
                 "เจ้าพระยา การบริหารเขื่อน"},
        {"id": "N6", "date": "2022-10-07",
         "text": "น้ำท่วมสิงห์บุรีบางพื้นที่ริมเจ้าพระยา ชาวบ้านขนของหนีน้ำ"},
        {"id": "N7", "date": "2022-10-08",
         "text": "ชัยนาทเฝ้าระวังน้ำล้นตลิ่ง หลังเขื่อนเจ้าพระยาระบายเพิ่ม "
                 "พื้นที่การเกษตรได้รับผลกระทบ"},
        {"id": "N8", "date": "2022-10-09",
         "text": "ภาพรวมลุ่มเจ้าพระยา: น้ำจากเขื่อนภูมิพลและสิริกิติ์ไหลรวมที่ปากน้ำโพ "
                 "ก่อนลงเจ้าพระยาตอนล่าง กระทบหลายจังหวัด"},
    ]


def build_deprecated_fixture_flood_extent() -> dict:
    """เก็บ ground truth เดิม (box + gold fixture 6 จังหวัด) ไว้เทียบย้อนหลัง (Item 3 ไม่ลบทิ้ง)."""
    polys = []
    for pid in _FALLBACK_GOLD:
        lon, lat, *_ = PROVINCES[pid]
        polys.append(_box(lon, lat))
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature",
         "properties": {"event": EVENT_ID, "source": "DEPRECATED fixture (box, tuned gold 6 จว.)",
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
    # เก็บ ground truth เดิมไว้ (ไม่ลบ) สำหรับเทียบ fixture↔real
    (out / "gistda_flood_extent_fixture_deprecated.geojson").write_text(
        json.dumps(build_deprecated_fixture_flood_extent(), ensure_ascii=False, indent=2), "utf-8")
    (out / "event_state.json").write_text(json.dumps(build_event_state(), ensure_ascii=False, indent=2), "utf-8")
    (out / "news_corpus.json").write_text(json.dumps(build_news_corpus(), ensure_ascii=False, indent=2), "utf-8")
    return out


if __name__ == "__main__":
    p = write_all()
    print(f"fixtures written to {p}")
