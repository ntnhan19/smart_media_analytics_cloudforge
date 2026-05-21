# =============================================================================
# EchoScene — Frontend Dockerfile
# Base image: node:20-alpine (lightweight, suitable for Node.js apps)
# Owner: M3 (Frontend Engineer)
# =============================================================================

FROM node:20-alpine

# Metadata
LABEL maintainer="EchoScene Team"
LABEL description="React/Vite frontend for EchoScene AI media management"

# Set working directory inside the container
WORKDIR /app

# ---------------------------------------------------------------------------
# Install dependencies first (leverage Docker layer cache)
# Copy only package files first — if source code changes but deps do not,
# Docker skips the npm install step entirely
# ---------------------------------------------------------------------------
COPY package*.json ./

RUN npm install

# Copy full source code into the container
# (In dev mode, the bind-mount will override this directory)
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# ---------------------------------------------------------------------------
# Run Vite dev server
# --host 0.0.0.0  required to accept connections from outside the container
# ---------------------------------------------------------------------------
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
