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

The **Budget** page (`/budget`) shows monthly spending, refunds/credits, and net expenses by category across expense accounts, with a previous-month comparison and links to the matching transactions. Set a monthly contribution for each category: changes apply from the selected month until the next saved change, including across years. Saving unchanged values does not create new changes.

Available funds are the month's contribution plus the previous month's remaining balance. Both unused funds and deficits roll over within the calendar year; January resets balances to zero while retaining recurring contributions. Refunds and credits reduce net expenses. Tracking starts in the first budgeted month without an opening deficit from earlier spending. Zero keeps tracking and rollover with no new contribution; blank stops tracking and clears rollover until a later change resumes it.

Annual budgets are derived from the sum of January–December contributions, including scheduled changes, without adding rollover. Annual progress shows net spending from January through the selected month, including spending before tracking began. Historical transaction or budget corrections automatically update subsequent balances. Unbudgeted categories remain in expense reports without budget progress.

Backup version 4 preserves recurring changes, including blank stop records. Versions 1–3 remain importable. Existing monthly budget rows and version 3 backup rows become effective-month changes: previously empty intervening and future months now inherit the most recent contribution.

The **Transactions** page keeps its category breakdown collapsed by default, with compact totals always visible. Select “Show categories” (or focus the summary and press Enter/Space) to expand the details. The open/closed preference is retained for the browser tab, including after filtering or editing transactions.

The **Transactions** page shows a category breakdown for the active date, category, and search filters, including uncategorized activity. Net expenses subtract credits from spending; category shares use spending before credits.

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
| `CASHCOMPASS_TIMEZONE` | `America/Los_Angeles` | Calendar timezone for monthly reports, transaction date presets, and demo data |
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
