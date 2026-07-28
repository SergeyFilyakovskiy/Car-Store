.PHONY: test test-fast test-all lint format shell db migrate makemigrations up down restart logs build

# Переменная для docker-compose файла
COMPOSE_FILE := docker-compose.dev.yml

# Запуск быстрых тестов (с маркером fast)
test:
	docker compose -f $(COMPOSE_FILE) exec django_app pytest /app/CarStore/tests/test_api.py  -m fast -v

# Запуск всех тестов
test-all:
	docker compose -f $(COMPOSE_FILE) exec django_app pytest /app/CarStore -v

# Запуск конкретного теста (пример: make test-file file=CarStore/tests/test_api.py)
test-file:
	docker compose -f $(COMPOSE_FILE) exec django_app pytest $(file) -v

# Запуск с покрытием
test-cov:
	docker compose -f $(COMPOSE_FILE) exec django_app pytest CarStore --cov=. --cov-report=html

# Линтинг
lint:
	docker compose -f $(COMPOSE_FILE) exec django_app ruff check .

# Форматирование
format:
	docker compose -f $(COMPOSE_FILE) exec django_app ruff format .

# Вход в контейнер (bash shell)
shell:
	docker compose -f $(COMPOSE_FILE) exec django_app bash

# Django shell
django-shell:
	docker compose -f $(COMPOSE_FILE) exec django_app python manage.py shell

# Применение миграций
migrate:
	docker compose -f $(COMPOSE_FILE) exec django_app python manage.py migrate

# Создание миграций
makemigrations:
	docker compose -f $(COMPOSE_FILE) exec django_app python manage.py makemigrations

# Сборка и запуск контейнеров
up:
	docker compose -f $(COMPOSE_FILE) up -d

# Остановка контейнеров
down:
	docker compose -f $(COMPOSE_FILE) down

# Перезапуск контейнеров
restart:
	docker compose -f $(COMPOSE_FILE) restart

# Просмотр логов (пример: make logs service=django_app)
logs:
	docker compose -f $(COMPOSE_FILE) logs -f $(service)

# Пересборка контейнеров
build:
	docker compose -f $(COMPOSE_FILE) build --no-cache

# Создание суперпользователя
createsuperuser:
	docker compose -f $(COMPOSE_FILE) exec django_app python manage.py createsuperuser

# Очистка кэша pytest
clean-pytest:
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Полный сброс (удаление контейнеров, volumes и пересборка)
reset:
	docker compose -f $(COMPOSE_FILE) down -v
	docker compose -f $(COMPOSE_FILE) up -d --build

# В существующий Makefile добавьте:
logs-app:
	docker compose -f $(COMPOSE_FILE) logs -f django_app

# Помощь (список всех команд)
help:
	@echo "Available commands:"
	@echo "  make test           - Run fast tests (marked with @pytest.mark.fast)"
	@echo "  make test-all       - Run all tests"
	@echo "  make test-file file=<path> - Run specific test file"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make lint           - Run linter (ruff)"
	@echo "  make format         - Format code (ruff)"
	@echo "  make shell          - Open bash shell in django_app container"
	@echo "  make django-shell   - Open Django shell"
	@echo "  make migrate        - Apply database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make createsuperuser - Create Django superuser"
	@echo "  make up             - Start containers in detached mode"
	@echo "  make down           - Stop containers"
	@echo "  make restart        - Restart containers"
	@echo "  make logs service=<name> - View logs for specific service"
	@echo "  make build          - Rebuild containers"
	@echo "  make reset          - Full reset (down volumes + rebuild)"
	@echo "  make clean-pytest   - Clean pytest cache"
	@echo "  make help           - Show this help message"
