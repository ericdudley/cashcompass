# CashCompass

CashCompass is a personal finance tracker built on the Python/FastHTML app in `src/`.

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

Local environment variables can be stored in `.env`; copy `.env.example` and set `ANTHROPIC_API_KEY` there when you want AI category recommendations enabled in the transaction form.

## Testing

Run the primary Python Playwright suite:

```bash
make pw
```

Useful targets:

```bash
make dev
make pw
make pw-ui
npm run test:e2e
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CASHCOMPASS_DB_PATH` | `./src/data/cashcompass.db` | SQLite database path for the Python app |
| `CASHCOMPASS_MIGRATIONS_PATH` | `./src/migrations` | SQL migrations path |
| `CASHCOMPASS_PORT` | `8080` | HTTP listen port |
| `CASHCOMPASS_DEV` | unset | Enables dev-only routes such as `/dev/reset` when `true` |
| `ANTHROPIC_API_KEY` | unset | Enables Anthropic Haiku category recommendations on the transaction create form |

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

## Repository Layout

- `src/` contains the application code
- `static/` contains CSS and static assets
- `e2e-tests/` contains Playwright specs, fixtures, and page objects
- `playwright.pyserver.config.ts` is the only supported Playwright config
