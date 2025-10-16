# Makefile for FastAPI Job Portal

# Environment variables
PYTHON := python3
APP_MODULE := app.main:app
MIGRATE_SCRIPT := migrate.py
UVICORN := uvicorn

# Load .env variables automatically (optional)
include .env
export $(shell sed 's/=.*//' .env)

# Default target
.DEFAULT_GOAL := help

# Help command
help:
	@echo "Available commands:"
	@echo "  make run         - Run FastAPI app with uvicorn"
	@echo "  make migrate     - Apply database migrations"
	@echo "  make clean       - Remove Python cache files"
	@echo "  make install     - Install project dependencies"
	@echo "  make envcheck    - Show important environment variables"

#  Run FastAPI app
run:
	$(UVICORN) $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

# 🗄️ Run migrations
migrate:
	$(PYTHON) $(MIGRATE_SCRIPT)

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Install all dependencies
install:
	pip install -r requirements.txt

# Check if env vars are loaded
envcheck:
	@echo "Database Host: $(DB_HOST)"
	@echo "Database Name: $(DB_NAME)"
	@echo "Database User: $(DB_USER)"
