COMPOSE := docker compose
ENV_FILE := auth_service/.env.auth

API_URL ?= http://localhost:8000

RUFF_PATHS := auth_service/src auth_service/*.py
MYPY_PATHS := \
	auth_service/src/core \
	auth_service/src/db \
	auth_service/src/utils/jwt.py \
	auth_service/src/utils/security.py

TEST_COMPOSE_FILE := auth_service/tests/docker-compose.test.auth.yml
TEST_COMPOSE := docker compose -f $(TEST_COMPOSE_FILE)

.PHONY: help init-env up down ps logs logs-auth health ready migrate seed-roles create-superuser bootstrap
.PHONY: test test-up test-run test-cov test-logs test-down
.PHONY: fmt fmt-check lint typecheck quality check demo demo-clean

help:
	@echo "Targets:"
	@echo "  make up        - start standalone auth stack"
	@echo "  make down      - stop stack"
	@echo "  make ps        - show containers"
	@echo "  make logs      - follow logs"
	@echo "  make logs-auth - auth service logs"
	@echo "  make health    - check API is up"
	@echo "  make ready     - check dependencies are ready (DB + Redis)"
	@echo "  make init-env  - create auth_service/.env.auth from sample"
	@echo "  make create-superuser SUPERUSER_PASSWORD=StrongPass123!"
	@echo "  make test      - run integration tests via docker compose"
	@echo "  make test-cov  - run integration tests with coverage (docker compose)"
	@echo "  make quality   - run ruff fmt-check + lint + mypy"
	@echo "  make demo      - run the full demo in ~2 minutes"
	@echo "  make demo-clean - stop stack and remove .demo artifacts"

init-env:
	@test -f $(ENV_FILE) || cp auth_service/.env.auth.sample $(ENV_FILE)
	@echo "OK: $(ENV_FILE)"

up: init-env
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down -v --remove-orphans

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=200

logs-auth:
	$(COMPOSE) logs -f --tail=200 auth_service

logs-postgres-auth:
	$(COMPOSE) logs -f --tail=200 postgres_auth

logs-redis:
	$(COMPOSE) logs -f --tail=200 redis

health:
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -fsS "$(API_URL)/api/v1/healthz" | grep -q '"status":"ok"'; then \
			echo "OK: healthz"; exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "FAIL: API did not become healthy (healthz)"; exit 1

ready:
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		code=$$(curl -sS -o /dev/null -w "%{http_code}" "$(API_URL)/api/v1/readyz"); \
		if [ "$$code" = "200" ]; then \
			echo "OK: readyz"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "FAIL: service is not ready (readyz)"; \
	curl -sS -i "$(API_URL)/api/v1/readyz" || true; \
	exit 1

migrate:
	$(COMPOSE) exec auth_service alembic upgrade head

seed-roles:
	$(COMPOSE) exec auth_service python seed_roles.py

create-superuser:
	$(COMPOSE) exec -e SUPERUSER_PASSWORD="$(SUPERUSER_PASSWORD)" auth_service python create_superuser.py

bootstrap: up migrate seed-roles health

# --- Tests ---

test: test-up test-run test-down

COV_FAIL_UNDER ?= 75

test-cov:
	$(TEST_COMPOSE) run --rm --no-deps tests bash -lc '\
		alembic -c alembic_test.ini upgrade head \
		&& SUPERUSER_PASSWORD=123 python create_superuser.py \
		&& pytest -q --cov=src --cov-config=/app/.coveragerc --cov-report=term-missing \
			--cov-report=xml:/artifacts/coverage.xml --cov-fail-under=$(COV_FAIL_UNDER) \
	'

test-up:
	mkdir -p auth_service/tests/.artifacts
	$(TEST_COMPOSE) up -d --build  test_postgres test_redis jaeger

test-run:
	$(TEST_COMPOSE) run --rm --no-deps tests bash -lc '\
		alembic -c alembic_test.ini upgrade head \
		&& SUPERUSER_PASSWORD=123 python create_superuser.py \
		&& pytest -q \
	'

test-logs:
	$(TEST_COMPOSE) logs -f --tail=200 tests

test-down:
	$(TEST_COMPOSE) down -v --remove-orphans

# --- Quality ---

fmt:
	ruff format .

fmt-check:
	ruff format --check .

lint:
	ruff check $(RUFF_PATHS)

lint-fix:
	ruff check $(RUFF_PATHS) --fix

typecheck:
	MYPYPATH=auth_service/src mypy $(MYPY_PATHS)

quality: fmt-check lint typecheck
check: quality

demo:
	bash scripts/demo.sh

demo-clean:
	bash scripts/demo_clean.sh
