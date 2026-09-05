"""Parse a RID SWOC (กรมชลประทาน) situation bulletin PDF → per-sub-basin over-bank gate.

เครื่องมือสำหรับ **lever 1 ของ Roadmap B**: แปลง bulletin (ระดับน้ำ vs ตลิ่ง ต่อสถานี — *อิสระ*
จากภาพน้ำท่วม GISTDA) → `river_reach_overbank_{event}.json` (gate input) แบบ de-circularized.

ที่มาของ gate = สถานีวัดน้ำ RID (สูง/ต่ำกว่าตลิ่ง) → **ไม่ใช่เฉลย** → ใช้ตั้ง overflow ได้ตามกติกา integrity.
รหัสสถานี → ลุ่มน้ำสาขา: P.*=ปิง · W.*=วัง · Y.*=ยม · N.*=น่าน · C.*=เจ้าพระยา · S.*=ป่าสัก · T.*=ท่าจีน.

หมายเหตุ: อ่านส่วน *prose* ("แม่น้ำ... สถานี X ... สูง/ต่ำกว่าตลิ่ง N เมตร") ซึ่งเป็นที่มาเดียวกับ gate 2565.
ตารางสรุปรายสถานี (layout ซับซ้อน) ยังไม่ parse — ถ้า bulletin เหตุการณ์จริงมี prose ครบก็เพียงพอ.

Usage:
    python -m src.ingest.rid_bulletin --url http://water.rid.go.th/flood/flood/daily.pdf --event current
    python -m src.ingest.rid_bulletin --pdf path/to/bulletin_2024-10-05.pdf --event 2024 --write
"""
from __future__ import annotations

import argparse
import json
import re

import requests

from src.config import settings

PREFIX_SUBBASIN = {"P": "Ping", "W": "Wang", "Y": "Yom", "N": "Nan",
                   "C": "ChaoPhraya", "S": "Pasak", "T": "ThaChin"}
# strip RID PDF private-use glyphs (U+F700–F70F) + Thai tone/above marks (U+0E47–0E4E)
_MARKS = re.compile("[-็-๎]")


def _normalize(text: str) -> str:
    return _MARKS.sub("", text).replace("\n", " ")


def download(url: str, timeout: int = 60) -> bytes:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.content


def extract_text(pdf_bytes: bytes) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "".join(doc[i].get_text() for i in range(doc.page_count))


def parse_stations(text: str) -> list[dict]:
    """คืน [{station, subbasin, over_bank, margin_m}] จาก 'สถานี X ... (สูง/ต่ำ)กว่าตลิ่ง N ม.'.
    ทำบนข้อความที่ strip วรรณยุกต์แล้ว: 'ตลิ่ง'→'ตลิง', 'สูงกว่า'→'สูงกวา', 'ต่ำ/ตํ่า'→'ตา/ตำ'."""
    t = _normalize(text)
    out, seen = [], set()
    for m in re.finditer(r"สถานี\s*([A-Z]\.?\s*\d+[A-Z0-9]*)", t):
        code = re.sub(r"\s+", "", m.group(1))
        prefix = code.split(".")[0][:1].upper()
        sub = PREFIX_SUBBASIN.get(prefix)
        if sub is None or (code, sub) in seen:
            continue
        seg = t[m.end(): m.end() + 200]
        over = margin = None
        mb = re.search(r"กวาตลิง\s*([\d.]+)?", seg)          # 'กว่าตลิ่ง N'
        if mb:
            pre = seg[max(0, mb.start() - 8): mb.start()]
            over = ("สูง" in pre) or ("เหนือ" in pre)
            margin = mb.group(1)
        elif re.search(r"เหนือ\S{0,3}ตลิง", seg):            # 'เหนือตลิ่ง' = สูงกว่า
            over = True
        else:
            continue
        seen.add((code, sub))
        try:
            margin_m = float(margin) if margin else None
        except ValueError:
            margin_m = None
        out.append({"station": code, "subbasin": sub, "over_bank": bool(over), "margin_m": margin_m})
    return out


def to_overbank_json(stations: list[dict], event: str, source: str) -> dict:
    """per-sub-basin overflow: สถานีใดในลุ่มน้ำ 'สูงกว่าตลิ่ง' → ลุ่มน้ำนั้น overflow=true."""
    subs: dict[str, dict] = {}
    for s in stations:
        cur = subs.setdefault(s["subbasin"], {"overflow": False, "stations": []})
        cur["overflow"] = cur["overflow"] or bool(s["over_bank"])
        cur["stations"].append({k: s[k] for k in ("station", "over_bank", "margin_m")})
    return {"_meta": {"description": f"Sub-basin over-bank gate for {event} — parsed from RID SWOC "
                      "bulletin (river-gauge, independent of GISTDA satellite gold).",
                      "source": source, "rule": "any station in a sub-basin above bank -> overflow"},
            "overflow": {k: v["overflow"] for k, v in subs.items()},
            "detail": subs}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--pdf")
    ap.add_argument("--event", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    source = a.url or a.pdf
    data = download(a.url) if a.url else open(a.pdf, "rb").read()
    stations = parse_stations(extract_text(data))
    res = to_overbank_json(stations, a.event, source)
    over = [k for k, v in res["overflow"].items() if v]
    print(f"parsed {len(stations)} stations · over-bank sub-basins: {over or 'none'}")
    for s in stations:
        print(f"  {s['station']:8s} {s['subbasin']:11s} "
              f"{'OVER' if s['over_bank'] else 'below'} ({s['margin_m']} m)")
    if a.write:
        out = settings.data_processed_dir / f"river_reach_overbank_{a.event}.json"
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
