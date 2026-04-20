# CashCompass – Agent & Developer Guide

## Current State

This repo is Python/FastHTML only.

- Feature work should target the app under `src/`.
- End-to-end coverage lives in `e2e-tests/` and runs through `playwright.pyserver.config.ts`.
- There is no supported legacy server path in this repo anymore.

## Repo Layout

```text
cashcompass/
├── src/                           # New Python/FastHTML app
│   ├── main.py                    # App entry point, route registration, DB init
│   ├── db.py                      # SQLite wrapper, migrations, seed_if_empty
│   ├── models.py                  # Dataclasses for Account, Category, Transaction
│   ├── migrations/                # SQL migrations for Python app
│   ├── repository/                # SQLite data access layer
│   ├── services/                  # Business logic layer
│   ├── routes/                    # HTTP routes and HTMX endpoints
│   ├── components/                # FastHTML UI components/pages/partials
│   └── utils/                     # Formatting and date helpers
├── e2e-tests/                     # Playwright E2E tests and page objects
│   ├── fixtures.ts                # Resets the DB through /dev/reset before each test
│   ├── pages/                     # Page-object models
│   └── *.spec.ts                  # Feature specs
├── static/                        # Static assets served by the Python app
├── playwright.pyserver.config.ts  # Playwright config for the Python/FastHTML app
├── Dockerfile
└── Makefile
```

## Python App Architecture

The Python app follows a layered structure:

| Layer | Lives in | Responsibility |
|---|---|---|
| model | `src/models.py` | Dataclasses only |
| repository | `src/repository/` | SQL queries and row mapping |
| service | `src/services/` | Validation and business rules |
| route | `src/routes/` | Request parsing, HTMX/full-page responses |
| component | `src/components/` | FastHTML page, form, list, card, and row rendering |

Typical flow is:

```text
models -> repository -> service -> route -> component
```

## Python App Entry Points

- Main app: `src/main.py`
- Default port: `8080`
- Default DB path: `./src/data/cashcompass.db`
- Default migrations path: `./src/migrations`

Useful env vars:

| Variable | Default | Description |
|---|---|---|
| `CASHCOMPASS_DB_PATH` | `./src/data/cashcompass.db` | SQLite database for the Python app |
| `CASHCOMPASS_MIGRATIONS_PATH` | `./src/migrations` | SQL migrations directory |
| `CASHCOMPASS_PORT` | `8080` | HTTP port |
| `CASHCOMPASS_DEV` | unset | Enables `/dev/reset` and other dev-only endpoints when `true` |

## Running the Python App

```bash
.venv/bin/python -m uvicorn src.main:app --port 8080 --no-access-log
```

Example with a throwaway DB:

```bash
CASHCOMPASS_DB_PATH=/tmp/cashcompass.db CASHCOMPASS_DEV=true .venv/bin/python -m uvicorn src.main:app --port 8080 --no-access-log
```

## Running Tests

Python/FastHTML Playwright tests:

```bash
npx playwright test --config playwright.pyserver.config.ts
```

Run one spec:

```bash
npx playwright test --config playwright.pyserver.config.ts e2e-tests/categories.spec.ts
```

Run one test in isolation:

```bash
npx playwright test --config playwright.pyserver.config.ts e2e-tests/categories.spec.ts --grep "create category" --project=desktop
```

## FastHTML Conventions

### Routes

Routes live in `src/routes/*.py` and are registered from `src/main.py`.

Each feature usually exposes:

- A full-page route such as `GET /categories`
- Mutating HTMX routes such as `POST /categories`, `PUT /categories/{id}`, `DELETE /categories/{id}`
- Partial routes such as `GET /partials/categories` or `GET /partials/categories/{id}/edit`

Important FastHTML gotcha:

- Always declare explicit methods for read-only routes, for example `@rt("/categories", methods=["GET"])`.
- Do not rely on the default decorator behavior for page or partial routes.
- During the migration we hit a bug where a `GET` page route also accepted `POST`, causing HTMX form submissions to return a full page instead of the intended partial.

### Components

Components live in `src/components/*.py`.

Common patterns:

- `*_page(...)` returns the full page body content
- `*_list(...)` returns an HTMX-swappable list container
- `*_card(...)` or `*_row(...)` returns a single display item
- `*_card_edit(...)` or `*_row_edit(...)` returns the inline edit state
- Shared shell/navigation lives in `src/components/layout.py`

### HTMX

HTMX attributes are expressed with FastHTML keyword args such as:

- `hx_get`
- `hx_post`
- `hx_put`
- `hx_delete`
- `hx_target`
- `hx_swap`
- `hx_include`
- `hx_vals`
- `hx_confirm`

FastHTML renders these to normal `hx-*` attributes in HTML.

## Playwright Guidance

The current E2E coverage lives in `e2e-tests/`.

Before changing tests:

- Use `playwright.pyserver.config.ts`.
- Check the actual rendered FastHTML DOM instead of assuming an older selector still applies.
- Prefer updating page objects in `e2e-tests/pages/` instead of duplicating selectors in specs.

Current Python test harness details:

- `playwright.pyserver.config.ts` runs the Python app on port `18081`
- It uses `/tmp/cashcompass_py_test.db`
- `e2e-tests/fixtures.ts` resets state before each test by POSTing to `/dev/reset`
- Tests require `CASHCOMPASS_DEV=true` so the reset endpoint exists

## Data Integrity Notes

Some service-layer responsibilities are easy to miss during migration:

- Renaming an account should sync `transactions.account_label`
- Renaming a category should sync `transactions.category_label`
- Deleting a category should also clear `transactions.category_id` and `transactions.category_label`
- Validation belongs in the service layer when possible, with the route converting expected validation failures into HTTP responses

## Adding or Updating a Feature in the Python App

1. Add or update repository logic in `src/repository/`
2. Add validation and business rules in `src/services/`
3. Add routes and HTMX endpoints in `src/routes/`
4. Add or update FastHTML rendering in `src/components/`
5. Wire the route module from `src/main.py` if needed
6. Update the relevant Playwright page object and spec
7. Verify at least the smallest isolated test before running the broader suite

For UI work, prefer this sequence:

1. Run a single Playwright test with `--grep`
2. Fix feature bugs first
3. Update stale selectors in the page object
4. Re-run the isolated test
5. Expand to the full feature spec

## Practical Workflow Tips

- Check `git status` before editing because the migration branch may already be dirty.
- Prefer small focused Playwright runs while updating selectors and HTMX behavior.
- If an HTMX action swaps in an entire page unexpectedly, inspect route method declarations first.
- If a FastHTML component seems to stringify oddly in a quick REPL print, use `to_xml(...)` to inspect the rendered HTML.
- Use seeded data expectations carefully: the Python app seeds accounts, categories, and transactions on an empty DB.
