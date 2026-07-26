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

# ติดตั้ง deps ก่อน copy code เพื่อใช้ layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# copy code (dev จะถูก override ด้วย volume mount ใน compose อีกที)
COPY . .

EXPOSE 8501

# healthcheck ของ Streamlit
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
