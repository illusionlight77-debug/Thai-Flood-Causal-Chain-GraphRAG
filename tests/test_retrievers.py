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
def test_causal_traceable_for_2hop_but_misses_confluence_after_spec_active():
    # หลังแก้ threshold circularity (2026-07-27): causal อธิบายจังหวัด 2-hop (บาร์ราจเจ้าพระยา)
    # ได้พร้อม evidence แต่ *พลาด* จังหวัดจุดบรรจบ 4-hop เพราะเขื่อนเหนือ retaining ปี 2565.
    from src.rag.causal_graphrag import CausalGraphRAG
    c = _graph_or_skip()
    lower_2hop = {"Sing Buri", "Ang Thong", "Ayutthaya", "Pathum Thani"}
    # 2-hop province: traceable + ทำนายชุดที่ราบลุ่มล่าง, hop=2
    a2 = CausalGraphRAG(c).answer("ทำไมจังหวัดพระนครศรีอยุธยาถึงน้ำท่วม", province="Ayutthaya")
    assert a2.is_traceable
    assert a2.provinces == lower_2hop
    assert a2.hops == 2
    # 4-hop province (นครสวรรค์): พลาด → ไม่มี chain/evidence → ไม่ traceable (สะท้อน limitation)
    a4 = CausalGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    assert "Nakhon Sawan" not in a4.provinces
    assert not a4.is_traceable


@pytest.mark.integration
def test_entity_overincludes_and_untraceable():
    from src.rag.entity_graphrag import EntityGraphRAG
    from src.rag.causal_graphrag import CausalGraphRAG
    c = _graph_or_skip()
    ent = EntityGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    cau = CausalGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    assert not ent.is_traceable
    assert len(ent.provinces) > len(cau.provinces)  # baseline เกินจริง
