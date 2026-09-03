"""#4 DEM-consistency of the flow topology. Uses the cached Copernicus DEM elevations
(data/processed/dem_elevations.json) so it runs offline / without Neo4j."""
import pytest

from src.config import settings


@pytest.mark.skipif(not (settings.data_processed_dir / "dem_elevations.json").exists(),
                    reason="run `python -m src.geo.dem_topology` once to cache DEM elevations")
def test_flow_edges_go_downhill():
    from src.geo.dem_topology import run
    res = run()
    assert res["n_edges"] >= 8
    assert res["all_consistent"], f"DEM violations (flow edge going uphill): {res['violations']}"
    assert res["n_downhill"] == res["n_edges"]
