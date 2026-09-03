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
def test_multi_hop_causal_paths_exist(loaded):
    # กราฟลุ่มเจ้าพระยาขยาย (2026-09-03): 8 ลุ่มน้ำสาขา · 23 จังหวัด → hop มีครบ 2/3/4/5
    # (2=จังหวัดต้นน้ำในสาขา, 3=เจ้าพระยาตอนล่างผ่านป่าสัก/สะแกกรัง, 4=จุดบรรจบปากน้ำโพ,
    #  5=ท่าจีนที่แยกจากเจ้าพระยา). hop วัดจากสถานีฝน (สาขาที่ไม่มีเขื่อนก็วัดได้).
    c, _ = loaded
    from src.graph import queries
    hops = {r["province"]: r["hops"] for r in c.run(queries.HOP_PER_PROVINCE)}
    assert {2, 3, 4, 5} <= set(hops.values())     # multi-hop granularity ครบ
    assert hops["Nakhon Sawan"] == 4              # จุดบรรจบ ผ่านปากน้ำโพ
    assert hops["Sukhothai"] == 2                 # ยมต้นน้ำ (runoff → reach → จังหวัด)
    assert hops["Suphan Buri"] == 5               # ท่าจีน (แยกจากเจ้าพระยาตอนบน)


@pytest.mark.integration
def test_prediction_reflects_real_gauge_gate(loaded):
    # กราฟขยาย: reach.overflow มาจาก RID SWOC gauge (อิสระจาก GISTDA satellite gold).
    # causal จับจังหวัดหลายลุ่มน้ำสาขาที่ลำน้ำล้นจริง (ยม/น่าน/ป่าสัก/ท่าจีน/เจ้าพระยา)
    # แต่พลาดจังหวัดลุ่มปิง (ตาก/กำแพงเพชร) ที่ลำน้ำหลักไม่ล้น = ฝนท้องถิ่น (honest FN, ไม่ tune).
    c, _ = loaded
    from src.graph import queries
    pred = {r["province"] for r in c.run(queries.CAUSAL_FLOOD_PREDICT)}
    gold = {fixtures.PROVINCES[p][3] for p in fixtures.GOLD_FLOODED}
    # จับได้หลายลุ่มน้ำสาขา (ทุกสายที่ RID บอกว่าล้นตลิ่ง):
    assert {"Nakhon Sawan", "Chai Nat"} <= pred                       # เจ้าพระยาตอนบน (จุดบรรจบ)
    assert {"Sing Buri", "Ang Thong", "Ayutthaya"} <= pred            # เจ้าพระยาตอนล่าง
    assert {"Sukhothai", "Phichit", "Phitsanulok"} <= pred            # ยม/น่าน (โมเดลใหม่จับได้)
    assert {"Lopburi", "Saraburi"} <= pred                           # ป่าสัก
    assert {"Suphan Buri", "Nakhon Pathom"} <= pred                  # ท่าจีน
    # honest FP/FN (ไม่ tune ให้ตรง gold):
    assert "Pathum Thani" in pred and "Pathum Thani" not in gold      # FP (ยังไม่ป้องกัน/threshold)
    assert {"Tak", "Kamphaeng Phet"} <= gold                          # อยู่ใน gold จริง (2565)
    assert not ({"Tak", "Kamphaeng Phet"} & pred)                    # miss (ลุ่มปิงไม่ล้น = ฝนท้องถิ่น)
    # คันกั้นน้ำ: กทม./นนทบุรี ไม่ถูกทำนาย แม้เจ้าพระยาล้น
    assert not ({"Bangkok", "Nonthaburi"} & pred)
