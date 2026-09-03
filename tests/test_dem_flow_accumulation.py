"""#2 pysheds flow-accumulation consistency. Uses the cached DEM grid
(data/processed/dem_grid.json) so it runs offline; skips if pysheds isn't installed
or the grid hasn't been sampled yet."""
import pytest

from src.config import settings

pytest.importorskip("pysheds")


@pytest.mark.skipif(not (settings.data_processed_dir / "dem_grid.json").exists(),
                    reason="run `python -m src.geo.dem_flow_accumulation` once to cache the DEM grid")
def test_flow_accumulation_matches_topology():
    from src.geo.dem_flow_accumulation import run
    res = run()
    assert res["consistent_with_flow_accumulation"], f"violations: {res['violations']}"
    assert res["distributary_confirmed"]  # Tha Chin low accumulation = distributary
