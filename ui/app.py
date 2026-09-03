"""Streamlit UI — "ทำไมจังหวัดนี้ถึงน้ำท่วม?"

เทียบ 3 ระบบ side-by-side + causal chain viewer + evidence panel + overlay flood extent
(GISTDA) + ตัวชี้วัดสด (hop / F1 / traceability). อ่านกราฟจาก Neo4j + fixture ที่ ingest แล้ว.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# streamlit วาง path เป็นโฟลเดอร์ ui/ → เพิ่ม repo root เพื่อ import src.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.config import settings
from src.eval.f1_by_hop import f1
from src.ingest import fixtures
from src.rag._common import province_names

st.set_page_config(page_title="ทำไมจังหวัดนี้ถึงน้ำท่วม", page_icon="🌊", layout="wide")

SYS_ORDER = ["causal-graphrag", "entity-graphrag", "vector-rag"]
SYS_DESC = {
    "causal-graphrag": "ของเรา — เดินสายเหตุ-ผลจริง + evidence",
    "entity-graphrag": "baseline — entity-relation (ไม่สนทิศ/หลักฐาน)",
    "vector-rag": "baseline — ค้นข่าวด้วย vector",
}


@st.cache_resource(show_spinner="เชื่อมต่อ Neo4j + สร้าง retrievers…")
def get_retrievers():
    from src.rag.registry import build_retrievers
    return build_retrievers()


@st.cache_data
def gold_set() -> set[str]:
    return {fixtures.PROVINCES[p][3] for p in fixtures.GOLD_FLOODED}


def evidence_panel(ans):
    if not ans.evidence:
        st.caption("— ไม่มี evidence เชิงโครงสร้าง —")
        return
    for i, e in enumerate(ans.evidence, 1):
        badge = "✅" if e.is_complete else "⚠️"
        with st.expander(f"{badge} evidence #{i}: {e.dataset or '?'}"):
            st.write(f"**station_id:** `{e.station_id}`")
            st.write(f"**timestamp:** `{e.timestamp}`")
            st.write(f"**dataset:** `{e.dataset}`")


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("🌊 ตั้งค่า")
    st.caption(f"เหตุการณ์: **ลุ่มเจ้าพระยา {fixtures.EVENT_PERIOD}**")
    names = province_names()
    en_by_th = {v["th"]: v["en"] for v in names.values()}
    gold_th = [fixtures.PROVINCES[p][2] for p in fixtures.GOLD_FLOODED]
    _default = gold_th.index("นครสวรรค์") if "นครสวรรค์" in gold_th else 0  # default = เคสตัวอย่าง runoff
    prov_th = st.selectbox("เลือกจังหวัด (จังหวัดที่ท่วมจริงตาม GISTDA)", gold_th, index=_default)
    province = en_by_th[prov_th]
    st.divider()
    st.caption(f"Neo4j: `{settings.neo4j_uri}`")
    st.caption(f"Ground truth (gold): {', '.join(sorted(gold_set()))}")

st.title("ทำไมจังหวัดนี้ถึงน้ำท่วม? 🌊")
st.caption("Thai Flood Causal-Chain GraphRAG — เทียบ 3 ระบบบนคำถามเดียวกัน "
           "(ground truth = flood extent GISTDA)")

question = f"ทำไมจังหวัด{prov_th}ถึงน้ำท่วมในเหตุการณ์ลุ่มเจ้าพระยาปี 2565?"
st.info(f"**คำถาม:** {question}")

gold = gold_set()

try:
    retrievers = get_retrievers()
except Exception as exc:  # noqa: BLE001
    st.error(f"เชื่อม Neo4j ไม่ได้ — รัน `docker compose up -d` และโหลดกราฟก่อน "
             f"(`python -m src.graph.load`).\n\n{exc}")
    st.stop()

# ── รันทั้ง 3 ระบบ ─────────────────────────────────────────────
answers = {name: retrievers[name].answer(question, province=province) for name in SYS_ORDER}

cols = st.columns(3)
for col, name in zip(cols, SYS_ORDER):
    ans = answers[name]
    pred = set(ans.provinces)
    score = f1(pred, gold)
    with col:
        st.subheader(name)
        st.caption(SYS_DESC[name])
        m1, m2, m3 = st.columns(3)
        m1.metric("hop", ans.hops)
        m2.metric("F1", f"{score:.2f}")
        m3.metric("trace", "✓" if ans.is_traceable else "✗")
        st.caption(f"⏱ {ans.latency_s*1000:.1f} ms · ทำนาย {len(pred)} จังหวัด")
        st.write(ans.text)
        # correctness แยกจังหวัด
        tp = sorted(pred & gold)
        fp = sorted(pred - gold)
        miss = sorted(gold - pred)
        if tp:   st.success("ถูก (∈gold): " + ", ".join(tp))
        if fp:   st.error("เกิน (∉gold): " + ", ".join(fp))
        if miss: st.warning("ตกหล่น: " + ", ".join(miss))

st.divider()

# ── Causal chain viewer + evidence (ของ causal-graphrag) ───────
left, right = st.columns([3, 2])
with left:
    st.subheader("🔗 Causal chain viewer (causal-graphrag)")
    ca = answers["causal-graphrag"]
    if ca.chain:
        st.markdown("  →  ".join(f"**{c}**" for c in ca.chain))
        st.caption(f"ความยาวสายเหตุ-ผล = {ca.hops}-hop "
                   f"({'ข้ามลุ่มน้ำผ่านจุดบรรจบ' if ca.hops >= 4 else 'เขื่อนเดียว'})")
    else:
        st.caption("ไม่พบ chain")
with right:
    st.subheader("🧾 Evidence panel")
    st.caption("คลิกดู source record ที่ทำให้คำตอบ traceable (H1)")
    evidence_panel(answers["causal-graphrag"])

st.divider()

# ── แผนที่ overlay flood extent GISTDA ─────────────────────────
st.subheader("🗺️ Overlay flood extent (GISTDA) เทียบคำตอบ")
try:
    import pydeck as pdk

    prov_gj = json.loads((settings.data_processed_dir / "provinces.geojson").read_text("utf-8"))
    flood_gj = json.loads((settings.data_processed_dir / "gistda_flood_extent.geojson").read_text("utf-8"))
    causal_pred = answers["causal-graphrag"].provinces
    for f in prov_gj["features"]:
        f["properties"]["predicted"] = f["properties"]["name_en"] in causal_pred

    layers = []
    # ถ้ามี GISTDA sphere key → ใช้ basemap ของ GISTDA เป็นพื้นหลัง (verified: basemap tiles ใช้ได้)
    if settings.gistda_api_key:
        tile_url = ("https://basemap.sphere.gistda.or.th/tiles/sphere_hybrid/EPSG3857/"
                    "{z}/{x}/{y}.jpeg?key=" + settings.gistda_api_key)
        layers.append(pdk.Layer("TileLayer", data=tile_url, min_zoom=0, max_zoom=19, tile_size=256))
    layers += [
        pdk.Layer("GeoJsonLayer", flood_gj, get_fill_color=[30, 120, 220, 90],
                  stroked=False, pickable=False),
        pdk.Layer("GeoJsonLayer", prov_gj, get_fill_color=(
            "properties.predicted ? [220, 60, 60, 70] : [160, 160, 160, 25]"),
                  get_line_color=[90, 90, 90], line_width_min_pixels=1, pickable=True),
    ]
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=15.0, longitude=100.3, zoom=6.2),
        layers=layers, tooltip={"text": "{name_en}"}))
    _bm = "GISTDA sphere basemap" if settings.gistda_api_key else "ไม่มี basemap (ใส่ GISTDA_API_KEY ใน .env ได้)"
    st.caption(f"🔵 พื้นที่น้ำท่วมจริง (GISTDA)  ·  🔴 จังหวัดที่ causal-graphrag ทำนายว่าท่วม  ·  🗺️ {_bm}")
except Exception as exc:  # noqa: BLE001
    st.caption(f"(แผนที่ pydeck ใช้ไม่ได้: {exc}) — แสดงเป็นรายการแทน")
    st.write("gold:", ", ".join(sorted(gold)))
