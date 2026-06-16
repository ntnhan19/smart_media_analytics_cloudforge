# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Builder: cài dependencies vào virtual-env để tái dùng ở stage 2
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Không hỏi interactive khi cài apt
ENV DEBIAN_FRONTEND=noninteractive

# Cài build tools cần thiết để compile wheels (cv2, numpy, ...)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Virtual-env
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy và cài Python dependencies trước (layer cache hiệu quả)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Runtime: ảnh gọn nhẹ, chỉ chứa những gì cần thiết
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# ── Runtime system deps ───────────────────────────────────────────────────────
# ffmpeg  — video encoding/decoding (proxy creation)
# libgl1  — OpenCV runtime (cv2)
# libglib2.0-0, libsm6, libxext6 — OpenCV GUI libs (headless env)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -version 2>&1 | head -1   # Sanity check — ảnh bị thiếu ffmpeg thì fail build

# Copy virtual-env từ builder
COPY --from=builder /opt/venv /opt/venv

# ── App source ────────────────────────────────────────────────────────────────
WORKDIR /app

# Copy toàn bộ ai_pipeline package
COPY ai_pipeline/ ./ai_pipeline/

# Entrypoint script nằm trong package (ai_pipeline/ecs)
# symlink ra /app/entrypoint.py để dễ dàng gọi ở CMD
RUN ln -s /app/ai_pipeline/ecs/entrypoint.py /app/entrypoint.py

# ── Working dirs ──────────────────────────────────────────────────────────────
# /tmp/ecs_task  — task workspace, cleaned up after each run
# /app/data      — mount point for persistent data (thumbnails, logs)
RUN mkdir -p /tmp/ecs_task /app/data/thumbnails /app/data/logs

# ── Runtime env defaults (overridden by ECS task definition) ─────────────────
ENV STORAGE_BACKEND="minio" \
    TASK_TMP_DIR="/tmp/ecs_task" \
    LOG_LEVEL="INFO"

# ── Non-root user for security ────────────────────────────────────────────────
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /tmp/ecs_task
USER appuser

# ── Healthcheck (ECS checks this to confirm container started successfully) ───
# Chỉ kiểm tra import — không cần server port cho short-lived task
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=1 \
    CMD python -c "from ai_pipeline.database.storage_client import StorageClientFactory; print('OK')"

# ── Entrypoint ────────────────────────────────────────────────────────────────
# ECS Task Definition truyền input qua environment variable hoặc argument override
# Ví dụ ECS override: ["python", "entrypoint.py", "--config-path", "/tmp/input.json"]
CMD ["python", "entrypoint.py", "--help"]