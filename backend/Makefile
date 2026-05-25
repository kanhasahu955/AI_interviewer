# Interviewer AI - backend Makefile
#
# Targets are grouped:
#   - setup:       sync deps, init storage
#   - run:         start API / worker / livekit agent
#   - dev:         all three at once via tmux or background pids
#   - ops:         db tables, redis ping, healthcheck, smoke tests
#   - tooling:     format / lint / parse-check / clean

SHELL          := /usr/bin/env bash
PYTHON         := .venv/bin/python
UV             := uv
HOST           ?= 0.0.0.0
PORT           ?= 8000
WORKERS        ?= 1
ENV_FILE       ?= .env

# All targets that don't produce a like-named file.
.PHONY: help install sync lock upgrade env-check storage \
        api api-prod worker livekit dev dev-bg dev-stop dev-logs status _dev-preflight \
        db-init db-drop db-use-mysql db-use-snowflake db-provider redis-ping health connections smoke \
        mysql-up mysql-down mysql-logs mysql-shell redis-up redis-down quickstart \
        docker-build docker-up docker-down docker-logs docker-ps docker-shell \
        docker-rebuild docker-clean docker-health \
        hostinger-build-web hostinger-up hostinger-down hostinger-logs hostinger-ps \
        format lint parse-check clean nuke

help: ## Show this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ─────────────────────────── setup ────────────────────────────────────────────

install: ## Install/refresh python deps via uv sync.
	$(UV) sync

sync: install ## Alias for `install`.

lock: ## Regenerate uv.lock.
	$(UV) lock

upgrade: ## Upgrade all deps to their latest matching versions.
	$(UV) lock --upgrade && $(UV) sync

env-check: ## Verify .env exists.
	@test -f $(ENV_FILE) || (echo "Missing $(ENV_FILE)"; exit 1)
	@echo "$(ENV_FILE) OK"

storage: ## Make sure local storage directory exists.
	@mkdir -p storage/resumes
	@echo "storage/ ready"

# ─────────────────────────── run ──────────────────────────────────────────────

api: env-check storage ## Run FastAPI with --reload (dev).
	$(PYTHON) -m uvicorn main:app --reload --host $(HOST) --port $(PORT)

api-prod: env-check storage ## Run FastAPI without reload, multi-worker.
	$(PYTHON) -m uvicorn main:app --host $(HOST) --port $(PORT) --workers $(WORKERS)

worker: env-check ## Run the RQ background worker (resume/JD ingest, reports).
	$(PYTHON) -m app.jobs.worker

livekit: env-check ## Run the LiveKit Agents worker (joins each interview room).
	$(PYTHON) -m app.livekit_agent.worker dev

# ─────────────────────────── dev: all three at once ───────────────────────────

PID_DIR        := .run
API_PID        := $(PID_DIR)/api.pid
WORKER_PID     := $(PID_DIR)/worker.pid
LIVEKIT_PID    := $(PID_DIR)/livekit.pid
LOG_DIR        := .run/logs

$(PID_DIR) $(LOG_DIR):
	@mkdir -p $@

# Internal: kill anything left over from a previous run so port 8000 + the
# RQ/livekit workers don't collide on the next start.
_dev-preflight: $(PID_DIR)
	@echo ">> preflight: clearing stale dev processes"
	@for p in $(API_PID) $(WORKER_PID) $(LIVEKIT_PID); do \
	  if [ -f $$p ]; then \
	    pid=$$(cat $$p); kill $$pid 2>/dev/null; rm -f $$p; \
	  fi; \
	done
	@pkill -f "uvicorn main:app" 2>/dev/null || true
	@pkill -f "app.jobs.worker" 2>/dev/null || true
	@pkill -f "app.livekit_agent.worker" 2>/dev/null || true
	@lsof -ti :$(PORT) 2>/dev/null | xargs kill -9 2>/dev/null || true
	@sleep 1
	@echo ">> preflight: ensuring Redis is up (required for transcript + proctoring)"
	@$(PYTHON) -c "import sys; sys.path.insert(0,'.'); from app.core.redis_client import ping_redis; ping_redis()" 2>/dev/null \
	  || $(MAKE) redis-up

# `make dev` runs all three processes with live, multiplexed logs in the
# current terminal. A single Ctrl+C stops all of them cleanly.
dev: env-check storage _dev-preflight $(LOG_DIR) ## Run API + RQ worker + LiveKit agent in the foreground with live logs (Ctrl+C stops all).
	@echo ">> starting api, worker, livekit-agent (Ctrl+C to stop all)"
	@: > $(LOG_DIR)/api.log; : > $(LOG_DIR)/worker.log; : > $(LOG_DIR)/livekit.log
	@trap 'echo; echo ">> stopping..."; \
	   for p in $(API_PID) $(WORKER_PID) $(LIVEKIT_PID); do \
	     [ -f $$p ] && kill $$(cat $$p) 2>/dev/null; rm -f $$p; \
	   done; exit 0' INT TERM; \
	 ( $(PYTHON) -u -m uvicorn main:app --reload --host $(HOST) --port $(PORT) 2>&1 \
	     | sed -u 's/^/[api]      /' \
	     | tee $(LOG_DIR)/api.log ) & echo $$! > $(API_PID); \
	 ( $(PYTHON) -u -m app.jobs.worker 2>&1 \
	     | sed -u 's/^/[worker]   /' \
	     | tee $(LOG_DIR)/worker.log ) & echo $$! > $(WORKER_PID); \
	 ( $(PYTHON) -u -m app.livekit_agent.worker dev 2>&1 \
	     | sed -u 's/^/[livekit]  /' \
	     | tee $(LOG_DIR)/livekit.log ) & echo $$! > $(LIVEKIT_PID); \
	 wait

dev-bg: env-check storage _dev-preflight $(LOG_DIR) ## Start the same trio in the background (logs go to .run/logs/). Use `make dev-stop` later.
	@echo ">> starting api"
	@$(PYTHON) -u -m uvicorn main:app --reload --host $(HOST) --port $(PORT) > $(LOG_DIR)/api.log 2>&1 & echo $$! > $(API_PID)
	@echo ">> starting rq worker"
	@$(PYTHON) -u -m app.jobs.worker > $(LOG_DIR)/worker.log 2>&1 & echo $$! > $(WORKER_PID)
	@echo ">> starting livekit agent"
	@$(PYTHON) -u -m app.livekit_agent.worker dev > $(LOG_DIR)/livekit.log 2>&1 & echo $$! > $(LIVEKIT_PID)
	@sleep 1
	@$(MAKE) -s status

dev-stop: ## Stop API + worker + livekit started via `make dev-bg`.
	@for p in $(API_PID) $(WORKER_PID) $(LIVEKIT_PID); do \
	  if [ -f $$p ]; then \
	    pid=$$(cat $$p); \
	    if kill -0 $$pid 2>/dev/null; then kill $$pid && echo "stopped $$p (pid=$$pid)"; fi; \
	    rm -f $$p; \
	  fi; \
	done

dev-logs: ## Tail all three dev logs.
	@touch $(LOG_DIR)/api.log $(LOG_DIR)/worker.log $(LOG_DIR)/livekit.log
	@tail -n 40 -f $(LOG_DIR)/api.log $(LOG_DIR)/worker.log $(LOG_DIR)/livekit.log

status: ## Report which dev processes are running.
	@for name in api worker livekit; do \
	  pidf=$(PID_DIR)/$$name.pid; \
	  if [ -f $$pidf ] && kill -0 $$(cat $$pidf) 2>/dev/null; then \
	    echo "  $$name   running (pid=$$(cat $$pidf))"; \
	  else \
	    echo "  $$name   stopped"; \
	  fi; \
	done

# ─────────────────────────── ops ──────────────────────────────────────────────

db-init: ## Create DB tables (runs SQLModel metadata.create_all).
	$(PYTHON) -c "import sys; sys.path.insert(0,'.'); from app.core.database import create_db_and_tables; create_db_and_tables(); print('tables ready')"

db-provider: ## Show the currently configured DB_PROVIDER.
	@grep -E "^DB_PROVIDER=" $(ENV_FILE) || echo "DB_PROVIDER not set"

db-use-mysql: ## Switch .env to DB_PROVIDER=mysql (recommended for OLTP).
	@if grep -qE "^DB_PROVIDER=" $(ENV_FILE); then \
	  sed -i.bak -E 's/^DB_PROVIDER=.*/DB_PROVIDER=mysql/' $(ENV_FILE); \
	else \
	  echo "DB_PROVIDER=mysql" >> $(ENV_FILE); \
	fi
	@echo "DB_PROVIDER=mysql (backup at $(ENV_FILE).bak)"

db-use-snowflake: ## Switch .env to DB_PROVIDER=snowflake (OLTP works via explicit sequences).
	@if grep -qE "^DB_PROVIDER=" $(ENV_FILE); then \
	  sed -i.bak -E 's/^DB_PROVIDER=.*/DB_PROVIDER=snowflake/' $(ENV_FILE); \
	else \
	  echo "DB_PROVIDER=snowflake" >> $(ENV_FILE); \
	fi
	@echo "DB_PROVIDER=snowflake (backup at $(ENV_FILE).bak)"
	@echo "Schemas auto-adapted: indexes stripped, JSON->VARIANT, integer PKs"
	@echo "use Snowflake SEQUENCEs (id assigned client-side per insert)."
	@echo "Next: 'make db-drop && make db-init' to (re)create tables, then 'make dev'."

db-drop: ## Drop ALL Interviewer-AI tables (and sequences if Snowflake). Use before re-running db-init after a schema change.
	@echo ">> dropping all Interviewer AI tables on $$(grep -E '^DB_PROVIDER=' $(ENV_FILE) | cut -d= -f2)"
	@$(PYTHON) -c "import sys; sys.path.insert(0,'.'); \
	from app import models; \
	from app.core.database import engine; \
	from sqlmodel import SQLModel; \
	from sqlalchemy import inspect, Sequence; \
	insp = inspect(engine); \
	SQLModel.metadata.drop_all(engine); \
	print('tables dropped')"

# ─────────────────────────── local dev infra (mysql, redis containers) ──────

MYSQL_CONTAINER ?= interviewer-mysql
MYSQL_PORT      ?= 3306
REDIS_CONTAINER ?= interviewer-redis
REDIS_PORT      ?= 6379

mysql-up: ## Run a local MySQL 8 container (port 3306, root/password, db=interviewer_ai).
	@if [ -z "$$(docker ps -q -f name=^/$(MYSQL_CONTAINER)$$)" ]; then \
	  docker rm -f $(MYSQL_CONTAINER) 2>/dev/null || true; \
	  echo ">> starting $(MYSQL_CONTAINER) on :$(MYSQL_PORT)"; \
	  docker run -d --name $(MYSQL_CONTAINER) \
	    -p $(MYSQL_PORT):3306 \
	    -e MYSQL_ROOT_PASSWORD=password \
	    -e MYSQL_DATABASE=interviewer_ai \
	    mysql:8.4 >/dev/null && \
	  echo ">> waiting for mysql to be ready..."; \
	  for i in $$(seq 1 40); do \
	    if docker exec $(MYSQL_CONTAINER) mysqladmin ping -h127.0.0.1 -uroot -ppassword >/dev/null 2>&1; then \
	      echo ">> mysql ready"; break; \
	    fi; sleep 1; \
	  done; \
	else \
	  echo "$(MYSQL_CONTAINER) already running"; \
	fi

mysql-down: ## Stop the local MySQL container.
	@docker rm -f $(MYSQL_CONTAINER) 2>/dev/null && echo "stopped" || echo "not running"

mysql-logs: ## Tail MySQL container logs.
	@docker logs -f $(MYSQL_CONTAINER)

mysql-shell: ## Open a mysql shell inside the container.
	@docker exec -it $(MYSQL_CONTAINER) mysql -uroot -ppassword interviewer_ai

redis-up: ## Run local Redis on :6379 (Docker container, or Homebrew redis-server fallback).
	@$(PYTHON) -c "import sys; sys.path.insert(0,'.'); from app.core.redis_client import ping_redis; ping_redis()" 2>/dev/null \
	  && echo "redis already reachable on :$(REDIS_PORT)" \
	  || { \
	    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
	      if [ -z "$$(docker ps -q -f name=^/$(REDIS_CONTAINER)$$)" ]; then \
	        docker rm -f $(REDIS_CONTAINER) 2>/dev/null || true; \
	        echo ">> starting $(REDIS_CONTAINER) on :$(REDIS_PORT)"; \
	        docker run -d --name $(REDIS_CONTAINER) -p $(REDIS_PORT):6379 redis:7-alpine >/dev/null; \
	      else \
	        echo "$(REDIS_CONTAINER) already running"; \
	      fi; \
	    elif command -v redis-server >/dev/null 2>&1; then \
	      if [ -f $(PID_DIR)/redis.pid ] && kill -0 $$(cat $(PID_DIR)/redis.pid) 2>/dev/null; then \
	        echo "redis-server already running (pid $$(cat $(PID_DIR)/redis.pid))"; \
	      else \
	        echo ">> starting redis-server on :$(REDIS_PORT)"; \
	        redis-server --daemonize yes --port $(REDIS_PORT) --pidfile $(PID_DIR)/redis.pid; \
	      fi; \
	    else \
	      echo "ERROR: Redis not running. Install Docker or run: brew install redis && brew services start redis"; \
	      exit 1; \
	    fi; \
	    sleep 1; \
	    $(MAKE) redis-ping; \
	  }

redis-down: ## Stop the local Redis container or redis-server pid.
	@docker rm -f $(REDIS_CONTAINER) 2>/dev/null && echo "docker redis stopped" || true
	@if [ -f $(PID_DIR)/redis.pid ]; then \
	  kill $$(cat $(PID_DIR)/redis.pid) 2>/dev/null && echo "redis-server stopped" || true; \
	  rm -f $(PID_DIR)/redis.pid; \
	fi

quickstart: mysql-up redis-up db-use-mysql db-init ## One-shot: launch mysql + redis, flip .env, create tables. Now run `make dev`.
	@echo
	@echo "Quickstart complete. Next: make dev"

redis-ping: ## Ping configured Redis.
	$(PYTHON) -c "import sys; sys.path.insert(0,'.'); from app.core.redis_client import ping_redis; ping_redis(); print('redis ok')"

health: ## Hit /api/v1/health on the running API.
	@curl -fsS http://$(HOST):$(PORT)/api/v1/health | $(PYTHON) -m json.tool

connections: ## Probe all configured services (live).
	@curl -fsS "http://$(HOST):$(PORT)/api/v1/health/connections?probe_live=true" | $(PYTHON) -m json.tool

smoke: ## Import-test main + compile LangGraph.
	@$(PYTHON) -c "import sys; sys.path.insert(0,'.'); import main; from app.langgraph.graph import get_compiled_graph; get_compiled_graph(); print('smoke OK · routes=', len(main.app.routes))"

# ─────────────────────────── docker ──────────────────────────────────────────

DOCKER_IMAGE   ?= interviewer-ai:latest
DOCKER_PLATFORM ?= linux/amd64
COMPOSE        := docker compose

docker-build: ## Build the production image (interviewer-ai:latest, linux/amd64).
	docker build --platform $(DOCKER_PLATFORM) -t $(DOCKER_IMAGE) .

docker-rebuild: ## Rebuild image without cache.
	docker build --no-cache --platform $(DOCKER_PLATFORM) -t $(DOCKER_IMAGE) .

docker-up: env-check ## Bring up MySQL + Redis + API + worker + livekit-agent.
	$(COMPOSE) up -d --build

docker-down: ## Stop and remove containers (keeps volumes).
	$(COMPOSE) down

docker-clean: ## Stop containers AND drop volumes (full reset).
	$(COMPOSE) down -v

docker-logs: ## Tail logs for all services.
	$(COMPOSE) logs -f --tail=200

docker-ps: ## Show running services.
	$(COMPOSE) ps

docker-shell: ## Open a shell inside the api container.
	$(COMPOSE) exec api bash

docker-health: ## Hit the API health endpoint from the host.
	@curl -fsS http://localhost:$${API_PORT_HOST:-8000}/api/v1/health | $(PYTHON) -m json.tool 2>/dev/null \
	  || curl -fsS http://localhost:$${API_PORT_HOST:-8000}/api/v1/health

HOSTINGER_COMPOSE := docker compose -f docker-compose.hostinger.yml

hostinger-build-web: ## Build React app for same-origin nginx deploy.
	@bash deploy/hostinger/build-frontend.sh

hostinger-up: env-check ## Hostinger VPS: build image once, then start stack.
	$(HOSTINGER_COMPOSE) build api
	$(HOSTINGER_COMPOSE) up -d

hostinger-down: ## Stop Hostinger stack.
	$(HOSTINGER_COMPOSE) down

hostinger-logs: ## Tail Hostinger stack logs.
	$(HOSTINGER_COMPOSE) logs -f --tail=200

hostinger-ps: ## Show Hostinger stack status.
	$(HOSTINGER_COMPOSE) ps

# ─────────────────────────── tooling ──────────────────────────────────────────

format: ## Format with ruff.
	$(UV) run ruff format app main.py

lint: ## Lint with ruff.
	$(UV) run ruff check app main.py

parse-check: ## AST-parse every .py to catch syntax errors fast.
	@$(PYTHON) -c "import ast, glob; files = glob.glob('app/**/*.py', recursive=True) + ['main.py']; [ast.parse(open(f).read(), f) for f in files]; print('parse OK ('+str(len(files))+' files)')"

clean: ## Remove caches.
	@find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
	@rm -rf $(PID_DIR)
	@echo "cleaned"

nuke: clean ## clean + remove .venv (re-run `make install` after).
	@rm -rf .venv
	@echo ".venv removed"
