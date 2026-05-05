# SEND-IT Backend Makefile
# Convenient commands for development

.PHONY: help venv install dev test lint format clean migrate seed

help:
	@echo "SEND-IT Backend - Available Commands"
	@echo "====================================="
	@echo "make venv      - Create virtual environment"
	@echo "make install   - Install dependencies"
	@echo "make dev       - Run development server"
	@echo "make test      - Run tests"
	@echo "make lint      - Run linters"
	@echo "make format    - Auto-format code"
	@echo "make migrate   - Run database migrations"
	@echo "make seed      - Seed database with test data"
	@echo "make clean     - Remove cache and temp files"

venv:
	@echo "Creating virtual environment..."
	@bash setup_venv.sh

install:
	@echo "Installing dependencies..."
	@. .venv/bin/activate && pip install -r requirements.txt

dev:
	@echo "Starting development server..."
	@. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "Running tests..."
	@. .venv/bin/activate && pytest

lint:
	@echo "Running linters..."
	@. .venv/bin/activate && ruff check . && black --check . && mypy app/

format:
	@echo "Formatting code..."
	@. .venv/bin/activate && ruff check --fix . && black .

migrate:
	@echo "Running migrations..."
	@. .venv/bin/activate && alembic upgrade head

seed:
	@echo "Seeding database..."
	@. .venv/bin/activate && python scripts/seed_data.py

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"
