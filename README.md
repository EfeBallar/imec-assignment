# Social Grouping Backend (FastAPI + PostgreSQL)

Backend service for user registration, attribute management, and delayed/batch user grouping based on shared attributes.

## Tech stack

- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- APScheduler (periodic non-real-time grouping)
- Docker + Docker Compose

## How grouping works

The grouping worker runs periodically (every `GROUPING_INTERVAL_SECONDS`).

For each ungrouped user:

1. Compute overlap score against every existing group.
2. Group score = maximum number of shared attributes with any member in that group.
3. If best score >= `MIN_MATCH`, assign user to that group.
4. If no group qualifies, create a new group containing only that user.

`MIN_MATCH` is configurable via environment variables.

When a user updates attributes, their old membership is removed so they can be reassigned in the next batch run.

## Run locally with Docker

1. Ensure Docker is running.
2. From project root:

```bash
docker compose up --build
```

API will be available at:

- `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

## Environment variables

See `.env.example`:

- `DATABASE_URL`: SQLAlchemy connection string
- `MIN_MATCH`: required number of shared attributes for a match
- `GROUPING_INTERVAL_SECONDS`: scheduler interval for batch grouping

## REST API

- `POST /api/users` - Create user
- `GET /api/users` - List users
- `GET /api/users/{user_id}` - Retrieve user info
- `PUT /api/users/{user_id}/attributes` - Set user attributes
- `GET /api/users/{user_id}/attributes` - Retrieve user attributes
- `GET /api/users/{user_id}/group` - Retrieve user's group and members
- `POST /api/grouping/run` - Manually trigger grouping cycle (`?min_match=...` optional)
- `GET /health` - Health endpoint

## Tests

Test coverage includes:

- route tests for all endpoints
- database/model constraint tests
- service/grouping logic tests

Run tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Database schema

- ORM models in `app/models.py`
- SQL DDL in `schema.sql`

## Local development without Docker

1. Start PostgreSQL and create DB `social_grouping`.
2. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure `.env` with local DB URL (example):

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/social_grouping
MIN_MATCH=2
GROUPING_INTERVAL_SECONDS=30
```

4. Run app:

```bash
uvicorn app.main:app --reload
```
