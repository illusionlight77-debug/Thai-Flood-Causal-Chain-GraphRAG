"""เฟส 2 tests — point-in-polygon จับจังหวัดถูก + gold จาก flood overlay + CRS."""
import pytest

gpd = pytest.importorskip("geopandas")

from src.config import settings
from src.geo import basin_to_province as geo
from src.ingest import fixtures


@pytest.fixture(scope="module", autouse=True)
def _fixtures():
    fixtures.write_all()  # ให้แน่ใจว่ามี geojson ให้อ่าน


@pytest.mark.geo
def test_all_layers_reprojected_to_project_crs():
    for name in ("provinces.geojson", "reach_outlets.geojson", "gistda_flood_extent.geojson"):
        gdf = geo._load(name)
        assert gdf.crs.to_string() == settings.project_crs


@pytest.mark.geo
def test_reach_outlet_maps_to_expected_province():
    # known-answer: outlet ที่วางในจังหวัด expected_prov ต้อง PIP กลับเป็นจังหวัดนั้น
    pip = geo.reach_to_province()
    assert (pip["prov_id"] == pip["expected_prov"]).all()


@pytest.mark.geo
def test_no_unresolved_outlets():
    pip = geo.reach_to_province()
    assert pip["prov_id"].notna().all()


@pytest.mark.geo
def test_inundates_edges_have_complete_evidence():
    edges = geo.build_inundates_edges()
    assert edges
    for e in edges:
        ev = e["evidence"]
        assert all(ev.get(k) for k in ("station_id", "timestamp", "dataset"))


@pytest.mark.geo
def test_gold_matches_gistda_flooded_set():
    gold = geo.gold_provinces_from_flood()
    assert gold == set(fixtures.GOLD_FLOODED)
