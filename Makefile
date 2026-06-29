# Developer convenience targets. Use inside the container or a POSIX shell.
.DEFAULT_GOAL := help
COMPOSE := docker compose

.PHONY: help build up down logs shell migrate makemigrations superuser test lint format check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

build: ## Build images
	$(COMPOSE) build

up: ## Start the stack
	$(COMPOSE) up -d

down: ## Stop the stack
	$(COMPOSE) down

logs: ## Tail web logs
	$(COMPOSE) logs -f web

shell: ## Open a shell in the web container
	$(COMPOSE) exec web bash

migrate: ## Apply database migrations
	$(COMPOSE) exec web python manage.py migrate

makemigrations: ## Generate migrations
	$(COMPOSE) exec web python manage.py makemigrations

superuser: ## Create a superuser
	$(COMPOSE) exec web python manage.py createsuperuser

test: ## Run the test suite
	$(COMPOSE) exec web pytest

lint: ## Run ruff + mypy
	$(COMPOSE) exec web ruff check .
	$(COMPOSE) exec web mypy .

format: ## Auto-format with ruff
	$(COMPOSE) exec web ruff format .
	$(COMPOSE) exec web ruff check --fix .

check: ## Django system checks
	$(COMPOSE) exec web python manage.py check
