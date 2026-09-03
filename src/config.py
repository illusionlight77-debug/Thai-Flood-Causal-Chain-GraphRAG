"""Central config — จุดเดียวที่อ่าน env/port/creds ทั้งโปรเจกต์.

โมดูลอื่นควร `from src.config import settings` แทนการอ่าน os.environ ตรง ๆ
เพื่อให้ port/creds ตรงกันระหว่าง docker-compose, Python และ tests.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()  # โหลด .env ถ้ามี (ไม่มีก็ใช้ default)
except ImportError:  # dotenv ยังไม่ติดตั้งตอน scaffold — ไม่เป็นไร
    pass

ROOT = Path(__file__).resolve().parent.parent


def _get(key: str, default: str) -> str:
    return os.environ.get(key, default)


@dataclass(frozen=True)
class Settings:
    # ── Neo4j ──────────────────────────────────────────────
    neo4j_uri: str = field(default_factory=lambda: _get("NEO4J_URI", "bolt://localhost:7689"))
    neo4j_user: str = field(default_factory=lambda: _get("NEO4J_USER", "neo4j"))
    neo4j_password: str = field(default_factory=lambda: _get("NEO4J_PASSWORD", "floodgraph123"))
    neo4j_http_port: int = field(default_factory=lambda: int(_get("NEO4J_HTTP_PORT", "7476")))
    neo4j_bolt_port: int = field(default_factory=lambda: int(_get("NEO4J_BOLT_PORT", "7689")))

    # ── UI ─────────────────────────────────────────────────
    streamlit_port: int = field(default_factory=lambda: int(_get("STREAMLIT_PORT", "8501")))

    # ── LLM / embeddings ───────────────────────────────────
    anthropic_api_key: str = field(default_factory=lambda: _get("ANTHROPIC_API_KEY", ""))
    gistda_api_key: str = field(default_factory=lambda: _get("GISTDA_API_KEY", ""))  # sphere basemap
    anthropic_model: str = field(default_factory=lambda: _get("ANTHROPIC_MODEL", "claude-opus-4-8"))
    embedding_provider: str = field(default_factory=lambda: _get("EMBEDDING_PROVIDER", "huggingface"))
    embedding_model: str = field(default_factory=lambda: _get("EMBEDDING_MODEL", "BAAI/bge-m3"))

    # ── data endpoints (ยืนยันจริงตอนเฟส 1) ─────────────────
    datagoth_ckan_base: str = field(default_factory=lambda: _get("DATAGOTH_CKAN_BASE", "https://data.go.th/api/3/action"))
    thaiwater_api_base: str = field(default_factory=lambda: _get("THAIWATER_API_BASE", "https://api.thaiwater.net/v1"))
    gistda_stac_base: str = field(default_factory=lambda: _get("GISTDA_STAC_BASE", "https://disaster.gistda.or.th/api/stac"))

    # ── geo ────────────────────────────────────────────────
    project_crs: str = field(default_factory=lambda: _get("PROJECT_CRS", "EPSG:32647"))

    # ── paths ──────────────────────────────────────────────
    data_raw_dir: Path = field(default_factory=lambda: ROOT / _get("DATA_RAW_DIR", "data/raw"))
    data_processed_dir: Path = field(default_factory=lambda: ROOT / _get("DATA_PROCESSED_DIR", "data/processed"))


settings = Settings()
