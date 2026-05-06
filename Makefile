.PHONY: install dev install-docs docs serve-docs test lint clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-docs:
	pip install -e ".[docs]"

docs:
	mkdocs build

serve-docs:
	mkdocs serve

test:
	python -m pytest tests/ -v

lint:
	ruff check hermes_a2a_plugin/

clean:
	rm -rf build/ dist/ *.egg-info site/
	find . -type d -name __pycache__ -exec rm -rf {} +
