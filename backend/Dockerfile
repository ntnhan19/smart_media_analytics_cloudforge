# ============================================================================
# BACKEND DOCKERFILE (Build từ thư mục gốc của dự án)
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="EchoScene Team"
LABEL description="FastAPI backend for EchoScene AI media management"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Chỉ copy và cài requirements của Backend
COPY backend/requirements.txt .

RUN pip install --no-cache-dir "pip==23.3.2" "setuptools==70.3.0" "wheel"
RUN pip install --no-cache-dir -r requirements.txt

# Copy code Backend
COPY backend/ ./

# COPY thư mục ai_pipeline ĐỂ BACKEND IMPORT SCHEMA/CONTRACT (Rất nhẹ, không cài thư viện AI)
COPY ai_pipeline/ ./ai_pipeline/

RUN mkdir -p /app/data/media

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]