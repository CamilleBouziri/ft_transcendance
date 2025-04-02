DOCKER_COMPOSE = docker compose
PROJECT_NAME = ft_transcendence

up:
	- $(DOCKER_COMPOSE) up --build -d
	sleep 10
	$(DOCKER_COMPOSE) exec backend python manage.py makemigrations
	$(DOCKER_COMPOSE) exec backend python manage.py migrate

down:
	$(DOCKER_COMPOSE) down

clean:
	$(DOCKER_COMPOSE) down --volumes
	docker system prune -f
	docker volume rm $(PROJECT_NAME)_db_data || true
	rm -rf backend/media/avatars/*

logs:
	$(DOCKER_COMPOSE) logs -f

migrate:
	$(DOCKER_COMPOSE) exec backend python manage.py migrate

createsuperuser:
	$(DOCKER_COMPOSE) exec backend python manage.py createsuperuser


migration:
	$(DOCKER_COMPOSE) exec backend python manage.py makemigrations

stop:
	docker compose down