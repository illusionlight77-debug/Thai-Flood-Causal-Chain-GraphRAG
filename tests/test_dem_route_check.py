"""#3 D8 flow-routing reproduces the main-stem topology. Offline (cached DEM grid)."""
import pytest

from src.config import settings

pytest.importorskip("pysheds")


@pytest.mark.skipif(not (settings.data_processed_dir / "dem_grid.json").exists(),
                    reason="run `python -m src.geo.dem_flow_accumulation` once to cache the DEM grid")
def test_main_stem_edges_reproduced_by_routing():
    from src.geo.dem_route_check import run
    res = run()
    # coarse ~11km DEM should reproduce the main-stem backbone (>= 7 of 11 edges);
    # misses are the Tha Chin distributary + sub-grid tributary junctions (documented).
    assert res["n_confirmed_by_routing"] >= 7
