FROM python:3.11-slim

LABEL maintainer="EchoScene Team"
LABEL description="FastAPI backend for EchoScene AI media management"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir "pip==23.3.2" "setuptools==70.3.0" "wheel"

# Install all dependencies from requirements.txt
# Note: torch is NOT needed — all AI models run via Ollama HTTP API,
# and faster-whisper uses ctranslate2 (not torch).
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/media

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]