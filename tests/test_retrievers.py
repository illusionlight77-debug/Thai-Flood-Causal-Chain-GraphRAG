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
def test_causal_is_traceable_and_matches_gold():
    from src.rag.causal_graphrag import CausalGraphRAG
    c = _graph_or_skip()
    a = CausalGraphRAG(c).answer("ทำไมจังหวัดพระนครศรีอยุธยาถึงน้ำท่วม", province="Ayutthaya")
    gold = {fixtures.PROVINCES[p][3] for p in fixtures.GOLD_FLOODED}
    assert a.is_traceable
    assert a.provinces == gold
    assert a.hops == 2


@pytest.mark.integration
def test_entity_overincludes_and_untraceable():
    from src.rag.entity_graphrag import EntityGraphRAG
    from src.rag.causal_graphrag import CausalGraphRAG
    c = _graph_or_skip()
    ent = EntityGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    cau = CausalGraphRAG(c).answer("ทำไมจังหวัดนครสวรรค์ถึงน้ำท่วม", province="Nakhon Sawan")
    assert not ent.is_traceable
    assert len(ent.provinces) > len(cau.provinces)  # baseline เกินจริง
