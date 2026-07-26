"""Helper ร่วมของ retriever — province name resolution + news corpus."""
from __future__ import annotations

import json
from functools import lru_cache

from src.config import settings


@lru_cache(maxsize=1)
def province_names() -> dict[str, dict]:
    """{prov_id: {th, en}} จาก fixture provinces.geojson."""
    gj = json.loads((settings.data_processed_dir / "provinces.geojson").read_text("utf-8"))
    out = {}
    for f in gj["features"]:
        p = f["properties"]
        out[p["prov_id"]] = {"th": p["name_th"], "en": p["name_en"]}
    return out


def resolve_province(question: str, province: str | None = None) -> str | None:
    """คืน name_en ของจังหวัดที่ถามถึง (จาก kwarg หรือ parse จากคำถาม th/en)."""
    names = province_names()
    if province:
        for v in names.values():
            if province in (v["en"], v["th"]) or province == v["en"]:
                return v["en"]
        return province
    for v in names.values():
        if v["th"] in question or v["en"].lower() in question.lower():
            return v["en"]
    return None


@lru_cache(maxsize=1)
def news_corpus() -> list[dict]:
    return json.loads((settings.data_processed_dir / "news_corpus.json").read_text("utf-8"))


# ชื่อย่อที่ข่าวจริงมักใช้ (ไม่ตรงชื่อทางการเป๊ะ)
_ALIASES: dict[str, list[str]] = {
    "AYUTTHAYA": ["อยุธยา"],
    "BANGKOK": ["กรุงเทพ"],
}


def provinces_mentioned(text: str) -> set[str]:
    """หา name_en ของจังหวัดที่ถูกกล่าวถึงใน text (match ชื่อทางการ th/en + ชื่อย่อ)."""
    low = text.lower()
    hits = set()
    for pid, v in province_names().items():
        names = [v["th"], v["en"].lower()] + _ALIASES.get(pid, [])
        if any(n in text or n in low for n in names):
            hits.add(v["en"])
    return hits
