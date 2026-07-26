"""Phase 0 smoke — config โหลดได้ + port ไม่ชนกันเองในโปรเจกต์."""
from src.config import settings


def test_settings_loads():
    assert settings.neo4j_user
    assert settings.project_crs.startswith("EPSG:")


def test_ports_are_distinct():
    # กันพลาดตั้งพอร์ตชนกันเองภายในโปรเจกต์
    ports = [settings.neo4j_http_port, settings.neo4j_bolt_port, settings.streamlit_port]
    assert len(ports) == len(set(ports)), "project ports must be unique"


def test_default_ports_avoid_known_conflicts():
    # 7474/7475/7687/7688 ถูกจองโดย Neo4j อื่นในเครื่องนี้แล้ว
    taken = {7474, 7475, 7687, 7688, 8000, 8001, 8080, 8081, 8100, 8200}
    assert settings.neo4j_http_port not in taken
    assert settings.neo4j_bolt_port not in taken
