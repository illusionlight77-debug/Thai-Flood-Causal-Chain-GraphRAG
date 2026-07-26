---
name: geo-basin-to-province
description: >
  Map river basins / river reaches to their DOWNSTREAM provinces using GeoPandas
  point-in-polygon (and polygon-intersect), producing the INUNDATES edges for the
  causal graph. Use for any GIS join in this repo — loading basin/province
  shapefiles or GeoJSON, reprojecting to one CRS, spatial joins, or overlaying
  GISTDA flood extent onto province polygons. Not for Neo4j/Cypher or retrieval
  scoring (use causal-graphrag).
---

# Skill: geo-basin-to-province

ใช้ทักษะ GeoPandas point-in-polygon ที่มีอยู่แล้ว (thesis + GraphRAG) มาทำ "ลุ่มน้ำ → จังหวัดท้ายน้ำ" — ไม่ต้องเรียนใหม่.
Reuse existing GeoPandas point-in-polygon skill for "basin → downstream province".

> ℹ️ ย้าย/symlink โฟลเดอร์นี้ไป `.claude/skills/` เพื่อให้ Claude Code โหลดอัตโนมัติ.

## 1. กติกาเหล็ก / Hard rules
1. **Reproject ทุกชั้นเป็น CRS เดียวก่อน spatial join** (แนะนำ EPSG:32647 / UTM 47N สำหรับไทย หรือ EPSG:4326 ถ้าทำงานเป็น lat/lon อย่างสม่ำเสมอ). CRS ไม่ตรง = จับจังหวัดผิด → บั๊คเงียบที่สุดในงานนี้.
2. ทุกผลลัพธ์ที่กลายเป็น edge ต้องบันทึก source (dataset id + วันที่ layer) เพื่อไปเป็น `evidence` ใน causal graph.

## 2. โหลด + จัดแนว CRS
```python
import geopandas as gpd
CRS = "EPSG:32647"  # ตัดสินใจครั้งเดียวใช้ทั้งโปรเจกต์
basins    = gpd.read_file("data/basin.geojson").to_crs(CRS)
provinces = gpd.read_file("data/province.geojson").to_crs(CRS)
reaches   = gpd.read_file("data/river_reach.geojson").to_crs(CRS)  # point/line ปลายน้ำ
```

## 3. Point-in-polygon: จุดปลายน้ำ → จังหวัด
```python
# reaches = จุด outlet/ปลายลำน้ำของแต่ละ reach
pip = gpd.sjoin(reaches, provinces[["prov_id","name_en","geometry"]],
                how="left", predicate="within")
# pip.name_en = จังหวัดที่ reach ไหลลงไปท่วม → ใช้สร้าง INUNDATES edge
```

## 4. Basin → downstream provinces (polygon intersect)
```python
bp = gpd.overlay(basins, provinces, how="intersection")
bp["area"] = bp.geometry.area
# กรอง sliver เล็ก ๆ ออก + จัดเรียงจังหวัดตามลำดับท้ายน้ำ (ใช้ river order/elevation ถ้ามี)
bp = bp[bp.area > MIN_AREA]
```

## 5. Overlay GISTDA flood extent → province (ground truth)
```python
flood = gpd.read_file("data/gistda_flood_extent.geojson").to_crs(CRS)
flooded = gpd.overlay(flood, provinces, how="intersection")
gold = set(flooded["name_en"].unique())   # = gold provinces สำหรับ eval
```

## 6. ส่งต่อไป causal graph
- ผลจาก §3/§4 → สร้าง `(:RiverReach)-[:INUNDATES {threshold, evidence}]->(:Province)` (ดู skill causal-graphrag).
- แนบ `evidence = {dataset:'D4/basin+province', timestamp: layer_date, station_id: reach_id}`.

## 7. Tests (pytest)
- ทดสอบด้วยจังหวัดที่รู้คำตอบแน่ ๆ (เช่น outlet ที่อยู่ในจังหวัด A ต้อง map เป็น A).
- assert ว่าทุก layer มี `.crs == CRS` หลัง reprojection.
- assert ไม่มี reach ที่ join แล้วได้ province = NaN (ถ้ามี = จุดหลุดขอบเขต → ตรวจ CRS/geometry).

## Anti-patterns
- ❌ sjoin ข้าม CRS.
- ❌ ใช้ centroid ของลุ่มน้ำแทนจุดปลายน้ำ (ได้จังหวัดกลางลุ่ม ไม่ใช่ท้ายน้ำ).
- ❌ ลืมกรอง sliver polygon จาก overlay → จังหวัดปลอมเพียบ.
