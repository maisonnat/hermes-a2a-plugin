.PHONY: install dev install-docs docs serve-docs test lint ai-docs clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-docs:
	pip install -e ".[docs]"

docs:
	mkdocs build --strict

serve-docs:
	mkdocs serve --strict

ai-docs:
	python3 scripts/generate_ai_docs.py

test:
	python -m pytest tests/ -v

lint:
	ruff check hermes_a2a_plugin/

clean:
	rm -rf build/ dist/ *.egg-info site/
	find . -type d -name __pycache__ -exec rm -rf {} +
