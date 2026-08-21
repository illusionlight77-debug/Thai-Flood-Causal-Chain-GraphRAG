"""เฟส 4 tests — อินเทอร์เฟซร่วม + คุณสมบัติที่ต่างกันของ 3 retriever."""
import pytest

from src.ingest import fixtures
from src.geo import basin_to_province as geo
from src.rag.base import Retriever, RetrieverAnswer
from src.rag.vector_rag import VectorRAG


@pytest.fixture(scope="module", autouse=True)
def _data():
    fixtures.write_all()
    geo.main()


def _graph_or_skip():
    try:
        from src.graph.load import load
        from src.graph.client import Neo4jClient
        c = Neo4jClient(); c.run("RETURN 1"); load(c)
        return c
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Neo4j ไม่พร้อม: {exc}")


def test_vector_rag_is_a_retriever_and_no_evidence():
    v = VectorRAG()
    a = v.answer("ทำไมจังหวัดพระนครศรีอยุธยาถึงน้ำท่วม", province="Ayutthaya")
    assert isinstance(v, Retriever)
    assert isinstance(a, RetrieverAnswer)
    assert not a.is_traceable          # vector ไม่มี evidence เชิงโครงสร้าง
    assert "Ayutthaya" in a.provinces


@pytest.mark.integration
def test_causal_recovers_confluence_via_runoff_path():
    # หลังเติม runoff path (ฝน→น้ำท่า) + gate ด้วย river-gauge จริง: causal อธิบายจังหวัดจุดบรรจบ
    # (นครสวรรค์ 4-hop) ได้พร้อม chain ที่เริ่มจาก "สถานีฝน" และ evidence ครบ → traceable.
    from src.rag.causal_graphrag import CausalGraphRAG
    c = _graph_or_skip()
    # 2-hop province: traceable
    a2 = CausalGraphRAG(c).answer("ทำไมจังหวัดพระนครศรีอยุธยาถึงน้ำท่วม", province="Ayutthaya")
    assert a2.is_traceable and "Ayutthaya" in a2.provinces and a2.hops == 2
    # 4-hop confluence (นครสวรรค์): กู้คืนได้ + chain เริ่มจากฝน (runoff) ไม่ใช่เขื่อนล้น
    a4 = CausalGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    assert "Nakhon Sawan" in a4.provinces and a4.is_traceable and a4.hops == 4
    assert "ฝน" in a4.chain[0]                                   # ต้นสายเป็นสถานีฝน (runoff)
    # ยังพลาดต้นน้ำที่ท่วมจากฝนท้องถิ่น (ลำน้ำหลักไม่ล้น) — honest limitation
    aT = CausalGraphRAG(c).answer("ทำไมจังหวัดตากถึงน้ำท่วม", province="Tak")
    assert "Tak" not in aT.provinces


@pytest.mark.integration
def test_entity_overincludes_and_untraceable():
    from src.rag.entity_graphrag import EntityGraphRAG
    from src.rag.causal_graphrag import CausalGraphRAG
    c = _graph_or_skip()
    ent = EntityGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    cau = CausalGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    assert not ent.is_traceable
    assert len(ent.provinces) > len(cau.provinces)  # baseline เกินจริง
