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

## Run the application

Install and start Docker Desktop (or Docker Engine with Compose). No local Python
or uv installation is needed to run the application. From the repository root:

| Flavor | Command | Behavior |
|---|---|---|
| Development | `./scripts/run dev` | Full Docker stack; Python changes in `app/` reload automatically |
| Production | `./scripts/run prod` | Same Docker stack; code baked into the image, no reload |

Both commands build the image using locked dependencies, start PostgreSQL, wait
for its health check, apply migrations, and then start the API. Migration failure
prevents API startup. Services are recreated on each launch so migrations run
again; existing database data stays in the named `postgres_data` volume.

Open <http://localhost:8000/docs> to try the API. The root, health check, and metrics
are available at `/`, `/health`, and `/metrics` respectively.

Logs stay attached to your terminal. Press Ctrl+C to stop the stack. To switch
flavors, stop the current run and launch the other command. Both flavors use the
same database volume and ports; they are not isolated deployment environments.
Restart the launcher after changing dependencies, migrations, or Docker settings.
Only application source changes reload automatically in dev.

The production flavor runs a non-root container with one Uvicorn worker and a
25-second graceful shutdown window (Compose allows 30 seconds). One worker keeps
the current in-process Prometheus metrics consistent. Proxy headers are disabled.
This selects production runtime behavior; deploying publicly still requires
replacing local database credentials, restricting database access, and configuring
TLS, authentication, and backups. Authentication is not implemented in the API.

`compose.yaml` defines the shared stack and production defaults;
`compose.dev.yaml` adds the read-only source mount and reload command. The launcher
selects these files for you. There is no separate local-Python startup path or
manual migration step.

Validate the launcher without starting services:

```bash
bash -n scripts/run
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

## Run tests

Run the complete test suite:

```bash
uv run python -m pytest -v
```

Run one test file:

```bash
uv run python -m pytest tests/test_incidents.py -v
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

Valid incident statuses are `triggered`, `acknowledged`, and `resolved` (case-sensitive).
New incidents start as `triggered`. Status updates accept any of these values;
transition ordering is not enforced.

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
| `status` | Exact incident status | `triggered`, `acknowledged`, or `resolved` |
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
