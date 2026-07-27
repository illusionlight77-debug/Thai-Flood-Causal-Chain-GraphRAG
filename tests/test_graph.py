"""เฟส 3 tests (integration) — skip ถ้าไม่มี Neo4j. โหลดกราฟแล้วตรวจ hop + evidence."""
import pytest

from src.ingest import fixtures
from src.geo import basin_to_province as geo


def _client_or_skip():
    try:
        from src.graph.client import Neo4jClient
        c = Neo4jClient()
        c.run("RETURN 1")
        return c
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Neo4j ไม่พร้อม: {exc}")


@pytest.fixture(scope="module")
def loaded():
    fixtures.write_all()
    geo.main()
    from src.graph.load import load
    c = _client_or_skip()
    counts = load(c)
    yield c, counts
    c.close()


@pytest.mark.integration
def test_all_edges_have_evidence(loaded):
    _, counts = loaded
    assert counts["edges_without_evidence"] == 0


@pytest.mark.integration
def test_two_and_four_hop_paths_exist(loaded):
    c, _ = loaded
    from src.graph import queries
    hops = {r["province"]: r["hops"] for r in c.run(queries.HOP_PER_PROVINCE)}
    assert 2 in hops.values() and 4 in hops.values()
    assert hops["Nakhon Sawan"] == 4  # cross-basin ผ่านปากน้ำโพ
    assert hops["Ayutthaya"] == 2     # เขื่อนเจ้าพระยาโดยตรง


@pytest.mark.integration
def test_threshold_prediction_reflects_spec_driven_active(loaded):
    # หลังแก้ threshold circularity (2026-07-27): active มาจาก dam_specs.json (สถานะจริงปี 2565)
    # → มีเพียงเขื่อนเจ้าพระยา (barrage) ที่ active; ภูมิพล/สิริกิติ์ retaining (ไม่ล้นสปิลเวย์).
    # ดังนั้น causal ทำนายได้เฉพาะจังหวัดที่ราบลุ่มล่าง (2-hop) และ *พลาด* จังหวัดจุดบรรจบ
    # (นครสวรรค์/ชัยนาท 4-hop) เพราะเหตุจริงคือ runoff+barrage ไม่ใช่เขื่อนล้น. เดิม pred==gold
    # (ตอน active=all True แบบ tuned) — เปลี่ยนเป็นสะท้อนความจริง ไม่ใช่ผลที่เข้าข้างตัวเอง.
    c, _ = loaded
    from src.graph import queries
    pred = {r["province"] for r in c.run(queries.CAUSAL_FLOOD_PREDICT)}
    gold = {fixtures.PROVINCES[p][3] for p in fixtures.GOLD_FLOODED}
    lower_2hop = {"Sing Buri", "Ang Thong", "Ayutthaya", "Pathum Thani"}
    assert pred == lower_2hop            # barrage-driven 2-hop เท่านั้น
    assert pred < gold                   # เป็น subset — พลาดจังหวัดจุดบรรจบ
    assert "Nakhon Sawan" not in pred and "Chai Nat" not in pred
