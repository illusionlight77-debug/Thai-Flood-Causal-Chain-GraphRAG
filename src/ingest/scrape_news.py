"""เฟส Item 2 — scrape ข่าวจริงเกี่ยวกับน้ำท่วมลุ่มเจ้าพระยา (เน้นเหตุการณ์ 2565)
จาก Google News RSS (มี real url + source + published_date) → ขยาย vector corpus.

เขียนผลลง data/processed/news_corpus_v2.jsonl (1 บรรทัด/ข่าว) พร้อม metadata:
  {id, source, url, published_date, year, title, text}

หมายเหตุความซื่อสัตย์: Google News RSS คืนข่าว "ปัจจุบัน" เป็นหลัก → corpus จะผสม
ข่าวร่วมสมัย (2565) กับข่าวย้อนหลัง/อ้างอิงเหตุการณ์เดียวกัน. เราเก็บ `year` ไว้ทุกชิ้น
และรายงานสัดส่วนปีใน README เพื่อไม่ให้เข้าใจผิดว่าเป็นข่าว 2565 ล้วน.
กรอง: title ต้องมี (จังหวัดลุ่มเจ้าพระยา) และ (คำเกี่ยวกับน้ำ/เขื่อน/น้ำท่วม).
"""
from __future__ import annotations

import json
import re
import time
from urllib.parse import quote
from xml.etree import ElementTree as ET

import requests

from src.config import settings

RSS = "https://news.google.com/rss/search?q={q}&hl=th&gl=TH&ceid=TH:th"
HEADERS = {"User-Agent": "thai-flood-graphrag/0.2 (research)"}

# จังหวัดลุ่มเจ้าพระยา (ชื่อไทย + ชื่อย่อที่ข่าวใช้) — ใช้กรอง + tag
PROVINCE_ALIASES = {
    "Nakhon Sawan": ["นครสวรรค์", "ปากน้ำโพ"], "Chai Nat": ["ชัยนาท"],
    "Sing Buri": ["สิงห์บุรี"], "Ang Thong": ["อ่างทอง"],
    "Ayutthaya": ["พระนครศรีอยุธยา", "อยุธยา"], "Pathum Thani": ["ปทุมธานี"],
    "Nonthaburi": ["นนทบุรี"], "Bangkok": ["กรุงเทพ"],
    "Tak": ["ตาก"], "Phitsanulok": ["พิษณุโลก"],
}
WATER_KW = ["น้ำท่วม", "อุทกภัย", "ระบายน้ำ", "เขื่อน", "น้ำล้น", "ตลิ่ง", "เจ้าพระยา", "น้ำเหนือ"]

QUERIES = [
    "น้ำท่วม เจ้าพระยา 2565", "อุทกภัย ลุ่มเจ้าพระยา 2565",
    "เขื่อนเจ้าพระยา ระบายน้ำ 2565", "น้ำท่วม ตุลาคม 2565 ภาคกลาง",
    "น้ำเหนือ ปากน้ำโพ นครสวรรค์ 2565", "เขื่อนภูมิพล สิริกิติ์ ระบายน้ำ 2565",
] + [f"น้ำท่วม {al[0]} 2565" for al in PROVINCE_ALIASES.values()]


def _provinces_in(text: str) -> list[str]:
    hits = []
    for en, aliases in PROVINCE_ALIASES.items():
        if any(a in text for a in aliases):
            hits.append(en)
    return hits


def fetch_rss(query: str) -> list[dict]:
    url = RSS.format(q=quote(query))
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"  [rss fail] {query}: {exc}")
        return []
    root = ET.fromstring(r.content)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        src_el = item.find("source")
        source = (src_el.text if src_el is not None else "").strip()
        year = None
        m = re.search(r"\b(20\d{2})\b", pub)
        if m:
            year = int(m.group(1))
        out.append({"title": title, "url": link, "published_date": pub,
                    "year": year, "source": source})
    return out


def scrape() -> list[dict]:
    seen: set[str] = set()
    rows: list[dict] = []
    for q in QUERIES:
        items = fetch_rss(q)
        print(f"  '{q}': {len(items)} raw")
        for it in items:
            title = it["title"]
            key = title[:80]
            if key in seen or not title:
                continue
            provs = _provinces_in(title)
            if not provs or not any(k in title for k in WATER_KW):
                continue  # กรองให้เกี่ยวข้องจริง
            seen.add(key)
            rows.append({**it, "provinces": provs})
        time.sleep(1.0)  # สุภาพกับ endpoint
    for i, r in enumerate(rows, 1):
        r["id"] = f"V2-{i:03d}"
        r["text"] = r["title"]  # vector-rag ใช้ title เป็น text (headline-level corpus)
    return rows


def main() -> None:
    rows = scrape()
    out = settings.data_processed_dir / "news_corpus_v2.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    years: dict = {}
    for r in rows:
        years[r["year"]] = years.get(r["year"], 0) + 1
    print(f"\nเขียน {len(rows)} ข่าว → {out}")
    print("แยกตามปี:", dict(sorted(years.items(), key=lambda x: (x[0] is None, x[0]))))


if __name__ == "__main__":
    main()
