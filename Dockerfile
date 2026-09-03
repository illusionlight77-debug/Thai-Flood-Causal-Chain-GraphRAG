# ── app image: Python + geo stack + Streamlit ─────────────────
FROM python:3.11-slim

# geopandas/shapely/pyproj/fiona ต้องมี system libs (GEOS/GDAL/PROJ)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        proj-data \
        proj-bin \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ติดตั้ง core deps ก่อน copy code เพื่อใช้ layer cache
# (heavy/optional libs อยู่ใน requirements-optional.txt — ไม่ติดตั้งใน image หลัก)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# copy code (dev จะถูก override ด้วย volume mount ใน compose อีกที)
COPY . .

EXPOSE 8501

# healthcheck ของ FastAPI UI
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://localhost:8501/api/config || exit 1

CMD ["uvicorn", "src.web.server:app", "--host", "0.0.0.0", "--port", "8501"]
