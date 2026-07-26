"""Streamlit UI — "ทำไมจังหวัดนี้ถึงน้ำท่วม?"

เฟส 0: หน้า placeholder ที่ boot ได้จริงในคอนเทนเนอร์ + เช็คการเชื่อม Neo4j
เพื่อยืนยันว่า `docker compose up` ยกทั้ง stack ได้ในครั้งเดียว.
เฟส 6 จะเติม: เลือกจังหวัด+ช่วงเวลา, เทียบ 3 ระบบ, chain viewer, evidence panel,
overlay flood extent GISTDA, ตัวชี้วัดสด (hop/F1/traceability).
"""
from __future__ import annotations

import streamlit as st

from src.config import settings

st.set_page_config(page_title="Thai Flood Causal-Chain GraphRAG", page_icon="🌊", layout="wide")

st.title("🌊 ทำไมจังหวัดนี้ถึงน้ำท่วม?")
st.caption("Thai Flood Causal-Chain GraphRAG — Phase 0 scaffold (UI ยัง placeholder)")

with st.sidebar:
    st.header("การเชื่อมต่อ / Connections")
    st.write(f"**Neo4j URI:** `{settings.neo4j_uri}`")
    st.write(f"**Model:** `{settings.anthropic_model}`")
    st.write(f"**CRS:** `{settings.project_crs}`")

    if st.button("ทดสอบเชื่อม Neo4j"):
        try:
            from src.graph.client import Neo4jClient

            rows = Neo4jClient().run("RETURN 1 AS ok")
            st.success(f"Neo4j OK: {rows[0]['ok'] if rows else '?'}")
        except Exception as exc:  # noqa: BLE001 — แสดง error ตรง ๆ ในหน้า dev
            st.error(f"เชื่อม Neo4j ไม่ได้: {exc}")

st.info(
    "โครงเฟส 0 พร้อมแล้ว. เฟสถัดไปจะเติม: เลือกจังหวัด+ช่วงเวลา, เทียบ 3 ระบบ "
    "side-by-side, causal chain viewer, evidence panel, overlay flood extent."
)

col1, col2, col3 = st.columns(3)
for col, name in zip((col1, col2, col3), ("causal-graphrag", "entity-graphrag", "vector-rag")):
    with col:
        st.subheader(name)
        st.write("_รอเฟส 4 (retrievers)_")
