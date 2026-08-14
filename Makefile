.PHONY: install format lint typecheck harness test check

install:
	python -m pip install -e ".[dev]"

format:
	ruff format .

lint:
	ruff check .

typecheck:
	mypy bild

harness:
	python tools/check.py

test:
	pytest tests -q

check:
	python tools/check.py --all
