# SEND-IT Backend

FastAPI backend for the SEND-IT courier aggregation platform.

## Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload
```

## API Documentation

Interactive docs: http://localhost:8000/docs

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

```bash
pytest
pytest --cov=app tests/
```

## Project Structure

- `app/main.py` — FastAPI application
- `app/routers/` — API endpoints
- `app/services/` — Business logic
- `app/models/` — SQLAlchemy models
- `app/schemas/` — Pydantic schemas
- `app/integrations/` — External APIs (couriers, payments)
- `alembic/` — Database migrations
- `tests/` — Automated tests
