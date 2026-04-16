SHELL := /bin/zsh

.PHONY: help setup setup-venv run traffic

help:
	@echo "Available targets:"
	@echo "  make setup        # install dependencies with uv"
	@echo "  make setup-venv   # install dependencies with python venv + pip"
	@echo "  make run          # run the demo service with env loaded from .env"
	@echo "  make traffic      # run the standalone traffic generator with env loaded from .env"

setup:
	uv sync

setup-venv:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e .

run:
	set -a; source .env; set +a; \
	if [ -x .venv/bin/demo-store ]; then .venv/bin/demo-store; else uv run demo-store; fi

traffic:
	set -a; source .env; set +a; \
	if [ -x .venv/bin/demo-traffic ]; then .venv/bin/demo-traffic; else uv run demo-traffic; fi
