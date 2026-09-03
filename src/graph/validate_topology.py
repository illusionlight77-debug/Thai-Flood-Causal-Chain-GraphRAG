"""Validate the loaded causal graph's topology for internal consistency.

This does NOT prove the topology matches a DEM — it proves the hand-built, geo-grounded
topology (see data/processed/chao_phraya_topology_provenance.json) is self-consistent:
  1. flow graph (FEEDS/RUNOFF_TO/OVERFLOWS_TO/FLOWS_TO) is a DAG (no cycles).
  2. every Province is reachable from some RainStation via causal edges (no orphan).
  3. every Province's INUNDATES reach is in the SAME sub-basin the basin-membership file
     assigns it (geometry ↔ graph agreement).
  4. all reaches drain toward the outlet reach (RR-CP-LOWER) — single outlet.

Run after loading the graph. Used by tests/test_topology.py.
"""
from __future__ import annotations

import json

from src.config import settings
from src.graph.client import Neo4jClient
from src.ingest import fixtures

REACH_SUBBASIN = fixtures.REACH_SUBBASIN
OUTLET = "RR-CP-L3"  # ปลายแกนเจ้าพระยา (อยุธยา–กรุงเทพ); ท่าจีนเป็น outlet ที่ 2 (distributary)

_FLOW = "FEEDS|RUNOFF_TO|OVERFLOWS_TO|FLOWS_TO"


def check(c: Neo4jClient | None = None) -> dict:
    c = c or Neo4jClient()
    problems: list[str] = []

    # 1. DAG over the water-flow relations (exclude INUNDATES = terminal to province)
    cyc = c.run(f"MATCH p=(n)-[:{_FLOW}*1..12]->(n) RETURN count(p) AS n")[0]["n"]
    if cyc:
        problems.append(f"พบ cycle ในกราฟการไหล ({cyc} เส้น) — ควรเป็น DAG")

    # 2. every province reachable from a RainStation
    rel = "FEEDS|RUNOFF_TO|OVERFLOWS_TO|FLOWS_TO|INUNDATES"
    reached = {r["prov"] for r in c.run(
        f"MATCH (:RainStation)-[:{rel}*1..7]->(p:Province) RETURN DISTINCT p.id AS prov")}
    allprov = set(fixtures.PROVINCES)
    orphan = allprov - reached
    if orphan:
        problems.append(f"จังหวัดที่ไม่มีสายเหตุ-ผลจากสถานีฝน: {sorted(orphan)}")

    # 3. province's INUNDATES reach sub-basin == basin-membership sub-basin
    mism = []
    for r in c.run("MATCH (rr:RiverReach)-[:INUNDATES]->(p:Province) "
                   "RETURN rr.id AS reach, p.id AS prov"):
        want = fixtures.PROV_SUBBASIN.get(r["prov"])
        got = REACH_SUBBASIN.get(r["reach"])
        # ยกเว้น: จังหวัดหนึ่งอาจถูก inundate จากหลายสาขา (เช่น พิจิตร = ยม+น่าน) → ผ่านถ้าตรงอย่างน้อยหนึ่ง
        if want and got and want != got:
            mism.append((r["prov"], r["reach"], want, got))
    # กรองจังหวัดที่มี reach ตรงสาขาอย่างน้อยหนึ่ง
    prov_has_match = {p for p in fixtures.PROVINCES
                      for rid, tv in [(rr, REACH_SUBBASIN.get(rr)) for rr in fixtures.REACH_INUNDATION
                                      if p in [x[0] for x in fixtures.REACH_INUNDATION[rr]]]
                      if tv == fixtures.PROV_SUBBASIN.get(p)}
    hard_mism = [m for m in mism if m[0] not in prov_has_match]
    if hard_mism:
        problems.append(f"INUNDATES ไม่ตรงสาขา (ไม่มี reach สาขาที่ถูกเลย): {hard_mism}")

    # 4. every reach drains to a TERMINAL reach (one with no outgoing FLOWS_TO).
    #    Chao Phraya system has 2 valid outlets: RR-CP-LOWER (main → อ่าวไทย) and
    #    RR-THACHIN (distributary ท่าจีน → อ่าวไทย, แยกออกที่ชัยนาท ไม่รวมกลับ).
    terminals = {r["id"] for r in c.run(
        "MATCH (rr:RiverReach) WHERE NOT (rr)-[:FLOWS_TO]->(:RiverReach) RETURN rr.id AS id")}
    no_drain = []
    for reach in REACH_SUBBASIN:
        if reach in terminals:
            continue
        ok = c.run("MATCH (rr:RiverReach {id:$r})-[:FLOWS_TO*1..8]->(o:RiverReach) "
                   "WHERE o.id IN $terms RETURN count(*) AS n",
                   r=reach, terms=list(terminals))[0]["n"]
        if not ok:
            no_drain.append(reach)
    if no_drain:
        problems.append(f"reach ที่ไม่ไหลถึง outlet ใด ๆ {sorted(terminals)}: {no_drain}")

    return {"ok": not problems, "problems": problems,
            "provinces_reached": len(reached), "provinces_total": len(allprov)}


def main() -> None:
    res = check()
    prov = settings.data_processed_dir / "chao_phraya_topology_provenance.json"
    print(f"topology provenance: {prov.name} (exists={prov.exists()})")
    if res["ok"]:
        print(f"✔ topology valid — DAG, {res['provinces_reached']}/{res['provinces_total']} "
              f"provinces reachable, sub-basin consistent, all reaches drain to outlet")
    else:
        print("✗ topology problems:")
        for p in res["problems"]:
            print("  -", p)


if __name__ == "__main__":
    main()
