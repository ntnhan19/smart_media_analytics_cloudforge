# ============================================================================
# AI PIPELINE DOCKERFILE (Build từ thư mục gốc của dự án)
# ============================================================================
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ai_pipeline/Requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -version 2>&1 | head -1

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY ai_pipeline/ ./ai_pipeline/
COPY utils/ ./utils/

RUN ln -s /app/ai_pipeline/ecs/entrypoint.py /app/entrypoint.py
RUN mkdir -p /tmp/ecs_task /app/data/thumbnails /app/data/logs

ENV STORAGE_BACKEND="s3" \
    TASK_TMP_DIR="/tmp/ecs_task" \
    LOG_LEVEL="INFO"

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /tmp/ecs_task
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=1 \
    CMD python -c "from ai_pipeline.database.storage_client import StorageClientFactory; print('OK')"

CMD ["python", "entrypoint.py", "--help"]