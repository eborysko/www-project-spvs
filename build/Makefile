# SPVS Build Toolchain — developer task runner
# Requires: uv, pre-commit
# Usage: make <target>

.DEFAULT_GOAL := help
.PHONY: help install sync lock lint lint-fix format format-check type-check check \
        test test-fast test-file pre-commit pre-commit-install pre-commit-update \
        pre-commit-all validate-baseline build-baseline check-baseline \
        migrate-baseline yamllint security clean

# Bypass any user-level uv config (e.g., private PyPI proxies) so the
# committed uv.lock and pyproject.toml are the only inputs to dependency
# resolution. Ensures reproducibility for external contributors and CI.
export UV_NO_CONFIG := 1

PYTHON  := uv run python
PYTEST  := uv run pytest
RUFF    := uv run ruff
MYPY    := uv run mypy
SPVS    := uv run python -m spvs_build

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' \
		| sort

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------
install: ## Bootstrap: install deps from lockfile + install pre-commit hooks
	uv sync --dev --frozen
	$(MAKE) pre-commit-install

sync: ## Install deps from lockfile (no re-resolution; lockfile is authoritative)
	uv sync --dev --frozen

lock: ## (Maintenance) Regenerate uv.lock by re-resolving dependencies
	uv lock
	uv sync --dev

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------
lint: ## Run ruff linter (no autofix)
	$(RUFF) check spvs_build/

lint-fix: ## Run ruff linter with autofix
	$(RUFF) check --fix spvs_build/

format: ## Run ruff formatter
	$(RUFF) format spvs_build/

format-check: ## Check formatting without writing
	$(RUFF) format --check spvs_build/

type-check: ## Run mypy strict type checking
	$(MYPY) spvs_build/

check: lint format-check type-check ## All read-only checks (lint + format-check + type-check)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test: ## Full test suite with coverage
	$(PYTEST)

test-fast: ## Tests without coverage (faster feedback)
	$(PYTEST) --no-cov -q

test-file: ## Run a specific test file: make test-file FILE=spvs_build/tests/test_foo.py
	$(PYTEST) $(FILE) --no-cov -v

# ---------------------------------------------------------------------------
# pre-commit
# ---------------------------------------------------------------------------
pre-commit-install: ## Install pre-commit hooks into .git
	cd .. && uv run --directory build pre-commit install --hook-type pre-commit
	cd .. && uv run --directory build pre-commit install --hook-type commit-msg

pre-commit: ## Run pre-commit hooks against staged files
	cd .. && uv run --directory build pre-commit run

pre-commit-all: ## Run pre-commit hooks against every file
	cd .. && uv run --directory build pre-commit run --all-files

pre-commit-update: ## Update pre-commit hook revisions to latest
	cd .. && uv run --directory build pre-commit autoupdate

# ---------------------------------------------------------------------------
# SPVS-specific build pipeline
# ---------------------------------------------------------------------------
validate-baseline: ## Validate baseline supplement YAML against schema + semantic rules
	$(SPVS) validate \
		--supplement ../controls/baseline \
		--schema ../schema/control.schema.json

build-baseline: ## Regenerate baseline 1.0 CSV from YAML
	$(SPVS) build \
		--supplement ../controls/baseline \
		--schema ../schema/control.schema.json \
		--renderer csv-baseline \
		--out ../1.5/OWASP_SPVS_1.0_-en_Requirements.csv

check-baseline: ## Drift check: regenerate baseline CSV and compare to committed
	$(SPVS) check \
		--supplement ../controls/baseline \
		--schema ../schema/control.schema.json \
		--renderer csv-baseline \
		--out ../1.5/OWASP_SPVS_1.0_-en_Requirements.csv

migrate-baseline: ## One-shot CSV→YAML migration of the baseline supplement
	$(SPVS) migrate \
		--csv ../1.5/OWASP_SPVS_1.0_-en_Requirements.csv \
		--out ../controls/baseline

yamllint: ## yamllint controls/ tree
	uv run yamllint -c ../.yamllint.yaml ../controls

security: ## Security scan: ruff bandit rules + secret scan via pre-commit gitleaks hook
	$(RUFF) check --select S spvs_build/
	cd .. && uv run --directory build pre-commit run gitleaks --all-files

# ---------------------------------------------------------------------------
# Distribution
# ---------------------------------------------------------------------------
build: ## Build wheel + sdist via uv
	uv build

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean: ## Remove caches, coverage, build artefacts
	rm -rf dist/ .mypy_cache/ .ruff_cache/ .pytest_cache/ htmlcov/
	rm -f .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
