.PHONY: setup install dev clean test format

# Default virtual environment path
VENV_PATH ?= .venv

setup:
	python -m uv venv $(VENV_PATH)

install:
	python -m uv pip install -r requirements.txt

dev:
	python -m uv pip install -r requirements-dev.txt

clean:
	rm -rf $(VENV_PATH)
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	python -m pytest tests/

format:
	python -m black synda/ tests/

# Install in development mode
develop:
	python -m uv pip install -e .

# Build the package
build:
	python -m uv pip install build
	python -m build

# Install the package
install-package:
	python -m uv pip install .