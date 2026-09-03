"""Topology validation (integration) — the geo-grounded flow graph must be a consistent
DAG matching sub-basin membership. Skips if Neo4j is unavailable."""
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
    load(c)
    yield c
    c.close()


@pytest.mark.integration
def test_topology_is_valid_dag(loaded):
    from src.graph.validate_topology import check
    res = check(loaded)
    assert res["ok"], f"topology invalid: {res['problems']}"
    assert res["provinces_reached"] == res["provinces_total"]  # ไม่มีจังหวัด orphan
