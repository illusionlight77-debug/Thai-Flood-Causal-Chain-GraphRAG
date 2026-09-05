"""FastAPI backend สำหรับหน้า UI ใหม่ (แทน Streamlit).

รัน:  uvicorn src.web.server:app --host 0.0.0.0 --port 8501
เสิร์ฟ web/index.html + API (ข้อมูล precomputed จาก build_ui_data) + proxy GISTDA
(basemap tiles + live flood) โดย key อยู่ฝั่ง server เท่านั้น (ไม่หลุดไป client).
"""
from __future__ import annotations

import json
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response

from src.config import settings

ROOT = Path(__file__).resolve().parent.parent.parent
WEB = ROOT / "web"
PROCESSED = settings.data_processed_dir

EVENTS = [("2022", "เจ้าพระยา 2565 (โนรู)"),
          ("2021", "เจ้าพระยา 2564 (เตี้ยนหมู่)"),
          ("2024", "เจ้าพระยา 2567"),
          ("2023", "เจ้าพระยา 2566"),
          ("ne2026", "โขง/อีสาน (live)")]

app = FastAPI(title="Thai Flood Causal-Chain GraphRAG")


@app.get("/")
def index():
    f = WEB / "index.html"
    if not f.exists():
        return JSONResponse({"error": "web/index.html not found"}, status_code=404)
    return FileResponse(str(f))


@app.get("/lab")
def lab():
    """หน้า research/measurement — แสดงทุกอย่างที่ทำ + ผลการทดลองทั้งหมด."""
    f = WEB / "lab.html"
    if not f.exists():
        return JSONResponse({"error": "web/lab.html not found"}, status_code=404)
    return FileResponse(str(f))


@app.get("/warn")
def warn():
    """หน้า early-warning (what-if) — ตั้งว่าลุ่มน้ำสาขาใดกำลังล้น → กราฟเตือนจังหวัดปลายน้ำ + lead-time."""
    f = WEB / "warn.html"
    if not f.exists():
        return JSONResponse({"error": "web/warn.html not found"}, status_code=404)
    return FileResponse(str(f))


_SUBBASINS = ["Ping", "Wang", "Yom", "Nan", "SakaeKrang", "Pasak", "ChaoPhraya", "ThaChin"]


@app.get("/api/early-warning")
def early_warning(overflowing: str = ""):
    """รับ 'ลุ่มน้ำสาขาที่กำลังล้น' (comma-separated) → ทำนายจังหวัดที่จะท่วม + lead-time.
    เป็น query-time (ไม่แตะ reach.overflow ที่เก็บไว้) → operator tool."""
    subs = [s.strip() for s in overflowing.split(",") if s.strip()] or ["ChaoPhraya"]
    try:
        from src.graph.client import Neo4jClient
        from src.graph import queries
        c = Neo4jClient()
        rows = c.run(queries.EARLY_WARNING_PREDICT, overflowing=subs)
        c.close()
        out = [{"province": r["province"], "province_th": r["province_th"],
                "lead_hours": int(r["lead_hours"]) if r["lead_hours"] is not None else None,
                "chain": r["chain"]} for r in rows]
        from src.eval.risk_warning import annotate  # #4 probability + risk
        out = annotate(out)
        return {"available": True, "overflowing": subs, "subbasins": _SUBBASINS,
                "warnings": out, "count": len(out)}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": str(exc), "subbasins": _SUBBASINS, "warnings": []}


@app.get("/api/report")
def report():
    """รวมผลการทดลองทั้งหมด (ทุก metric, 4-5 เหตุการณ์) สำหรับหน้า /lab แสดงละเอียดทีละส่วน."""
    out = {}
    for name in ("mcnemar", "pooled_significance", "discrimination", "lead_validation",
                 "blind_test", "dem_flow_accumulation", "dem_route_check", "dem_topology_check"):
        f = PROCESSED / f"{name}.json"
        out[name] = json.loads(f.read_text("utf-8")) if f.exists() else None
    # per-event summary (F1/POD/FAR/specificity/traceability + ablation)
    events = {}
    for y, lbl in EVENTS:
        f = WEB / f"ui_data_{y}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text("utf-8"))
        c = d["confusion"]["causal-graphrag"]
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        events[y] = {"label": lbl, "gold": sum(1 for p in d["provinces"] if d["per_province"][p]["is_gold"]),
                     "n": len(d["provinces"]),
                     "results": d.get("results"), "confusion": d.get("confusion"),
                     "ablation": d.get("ablation"), "faithfulness": d.get("faithfulness"),
                     "pod": round(tp / (tp + fn), 3) if (tp + fn) else 0,
                     "far": round(fp / (tp + fp), 3) if (tp + fp) else 0}
    out["events"] = events
    return out


@app.get("/api/track-record")
def track_record():
    """Roadmap B — สถิติการเตือนย้อนหลัง (case bank ถูก/ผิด + calibration) สำหรับหน้า /warn.
    ไม่แตะกราฟ/gate — เป็นชั้น 'บันทึก+ปรับความน่าจะเป็น' ที่กัน overfit (leave-one-event-out)."""
    def _load(name):
        f = PROCESSED / f"{name}.json"
        return json.loads(f.read_text("utf-8")) if f.exists() else None
    return {"case_bank": _load("case_bank"), "calibration": _load("calibration")}


@app.get("/api/config")
def config():
    events = [{"year": y, "label": lbl} for y, lbl in EVENTS
              if (WEB / f"ui_data_{y}.json").exists()]
    return {"events": events,
            "has_basemap": bool(settings.gistda_api_key),
            "has_live_flood": bool(settings.gistda_data_key)}


@app.get("/api/data/{year}")
def data(year: str):
    f = WEB / f"ui_data_{year}.json"
    if not f.exists():
        raise HTTPException(404, f"ui_data_{year}.json not found — รัน build_ui_data ก่อน")
    return JSONResponse(json.loads(f.read_text("utf-8")))


@app.get("/api/geo/provinces")
def provinces():
    f = PROCESSED / "provinces.geojson"
    if not f.exists():
        raise HTTPException(404, "provinces.geojson not found")
    return JSONResponse(json.loads(f.read_text("utf-8")))


@app.get("/api/gistda/basemap/{z}/{x}/{y}")
def gistda_basemap(z: int, x: int, y: int):
    """proxy basemap tile (key ฝั่ง server)."""
    key = settings.gistda_api_key
    if not key:
        raise HTTPException(404, "no GISTDA_API_KEY")
    url = (f"https://basemap.sphere.gistda.or.th/tiles/sphere_hybrid/EPSG3857/"
           f"{z}/{x}/{y}.jpeg?key={key}")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"tile error: {exc}")
    return Response(content=r.content, media_type="image/jpeg")


@app.get("/api/gistda/live-flood")
def live_flood(window: str = "30days"):
    """สรุปน้ำท่วมปัจจุบันรายจังหวัด (real-time, key ฝั่ง server)."""
    if not settings.gistda_data_key:
        return {"available": False, "provinces": []}
    try:
        from src.ingest.gistda_flood_api import summarize_by_province
        rows = summarize_by_province(window)
        return {"available": True, "window": window, "count": len(rows), "provinces": rows[:25]}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": str(exc), "provinces": []}
