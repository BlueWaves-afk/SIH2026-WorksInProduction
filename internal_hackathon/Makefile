.PHONY: install install-python test test-python lint fmt db-up db-down

PYTHON ?= python3
PYTHON_PACKAGES := \
	libs/adapters \
	libs/identity-consent \
	services/platform-core \
	services/scoring-engine \
	services/case-workflow \
	services/notification \
	services/ai-copilot \
	services/outreach

install:
	$(MAKE) install-python
	npm install

install-python:
	@set -e; for package in $(PYTHON_PACKAGES); do $(PYTHON) -m pip install -e "$$package[dev]"; done

test:
	$(MAKE) test-python
	npm run test

test-python:
	$(PYTHON) -m pytest services libs -q

lint:
	$(PYTHON) -m ruff check services libs
	npm run lint

fmt:
	$(PYTHON) -m ruff format services libs

db-up:
	docker compose -f infra/docker/docker-compose.yml up -d

db-down:
	docker compose -f infra/docker/docker-compose.yml down
