.PHONY: dev up down logs migrate prod

dev:
	docker compose -f docker-compose.base.yml -f docker-compose.yml up -d && cd frontend && pnpm run dev

up:
	docker compose -f docker-compose.base.yml -f docker-compose.yml up -d

down:
	docker compose -f docker-compose.base.yml -f docker-compose.yml down

logs:
	docker compose -f docker-compose.base.yml -f docker-compose.yml logs -f

migrate:
	docker compose -f docker-compose.base.yml -f docker-compose.yml exec api poetry run alembic upgrade head

prod:
	cd frontend && pnpm run build
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml up -d --build