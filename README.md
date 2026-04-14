# Social Grouping App

This project contains:

- FastAPI backend in `app/backend`
- TypeScript React frontend in `app/frontend`
- PostgreSQL persistence
- Non-real-time grouping worker

## Project structure

- `app/backend`: Python API, models, services
- `app/frontend`: TypeScript web UI
- `tests`: backend tests (routes, DB models, services)
- `schema.sql`: SQL DDL equivalent of ORM schema

## Backend overview

### Grouping behavior

The backend periodically processes ungrouped users:

1. Compare each ungrouped user against existing groups.
2. For each group, compute best overlap score with any member.
3. If best score >= `MIN_MATCH`, assign user to that group.
4. Otherwise create a new group for the user.

Group names are derived from matched attributes:

- New single-user groups use up to `MIN_MATCH` attributes from that user.
- When a second user joins a group, the name is updated to the first `MIN_MATCH`
  shared attributes between the two users that formed the match.
- If `MIN_MATCH` is overridden via `POST /api/grouping/run?min_match=...`, names
  are recalculated with that override during regroup.

When user attributes are updated, membership is removed so the user is re-evaluated in the next batch.

### Backend REST API

- `POST /api/users`
- `GET /api/users`
- `GET /api/users/{user_id}`
- `PUT /api/users/{user_id}/attributes`
- `GET /api/users/{user_id}/attributes`
- `GET /api/users/{user_id}/group`
- `POST /api/grouping/run`
- `GET /health`

## Frontend overview

The frontend provides 3 pages:

- User creation
- Attribute management (add/remove, multi-value comma input)
- Group view (group members + each member's attributes)

All backend communication uses Fetch API with REST endpoints.

## Run locally with Docker (recommended)

From project root:

```bash
docker compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5432`

## Run locally without Docker

### 1) Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.backend.main:app --reload
```

Make sure PostgreSQL is running and `.env` has a reachable `DATABASE_URL`.

### 2) Frontend

```bash
cd app/frontend
npm install
npm run dev
```

By default frontend expects backend at `http://localhost:8000`.
You can override with:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Environment variables

See `.env.example`:

- `APP_NAME`
- `DATABASE_URL`
- `MIN_MATCH`
- `GROUPING_INTERVAL_SECONDS`
- `CORS_ORIGINS` (comma-separated allowed frontend origins)

## Database schema

- ORM models: `app/backend/models.py`
- SQL schema: `schema.sql`

## Tests

Backend tests cover routes, DB constraints, and service logic.

```bash
pip install -r requirements-dev.txt
pytest -q
```
