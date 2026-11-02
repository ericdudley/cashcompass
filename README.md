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

The **Budget** page (`/budget?month=YYYY-MM`) groups monthly budgets separately from annual budgets. Each compact card shows a remaining balance, a combined progress bar, an expandable breakdown, and an **Edit budget** action. Monthly bars show spending, the current allowance left, and rollover reserves left; monthly funds are consumed before rollover. Overspending uses the original scale with an explicit excess amount. Refunds reduce net spending; net credits and non-positive allowances have explicit monetary states.

Choose **Monthly** or **Annual** per category, including Uncategorized. Type changes apply to the whole selected year and inherit until the next saved plan. Annual budgets use an explicit full-year amount, include spending already recorded in that year, and inherit into later years; edits are not prorated. Converting to monthly requires an amount starting in January of the selected year and preserves later scheduled contribution changes. Monthly contribution changes otherwise apply from their effective month until the next saved change. Unchanged values do not create changes.

New monthly budgets start with rollover off. Rollover changes are independent of contributions: enabling it starts with zero carry-in in the effective month; disabling discards incoming carry. When enabled, both unused funds and deficits carry within the calendar year, resetting in January. Existing budgets migrate with rollover on to preserve balances. Zero remains active; blank monthly amounts stop tracking from that month and clear the balance, while blank annual amounts stop tracking from the selected year onward.

The **Annual** view (`/budget?view=annual&year=YYYY`) separates explicit annual budgets from annualized monthly budgets. Annualized amounts sum the year's scheduled contributions without adding rollover. Annual bars include a calendar-day pace marker, accounting for leap years; ahead of pace is informational, while exceeding the actual limit is an over-budget state.

Current progress uses transactions through local today; past periods use period-end, and future periods show plans without progress. Annual cards in monthly context use that month-end capped at today. Reporting cutoffs are labeled, and drilldowns use matching transaction dates across expense accounts. Historical corrections automatically update subsequent balances. Net worth accounts are excluded.

Backup version 5 preserves contribution changes, effective-year plans, and independent rollover changes. Versions 1–4 remain importable; legacy budgets import as monthly with rollover on. Backup restoration validates before replacing data and preserves Uncategorized and category UID mappings.

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
