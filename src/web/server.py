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

EVENTS = [("2022", "เจ้าพระยา 2565 (พายุโนรู)"), ("2021", "เจ้าพระยา 2564 (พายุเตี้ยนหมู่)")]

app = FastAPI(title="Thai Flood Causal-Chain GraphRAG")


@app.get("/")
def index():
    f = WEB / "index.html"
    if not f.exists():
        return JSONResponse({"error": "web/index.html not found"}, status_code=404)
    return FileResponse(str(f))


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
