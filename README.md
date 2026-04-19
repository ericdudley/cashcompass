# CashCompass

CashCompass is a personal finance tracker built on the Python/FastHTML app in `src/`.

The legacy Go app in `server/` is still kept in the repo as a behavioral reference during the migration, but the Python app is now the primary development and deployment target.

## Primary Stack

- **Backend**: Python, FastHTML, SQLite
- **Frontend**: HTMX, Tailwind, FastHTML components
- **Tests**: Playwright E2E against the Python app

## Development

Run the primary Python app:

```bash
make dev
```

Equivalent direct command:

```bash
CASHCOMPASS_DEV=true .venv/bin/python -m uvicorn src.main:app --port 8080 --reload
```

The app runs at `http://localhost:8080`.

## Testing

Run the primary Python Playwright suite:

```bash
make test
```

Useful targets:

```bash
make test-e2e-py
make test-e2e-ui-py
make dev-go
make test-go
make test-e2e-go
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CASHCOMPASS_DB_PATH` | `./src/data/cashcompass.db` | SQLite database path for the Python app |
| `CASHCOMPASS_MIGRATIONS_PATH` | `./src/migrations` | SQL migrations path |
| `CASHCOMPASS_PORT` | `8080` | HTTP listen port |
| `CASHCOMPASS_DEV` | unset | Enables dev-only routes such as `/dev/reset` when `true` |

## Docker

Build and run the Python app with Docker Compose:

```bash
docker compose up --build
```

Or build the image directly:

```bash
docker build -t ghcr.io/ericdudley/cashcompass:latest .
docker run --rm -p 8080:8080 -v cashcompass-data:/data ghcr.io/ericdudley/cashcompass:latest
```

The published image preserves the existing runtime contract:

- port `8080`
- database at `/data/cashcompass.db`
- persistent `/data` volume

## Legacy Go Reference

The Go server remains available for comparison while the migration settles:

- `server/` contains the legacy implementation
- `make dev-go` runs the Go app
- `make test-go` and `make test-e2e-go` exercise legacy coverage
