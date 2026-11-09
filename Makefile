.PHONY: help setup test lint format validate clean

PYTHON ?= python

help:
	@echo "Targets:"
	@echo "  setup     Create/refresh the conda env and install the package"
	@echo "  test      Run the fast test suite"
	@echo "  lint      Run ruff check"
	@echo "  format    Run ruff format"
	@echo "  validate  Parse and validate all TOML configs"
	@echo "  clean     Remove caches and build artifacts (keeps data and runs)"

setup:
	conda env create -f environment.yml || conda env update -f environment.yml --prune
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

validate:
	$(PYTHON) -m rag_energy.cli validate

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '.pytest_cache', '.ruff_cache', '.mypy_cache', 'htmlcov']]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink(missing_ok=True) for p in pathlib.Path('.').rglob('*.egg-info')]"
