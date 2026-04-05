# Cash Compass HTMX Parity Tasks

Goal: match the existing Svelte Cash Compass feature set with the Go + HTMX server (including import/export).

## Architecture & Infrastructure
- [x] Repository / Service / Handler layered architecture (`internal/model`, `repository`, `service`, `handler`)
- [x] Interface-based repositories — unit-testable with hand-written mocks
- [x] Repository integration tests against `:memory:` SQLite
- [x] Playwright E2E test config (`playwright.server.config.ts`) — isolated port 18080, fresh DB each run
- [x] `CASHCOMPASS_DB_PATH` and `CASHCOMPASS_PORT` env vars for test isolation
- [x] Shared nav layout (top bar with links to Accounts, Categories, Transactions, Dashboard, Settings)
- [x] `TransactionRepository` interface + SQLite impl (needed by sync logic in AccountService / CategoryService)

## Backend/Data
- [x] SQLite schema: `accounts` table with `account_type`, `is_archived`, timestamps (migration V1)
- [x] SQLite schema: `categories` table (migration V2)
- [x] SQLite schema: `transactions` table with `yyyy_mm_dd`, denormalized labels, indexes (migration V3)
- [x] Forward-only versioned migrations (`schema_migrations` table)
- [x] Sync denormalized `account_label` in transactions when account label is updated
- [x] Sync denormalized `category_label` in transactions when category label is updated
- [ ] `deleteAllData` utility (truncate all tables, reset sequences)
- [ ] `repairData` utility: fill missing labels (`Uncategorized` / `Unknown Account`), re-derive `yyyy_mm_dd` from `iso8601`, re-sync denormalized fields

## Accounts
- [x] Accounts page (`/accounts`) — Active / Archived sections, HTMX-driven
- [x] Playwright E2E tests for all account CRUD flows
- [x] Create account (label + type, default `net_worth`)
- [x] Inline edit label (edit overlay with Save / Cancel)
- [x] Toggle account type (`expenses` ↔ `net_worth`)
- [x] Archive / unarchive (list re-renders so card moves between sections)
- [x] Delete account with confirm (DB `ON DELETE SET NULL` nulls out transaction refs)
- [x] Sync dependent transactions on label change

## Categories
- [x] `model.Category`, `CategoryRepository` interface + `SQLiteCategoryRepository`
- [x] `CategoryService` interface + impl (UpdateLabel syncs `category_label` in transactions)
- [x] Repository integration tests + service unit tests with mock
- [x] Categories page (`/categories`) — list with inline edit and delete
- [x] Create category
- [x] Inline edit label (same overlay pattern as accounts)
- [x] Delete category with confirm (`ON DELETE SET NULL` for transactions)
- [x] Playwright E2E tests

## Transactions
- [x] `model.Transaction`, `TransactionRepository` interface + `SQLiteTransactionRepository`
  - [x] `List(ctx, filter)` — date range, label search, account IDs, category IDs; ordered by `yyyy_mm_dd` DESC
  - [x] `Create`, `UpdateAmount`, `UpdateLabel`, `UpdateAccount`, `UpdateCategory`, `UpdateDate`, `Delete`
  - [x] `SumByMonth(ctx, accountType, dateRange)` — for dashboard stats
  - [x] `BalancesByMonth(ctx, accountIDs)` — cumulative net-worth balances per account per month
- [x] `TransactionService` interface + impl
- [x] Repository integration tests + service unit tests
- [x] Transaction list page (`/transactions`):
  - [x] Page loads, grouped by date, amount / label / account / category columns
  - [x] Date range filter with presets (This Month, Last Month, This Year, All Time)
  - [x] Label search input
  - [x] Category filter pills (multi-select)
  - [x] Grouped by date with per-day subtotals
  - [ ] Grouped by year / month with subtotals (currently day-only grouping)
  - [x] Inline edit: amount, label, account, category, date
  - [x] Delete with confirm
- [x] Transaction create form:
  - [x] Fields: date, label, amount, account (select), category (select)
  - [x] Amount mode: `debit` (negative), `credit` (positive)
  - [ ] Amount mode: `reconcile` (= input − latest balance)
  - [x] Restore last-used account on page load (cookie)
- [x] Playwright E2E tests — smoke tests (page loads, seeded rows visible)

## Net Worth Reconciliation (future)
- [ ] In Net Worth mode, allow entering a current balance → auto-create a delta reconciliation transaction
  - [ ] Ensure `Reconciliation` category exists (create if missing)
  - [ ] Compute delta = input balance − latest cumulative balance for selected account
  - [ ] Create a transaction with the delta amount, date = today, category = Reconciliation

## Dashboard
- [ ] Date range input with presets
- [ ] Summary stats:
  - [ ] This month's expenses total
  - [ ] % diff vs previous month
  - [ ] Average monthly expenses (full months only)
  - [ ] Net worth total (current month)
- [ ] Expenses section:
  - [ ] Bar chart — monthly expense totals (pure SVG or lightweight JS)
  - [ ] Category-by-month table with totals and averages
- [ ] Net worth section:
  - [ ] Line chart — account balances over time
  - [ ] Net worth table (accounts × months)

## Settings
- [ ] Import / Export: Expenses CSV
  - [ ] Import columns: `Amount`, `Category`, `Date`, `Description`
  - [ ] Create a new `expenses` account named `Imported Expenses <timestamp>`
  - [ ] Create missing categories on import
  - [ ] Import transactions with negative amounts
  - [ ] Export all `expenses` transactions to CSV (same columns)
- [ ] Import / Export: Accounts (net worth) CSV
  - [ ] Import columns: `Account`, `Date`, `Balance`
  - [ ] Ensure `Reconciliation` category exists
  - [ ] Create `net_worth` accounts from file
  - [ ] Sort by date; create delta transactions to reconcile balances
  - [ ] Export: cumulative balance per account per date as CSV rows
- [ ] Delete-all-data with confirmation
- [ ] Repair-data with confirmation
- [ ] Changelog view with "Load more" pagination

## Navigation & Layout
- [x] Persistent top nav / sidebar with links: Accounts, Categories, Transactions
- [ ] Settings link in nav
- [ ] Dashboard link in nav (once page exists)
- [x] Responsive mobile drawer
- [x] Active-link highlighting

## UI Components / Interactions
- [ ] Combobox: typeahead, keyboard navigation, create-on-enter confirmation (needed for transaction form)
- [ ] Date input: `+`/`−` day buttons and quick presets (Today / Yesterday / 2 Days Ago)
- [ ] Date range input with preset ranges
- [ ] Currency input: formatted on blur, raw edit on focus
- [ ] Multi-select pill filter with clear action (category / account filter)
- [ ] Loading indicator for async HTMX requests (`htmx:beforeRequest` / `htmx:afterRequest`)
