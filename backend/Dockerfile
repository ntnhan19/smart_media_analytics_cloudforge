FROM python:3.11-slim

LABEL maintainer="EchoScene Team"
LABEL description="FastAPI backend for EchoScene AI media management"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir "pip==23.3.2" "setuptools==70.3.0" "wheel"

# Install PyTorch CPU build first (avoids overwrite by requirements.txt)
RUN pip install --no-cache-dir \
    "torch==2.2.0+cpu" \
    "torchvision==0.17.0+cpu" \
    "torchaudio==2.2.0+cpu" \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies (exclude torch variants already installed above)
RUN grep -vE "^\s*(torch|torchvision|torchaudio|#|$)" requirements.txt \
    > /tmp/req_filtered.txt \
    && pip install --no-cache-dir -r /tmp/req_filtered.txt

COPY . .

RUN mkdir -p /app/data/media /app/data/chromadb

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]