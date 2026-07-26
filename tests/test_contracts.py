"""Test retriever contract — Evidence/RetrieverAnswer + traceability flag."""
from src.rag.base import Evidence, RetrieverAnswer
from src.rag.causal_graphrag import CausalGraphRAG
from src.rag.entity_graphrag import EntityGraphRAG
from src.rag.vector_rag import VectorRAG


def test_evidence_completeness():
    assert Evidence("S1", "2022-10-01T00:00", "D1").is_complete
    assert not Evidence("S1", None, "D1").is_complete


def test_answer_traceable_requires_complete_evidence():
    good = RetrieverAnswer(text="x", evidence=[Evidence("S1", "t", "D1")])
    bad = RetrieverAnswer(text="x", evidence=[Evidence("S1", None, "D1")])
    empty = RetrieverAnswer(text="x")
    assert good.is_traceable
    assert not bad.is_traceable
    assert not empty.is_traceable


def test_all_retrievers_expose_name():
    for cls in (CausalGraphRAG, EntityGraphRAG, VectorRAG):
        assert isinstance(cls.name, str) and cls.name
