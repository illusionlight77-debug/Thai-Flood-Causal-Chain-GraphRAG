@echo off
REM รัน Sentinel-1 flood mapping ผ่าน Copernicus (openEO) — ดับเบิลคลิกไฟล์นี้ได้เลย
REM หรือพิมพ์  run_copernicus.bat  ใน cmd ที่โฟลเดอร์นี้
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

set PY="C:\Program Files\Python313\python.exe"
if not exist %PY% set PY=python

echo === รัน Copernicus Sentinel-1 flood extent ===
%PY% -m src.ingest.copernicus_flood_extent
echo.
echo === จบการทำงาน (ถ้ามีไฟล์ผลลัพธ์ = data\processed\copernicus_flood_2022.json) ===
pause
