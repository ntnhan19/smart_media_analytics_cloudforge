# =============================================================================
# EchoScene — Frontend Dockerfile
# Base image: node:20-alpine (lightweight, fast build)
# Owner: M3 (Frontend Engineer)
# =============================================================================

FROM node:20-alpine

# Metadata
LABEL maintainer="EchoScene Team"
LABEL description="React/Vite frontend for EchoScene AI media management"

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
RUN apk add --no-cache curl

# Set working directory inside the container
WORKDIR /app

# ---------------------------------------------------------------------------
# Install Node dependencies first (leverage Docker layer cache)
# Copy only package files first — if source code changes but deps do not,
# Docker skips the npm install step entirely
# ---------------------------------------------------------------------------
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps --prefer-offline

# Copy full source code into the container
# (In dev mode, the bind-mount will override this directory)
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# ---------------------------------------------------------------------------
# Start Vite dev server
# --host 0.0.0.0  required to accept connections from outside the container
# --port 5173     explicit port binding
# ---------------------------------------------------------------------------
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
