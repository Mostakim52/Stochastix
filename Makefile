.PHONY: help setup lint format type test coverage pipeline pipeline-live serve dashboard docker-build docker-up clean

help:
	@echo "StockForge developer tasks"
	@echo "  setup          create venv and install everything"
	@echo "  lint           ruff checks"
	@echo "  format         ruff autofix + format"
	@echo "  type           mypy"
	@echo "  test           pytest suite"
	@echo "  coverage       pytest with coverage report"
	@echo "  pipeline       offline end-to-end demo (synthetic data)"
	@echo "  pipeline-live  full run on real market data"
	@echo "  serve          run the FastAPI server"
	@echo "  dashboard      run the Streamlit dashboard"
	@echo "  docker-build   build API image"
	@echo "  docker-up      compose up api+dashboard"
	@echo "  clean          remove caches and artifacts"

setup:
	python -m venv .venv
	.venv/Scripts/python -m pip install --upgrade pip
	.venv/Scripts/python -m pip install -e ".[dev,dashboard]"

lint:
	ruff check src tests

format:
	ruff check src tests --fix
	ruff format src tests

type:
	mypy src/stockforge --ignore-missing-imports

test:
	pytest -q

coverage:
	pytest --cov --cov-report=term-missing -q

pipeline:
	stockforge pipeline --synthetic

pipeline-live:
	stockforge pipeline --no-synthetic

serve:
	stockforge serve --host 127.0.0.1 --port 8000

dashboard:
	stockforge dashboard

docker-build:
	docker build -f docker/Dockerfile -t stockforge/api:latest .

docker-up:
	docker compose -f docker/docker-compose.yml up --build

clean:
	python -c "import shutil,pathlib; [shutil.rmtree(p, ignore_errors=True) for p in map(pathlib.Path, ['artifacts','data/cache','.pytest_cache','.mypy_cache','.ruff_cache','htmlcov','dist','build'])]"
