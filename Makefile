# =============================================================================
# EchoScene — Makefile
# Shortcut commands for managing the Docker Compose stack
# =============================================================================
# Usage:
#   make up             -> Start the full stack (build images if needed)
#   make down           -> Stop and remove containers
#   make build          -> Rebuild all images
#   make logs           -> Stream logs from all services
#   make shell-backend  -> Open a shell inside the backend container
#   make shell-frontend -> Open a shell inside the frontend container
#   make clean          -> Remove containers and volumes (full reset)
#   make help           -> Show all available commands
# =============================================================================

.PHONY: up down build restart logs logs-backend logs-frontend logs-chromadb \
        shell-backend shell-frontend shell-db \
        health check-env init-dirs \
        clean clean-all help

# Terminal colors
CYAN  := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

# ---------------------------------------------------------------------------
# Stack management
# ---------------------------------------------------------------------------

## Start the full stack (build images if not already built)
up: check-env init-dirs
	@echo "$(CYAN)Starting EchoScene stack...$(RESET)"
	docker compose up --build -d
	@echo "$(GREEN)Stack is up!$(RESET)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  ChromaDB: http://localhost:8001"
	@echo "  MinIO:    http://localhost:9001"

## Stop and remove containers (volumes are preserved)
down:
	@echo "$(CYAN)Stopping EchoScene stack...$(RESET)"
	docker compose down
	@echo "$(GREEN)Stack stopped.$(RESET)"

## Rebuild all images without using cache
build:
	@echo "$(CYAN)Building all images...$(RESET)"
	docker compose build --no-cache
	@echo "$(GREEN)Build complete.$(RESET)"

## Restart the full stack
restart: down up

# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

## Stream logs from all services
logs:
	docker compose logs -f

## Stream logs from the backend service only
logs-backend:
	docker compose logs -f backend

## Stream logs from the frontend service only
logs-frontend:
	docker compose logs -f frontend

## Stream logs from the chromadb service only
logs-chromadb:
	docker compose logs -f chromadb

# ---------------------------------------------------------------------------
# Shell access
# ---------------------------------------------------------------------------

## Open a bash shell inside the backend container
shell-backend:
	docker compose exec backend bash

## Open a sh shell inside the frontend container (Alpine uses sh, not bash)
shell-frontend:
	docker compose exec frontend sh

## Open a psql session inside the postgres container
shell-db:
	docker compose exec postgres psql -U echoscene -d echoscene

# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

## Check the health status of all services
health:
	@echo "$(CYAN)Checking service health...$(RESET)"
	@echo -n "  Backend  (/health):           "
	@curl -sf http://localhost:8000/health && echo "$(GREEN)OK$(RESET)" || echo "FAIL"
	@echo -n "  ChromaDB (/api/v1/heartbeat): "
	@curl -sf http://localhost:8001/api/v1/heartbeat && echo "$(GREEN)OK$(RESET)" || echo "FAIL"
	@echo -n "  Frontend (port 5173):         "
	@curl -sf http://localhost:5173 > /dev/null && echo "$(GREEN)OK$(RESET)" || echo "FAIL"

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

## Remove containers and volumes (all local data will be lost)
clean:
	@echo "$(CYAN)Removing containers and volumes...$(RESET)"
	docker compose down -v --remove-orphans
	@echo "$(GREEN)Clean complete.$(RESET)"

## Remove containers, volumes, AND locally built images (full reset)
clean-all:
	@echo "$(CYAN)Full reset — removing containers, volumes, and images...$(RESET)"
	docker compose down -v --remove-orphans --rmi local
	@echo "$(GREEN)Full clean complete.$(RESET)"

# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

## Copy .env.example to .env if .env does not exist
check-env:
	@if [ ! -f .env ]; then \
		echo "$(CYAN).env not found — copying from .env.example...$(RESET)"; \
		cp .env.example .env; \
		echo "$(GREEN).env created. Review and update values if needed.$(RESET)"; \
	fi

## Create required bind-mount data directories
init-dirs:
	@mkdir -p data/media data/chromadb data/whisper_cache

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

## Show all available make commands
help:
	@echo ""
	@echo "$(CYAN)EchoScene — Available Make Commands$(RESET)"
	@echo "======================================"
	@grep -E '^##' Makefile | sed 's/## /  /'
	@echo ""
