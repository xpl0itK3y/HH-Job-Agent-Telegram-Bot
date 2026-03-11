# HH Job Agent Telegram Bot

Telegram bot for resume-driven vacancy search and delivery, with:
- FastAPI API
- PostgreSQL
- Redis
- Celery worker
- Streamlit admin panel

## Requirements

- Docker
- Docker Compose

## Environment

Create `.env` from `.env.example` and fill the required values:

```bash
cp .env.example .env
```

Required fields:
- `TELEGRAM_BOT_TOKEN`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `STREAMLIT_ADMIN_PASSWORD_HASH`
- `STREAMLIT_SECRET_KEY`

## Run with Docker Compose

Build images:

```bash
docker compose build app worker streamlit-admin
```

Start infrastructure:

```bash
docker compose up -d postgres redis
```

Apply migrations:

```bash
docker compose run --rm app alembic upgrade head
```

Start application services:

```bash
docker compose up -d app worker streamlit-admin
```

## Service URLs

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Ready: `http://localhost:8000/ready`
- Admin panel: `http://localhost:8501`
- PostgreSQL from host: `localhost:5433`
- Redis from host: `localhost:6379`

## Useful Commands

Show service status:

```bash
docker compose ps
```

Show logs:

```bash
docker compose logs --tail=100 app worker streamlit-admin
```

Stop and remove containers and volumes:

```bash
docker compose down -v
```
 
