# OpsCopilot

OpsCopilot is an operations management API built with FastAPI. It manages incidents and operational documents, persists data in PostgreSQL, exposes Prometheus-compatible metrics, and uses a layered architecture that separates HTTP handling, validation, application logic, and database access.

The current release provides the service foundation for future LLM-assisted incident investigation and retrieval-augmented generation (RAG). LLM integration, embeddings, and vector search are not part of the current release.

## Current functionality

- Health and root endpoints
- Incident creation, listing, filtering, pagination, retrieval, partial update, and deletion
- Document creation, listing, filtering, pagination, retrieval, and deletion
- PostgreSQL persistence through SQLAlchemy
- Database schema migrations through Alembic
- Pydantic request validation and response serialization
- Clean HTTP error responses and application logging
- Prometheus-compatible request count and request-duration metrics
- Automated API tests with pytest and an isolated in-memory SQLite database

## Project structure

```text
app/
├── api/          # HTTP routes and HTTP-specific behavior
├── database/     # SQLAlchemy connection and database models
├── schemas/      # Pydantic request and response models
├── services/     # Database operations and application logic
├── main.py       # Creates and configures the FastAPI application
└── metrics.py    # Prometheus metric definitions

alembic/          # Database migrations
tests/            # Automated tests
compose.yaml      # API, migration, and PostgreSQL services
Dockerfile        # Application container image
```

## Requirements

Choose either the Docker Compose workflow or the local-development workflow below.

For the Docker Compose workflow:

- Docker Desktop, or Docker Engine with Docker Compose

For local Python development:

- Python 3.14
- Docker, used to run PostgreSQL locally
- `pip`, included with a normal Python installation

The commands below assume you are in the repository root—the directory containing `compose.yaml` and `requirements.txt`.

## Option 1: Run the complete stack with Docker Compose

This is the shortest way to start the project:

```bash
docker compose up --build
```

Compose will:

1. Start PostgreSQL.
2. Wait for PostgreSQL to become healthy.
3. Run all Alembic migrations.
4. Start the FastAPI application on port `8000`.

Open:

- API root: <http://localhost:8000/>
- Health check: <http://localhost:8000/health>
- Interactive API documentation: <http://localhost:8000/docs>
- Metrics: <http://localhost:8000/metrics>

Stop the stack with:

```bash
docker compose down
```

PostgreSQL data is stored in the `postgres_data` Docker volume and survives a normal `docker compose down`.

To also delete all local database data, use:

```bash
docker compose down -v
```

Warning: the `-v` option permanently removes the Compose database volume. The next startup creates an empty database and reruns the migrations.

## Option 2: Run Python locally and PostgreSQL in Docker

This workflow is convenient when changing Python code because Uvicorn can automatically reload the application.

### 1. Create a virtual environment

On macOS or Linux:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
```

When activated, the terminal prompt normally begins with `(.venv)`.

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Using `python -m pip` ensures that packages are installed for the active Python interpreter.

### 3. Start PostgreSQL

Start only the database service:

```bash
docker compose up -d db
```

Check its status:

```bash
docker compose ps
```

The database should eventually report `healthy`.

### 4. Configure the database URL

On macOS or Linux:

```bash
export DATABASE_URL='postgresql+psycopg://opscopilot:localdev@localhost:5432/opscopilot'
export LOG_LEVEL='INFO'
```

On Windows PowerShell:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://opscopilot:localdev@localhost:5432/opscopilot'
$env:LOG_LEVEL = 'INFO'
```

The hostname is `localhost` here because Python runs on the host machine. Inside Compose, the API uses the Compose service hostname `db` instead.

### 5. Apply database migrations

```bash
python -m alembic upgrade head
```

Migrations create and update the database tables. Run this after starting a fresh database and whenever new migrations are added.

### 6. Start FastAPI

```bash
python -m uvicorn app.main:app --reload
```

The command means:

- `app.main`: import the `app/main.py` module.
- `app`: use the FastAPI object named `app` from that module.
- `--reload`: restart the development server after Python files change.

The application is available at <http://localhost:8000>.

## Run tests

With the virtual environment active, run:

```bash
python -m pytest -v
```

Run one test file:

```bash
python -m pytest tests/test_incidents.py -v
```

The tests override the application's database dependency and use an isolated in-memory SQLite database. They do not require the Compose PostgreSQL service to be running.

## API endpoints

FastAPI provides interactive documentation at <http://localhost:8000/docs>. The main endpoints are summarized below.

### Operational endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Basic application response |
| `GET` | `/health` | Returns `{"status": "ok"}` when the API is running |
| `GET` | `/metrics` | Prometheus-compatible application and process metrics |

`/metrics` returns text rather than JSON. It includes `http_requests_total` and `http_request_duration_seconds` measurements.

### Incident endpoints

| Method | Path | Success status | Description |
|---|---|---:|---|
| `POST` | `/incidents` | `201` | Create an incident |
| `GET` | `/incidents` | `200` | List incidents |
| `GET` | `/incidents/{incident_id}` | `200` | Retrieve one incident |
| `PATCH` | `/incidents/{incident_id}` | `200` | Partially update an incident |
| `DELETE` | `/incidents/{incident_id}` | `204` | Delete an incident |

Create an incident:

```bash
curl -X POST http://localhost:8000/incidents \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Checkout failure",
    "description": "Checkout is returning HTTP 503",
    "service": "checkout",
    "severity": "critical"
  }'
```

Valid incident severities are:

- `low`
- `medium`
- `high`
- `critical`

Partially update an incident:

```bash
curl -X PATCH http://localhost:8000/incidents/1 \
  -H 'Content-Type: application/json' \
  -d '{"status": "resolved"}'
```

List incidents supports these optional query parameters:

| Parameter | Meaning | Validation/default |
|---|---|---|
| `service` | Exact service name | 2–100 characters |
| `severity` | Exact severity | One of the four values above |
| `status` | Exact incident status | At least 1 character |
| `limit` | Maximum number returned | Default `20`; from `1` through `100` |
| `offset` | Number of records to skip | Default `0`; cannot be negative |

Example:

```bash
curl 'http://localhost:8000/incidents?service=checkout&severity=critical&limit=20&offset=0'
```

### Document endpoints

| Method | Path | Success status | Description |
|---|---|---:|---|
| `POST` | `/documents` | `201` | Create a document |
| `GET` | `/documents` | `200` | List documents |
| `GET` | `/documents/{document_id}` | `200` | Retrieve one document |
| `DELETE` | `/documents/{document_id}` | `204` | Delete a document |

Create a document:

```bash
curl -X POST http://localhost:8000/documents \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Checkout Runbook",
    "document_type": "runbook",
    "content": "When checkout returns 503, check the upstream service."
  }'
```

List documents supports these optional query parameters:

| Parameter | Meaning | Validation/default |
|---|---|---|
| `title` | Exact document title | 1–200 characters |
| `document_type` | Exact document type | 1–50 characters |
| `limit` | Maximum number returned | Default `20`; from `1` through `100` |
| `offset` | Number of records to skip | Default `0`; cannot be negative |

Example:

```bash
curl 'http://localhost:8000/documents?document_type=runbook&limit=20&offset=0'
```

## Common HTTP responses

- `200 OK`: successful read or update
- `201 Created`: resource created
- `204 No Content`: resource deleted; the response body is empty
- `404 Not Found`: requested incident or document does not exist
- `422 Unprocessable Content`: FastAPI/Pydantic rejected invalid input
- `503 Service Unavailable`: the database is temporarily unavailable

## Current limitations

- Authentication and authorization are not implemented.
- Documents cannot currently be updated through the API.
- Metrics are kept in process memory; multi-process deployment requires additional Prometheus client configuration.
- PostgreSQL credentials in `compose.yaml` are local-development credentials and must not be reused in production.
- LLM and RAG functionality have not been implemented yet.