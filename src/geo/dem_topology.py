"""#4 DEM-ground the causal graph's flow topology with REAL elevation data.

Honest scope: this is NOT a full DEM flow-accumulation derivation (that needs a gridded
DEM + pysheds/richdem, heavy for this environment). Instead it uses a real satellite DEM
(Copernicus GLO-90, sampled via the open-meteo elevation API) to VALIDATE the hand-built
FLOWS_TO topology against physics: water flows downhill, so every FLOWS_TO edge must go
from a higher reach to a lower reach. This turns "hand-built, unverified topology" into
"hand-built, DEM-validated topology" and would immediately flag a mis-directed edge.

Elevations are cached to data/processed/dem_elevations.json so the check is reproducible
offline. A reach's elevation = mean elevation of the provinces it inundates; the Pak Nam
Pho confluence is sampled directly.

Usage:
    python -m src.geo.dem_topology            # fetch (or use cache) + validate
"""
from __future__ import annotations

import json

import requests

from src.config import settings
from src.ingest import fixtures

_CACHE = settings.data_processed_dir / "dem_elevations.json"
_CONFLUENCE = ("CONF-PAKNAMPHO", 15.70, 100.12)
_TOL = 3.0  # meters — allow near-ties (DEM noise / flat floodplain)


def _fetch_elevations(points: dict[str, tuple[float, float]]) -> dict[str, float]:
    """points: id -> (lat, lon). Returns id -> elevation_m. Cache-first."""
    if _CACHE.exists():
        cached = json.loads(_CACHE.read_text("utf-8")).get("elevation_m", {})
        if all(k in cached for k in points):
            return {k: float(cached[k]) for k in points}
    ids = list(points)
    lats = ",".join(str(points[i][0]) for i in ids)
    lons = ",".join(str(points[i][1]) for i in ids)
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    elevs = r.json()["elevation"]
    out = {ids[i]: float(elevs[i]) for i in range(len(ids))}
    _CACHE.write_text(json.dumps({
        "_meta": {"source": "Copernicus GLO-90 DEM via open-meteo elevation API",
                  "url": "https://api.open-meteo.com/v1/elevation", "unit": "meters"},
        "elevation_m": out}, ensure_ascii=False, indent=2), "utf-8")
    return out


def run() -> dict:
    # province centroids + confluence
    pts = {pid: (fixtures.PROVINCES[pid][1], fixtures.PROVINCES[pid][0]) for pid in fixtures.PROVINCES}
    pts[_CONFLUENCE[0]] = (_CONFLUENCE[1], _CONFLUENCE[2])
    elev = _fetch_elevations(pts)

    # reach elevation = mean elevation of inundated provinces
    reach_elev = {}
    for reach, targets in fixtures.REACH_INUNDATION.items():
        es = [elev[p] for p, _ in targets if p in elev]
        reach_elev[reach] = round(sum(es) / len(es), 1) if es else None
    node_elev = dict(reach_elev)
    node_elev[_CONFLUENCE[0]] = elev[_CONFLUENCE[0]]

    # check every FLOWS_TO edge is downhill (src >= dst - tol)
    edges = [(e["src"], e["dst"]) for e in fixtures.build_causal_edges() if e["type"] == "FLOWS_TO"]
    checks, bad = [], []
    for src, dst in edges:
        es, ed = node_elev.get(src), node_elev.get(dst)
        if es is None or ed is None:
            continue
        downhill = es >= ed - _TOL
        checks.append({"edge": f"{src}->{dst}", "src_m": es, "dst_m": ed, "downhill": downhill})
        if not downhill:
            bad.append(f"{src}({es}) -> {dst}({ed})")

    return {"n_edges": len(checks), "n_downhill": sum(1 for c in checks if c["downhill"]),
            "all_consistent": not bad, "violations": bad,
            "reach_elev_m": reach_elev, "confluence_m": elev[_CONFLUENCE[0]], "checks": checks}


def main() -> None:
    res = run()
    print(f"DEM (Copernicus GLO-90) topology check: {res['n_downhill']}/{res['n_edges']} "
          f"FLOWS_TO edges are downhill (tol {_TOL} m)")
    for c in res["checks"]:
        mark = "✔" if c["downhill"] else "✗"
        print(f"  {mark} {c['edge']:28s} {c['src_m']:>6} m → {c['dst_m']:>6} m")
    if res["all_consistent"]:
        print("✔ topology is DEM-consistent — every flow edge goes downhill (real elevation)")
    else:
        print("✗ DEM violations:", res["violations"])
    (settings.data_processed_dir / "dem_topology_check.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
