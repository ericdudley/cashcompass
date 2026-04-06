# CashCompass – Agent & Developer Guide

## Repo Layout

```
cashcompass/
├── server/                        # Go backend (module: cashcompass-server, go 1.22)
│   ├── cmd/server/main.go         # Entry point
│   └── internal/
│       ├── app/server.go          # Route wiring – constructs repos/services/handlers
│       ├── db/db.go               # Open, Migrate, SeedIfEmpty
│       ├── model/                 # Domain types (Account, Category, Transaction)
│       ├── repository/            # SQLite implementations of repository interfaces
│       ├── service/               # Business logic; depends on repositories
│       ├── handler/               # HTTP handlers; depends on services
│       │   └── render.go          # Shared renderPage helper + PageData struct
│       └── web/
│           ├── templates.go       # Parses all HTML templates from embed.FS
│           └── templates/
│               ├── layout.html            # Shared HTML shell (head, nav, main wrapper)
│               ├── *_page.html            # Per-page content templates (*-content names)
│               └── partials/              # HTMX partial templates
├── tests/server/                  # Playwright E2E tests against the Go server
│   ├── fixtures.ts                # Custom fixture – resets DB between tests
│   ├── pages/                     # Page-object models
│   └── *.spec.ts                  # Test suites per feature
└── static/                        # CSS and static assets served at /static/
```

## Architecture Layers

Each feature follows a strict layering: **model → repository → service → handler → template**.

| Layer      | Lives in          | Responsibility                                  |
|------------|-------------------|-------------------------------------------------|
| model      | `internal/model/` | Plain Go structs; no logic                      |
| repository | `internal/repository/` | SQL queries; implements interface          |
| service    | `internal/service/`    | Business rules; depends on repository interface |
| handler    | `internal/handler/`    | HTTP: parse request → call service → render template |
| template   | `internal/web/templates/` | HTML; uses HTMX for partial updates         |

## Running the Server

```bash
cd server
go run ./cmd/server          # default port 8080, DB at ./data/cashcompass.db
CASHCOMPASS_PORT=9000 go run ./cmd/server
CASHCOMPASS_DB_PATH=/tmp/cc.db go run ./cmd/server
```

## Running Tests

```bash
# Go unit tests (repository + service layers)
cd server && go test ./internal/repository/... ./internal/service/...

# Playwright E2E tests (spins up server on port 18080 with a fresh DB)
npm run test:server
```

## Adding a New Page

1. **Content template** – create `server/internal/web/templates/<feature>_page.html`:
   ```html
   {{ define "<feature>-content" }}
   <header class="space-y-2">
     <h1 class="text-4xl font-semibold text-white">Feature Name</h1>
   </header>
   <!-- page body -->
   {{ end }}
   ```

2. **Handler** – create `server/internal/handler/<feature>.go`:
   - Define a handler struct with `svc` and `tmpl` fields.
   - Add a `RegisterRoutes(mux)` method.
   - Render the full page with the shared helper:
     ```go
     renderPage(w, h.tmpl, "<nav-key>", "Page Title", "10", "<feature>-content", data)
     ```

3. **Wire it up** – add to `server/internal/app/server.go`:
   ```go
   featureHandler := handler.NewFeatureHandler(svc, s.Templates)
   featureHandler.RegisterRoutes(mux)
   ```

4. **Nav link** – add the route to `server/internal/web/templates/partials/nav.html` so it appears in the navigation bar.

## Adding a New HTMX Partial

1. **Template** – create `server/internal/web/templates/partials/<name>.html` with `{{ define "<name>" }}`.

2. **Handler endpoint** – add a `GET /partials/<name>` route that calls:
   ```go
   h.tmpl.ExecuteTemplate(w, "<name>", data)
   ```

3. **Wire the HTMX call** in the relevant page/partial template:
   ```html
   hx-get="/partials/<name>"
   hx-target="#<container-id>"
   hx-swap="outerHTML"
   ```

## Template Conventions

- **Full pages**: content templates named `<feature>-content` (rendered via `renderPage`).
- **List partials**: named `<feature>-list` (e.g. `accounts-list`).
- **Card partials**: named `<feature>-card`, `<feature>-card-edit`.
- **Form partials**: named `<feature>-form`.
- The shared `layout.html` provides the HTML shell, CDN scripts, nav, and `<main>` wrapper. It is driven by `PageData` in `handler/render.go`.

## Layout System

Every full-page response goes through `renderPage` in `handler/render.go`:

```
renderPage(w, tmpl, navKey, title, mainGap, contentTemplate, data)
       │                                         │
       └── ExecuteTemplate(buf, contentTemplate) ┘  ← renders inner HTML
       └── ExecuteTemplate(w, "layout", PageData{Body: buf})  ← wraps in shell
```

`mainGap` is a Tailwind gap value (`"10"` for most pages, `"6"` for Transactions).
