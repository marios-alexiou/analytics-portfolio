.DEFAULT_GOAL := help
VENV := .venv
BIN := $(VENV)/bin
DBT := cd transform && DBT_PROFILES_DIR=. ../$(BIN)/dbt

help:  ## List targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup:  ## Create the virtualenv and install Python and dbt dependencies
	python3.12 -m venv $(VENV)
	$(BIN)/pip install -q -r requirements.txt
	$(DBT) deps

data:  ## Generate raw source files and load them into DuckDB
	$(BIN)/python -m generator
	$(BIN)/python -m scripts.load_duckdb

build:  ## dbt build (seeds, models, tests) on DuckDB
	$(DBT) build

lint:  ## ruff + sqlfluff
	$(BIN)/ruff check generator scripts tests
	DUCKDB_PATH=data/fieldcraft.duckdb $(BIN)/sqlfluff lint transform/models

test:  ## Generator unit tests
	$(BIN)/pytest -q

all: data build lint test  ## Everything CI runs

dashboard-setup:  ## Install the pinned open-source Evidence dependencies
	cd dashboards && npm ci

dashboard-build:  ## Extract existing DuckDB marts and build the dashboard site
	cd dashboards && npm run sources && npm run build

dashboard-preview:  ## Serve the built dashboards at http://127.0.0.1:3001
	cd dashboards && npm run preview

.PHONY: help setup data build lint test all dashboard-setup dashboard-build dashboard-preview
