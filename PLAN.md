# CashCompass FastHTML Validation Plan

## Goal

Validate the new Python/FastHTML app feature by feature against the existing Playwright coverage, fixing feature bugs and stale test/page-object assumptions as we go.

The working rule is:

1. Pick one feature.
2. Run the smallest isolated test for that feature first.
3. Fix the feature and its Playwright page object/specs as needed.
4. Re-run the isolated test until it passes.
5. Run the full feature spec.
6. Mark the feature complete here before moving on.

Use the Python app and Python Playwright config unless there is a specific reason to compare with the Go app:

```bash
npx playwright test --config playwright.pyserver.config.ts
```

## Validation Order

This order is chosen to move from the smallest, lowest-coupling surface area to the heaviest feature with the most dependencies.

### 1. Categories

Status: Completed

Why first:

- Small CRUD surface
- Fewest dependencies
- Good proving ground for HTMX swaps, inline edit patterns, and FastHTML route behavior

Validation scope:

- Create category
- Edit category label
- Cancel edit
- Delete category
- Multiple categories render correctly
- Category rename/delete side effects on transaction data stay correct

Validation notes:

- Completed during the category audit
- Found and fixed the FastHTML route-method issue where read-only routes were unintentionally handling `POST`
- Updated the category Playwright page object to match the FastHTML DOM
- Added category label validation and delete-side transaction cleanup

### 2. Navigation

Status: Completed

Why next:

- Small surface area
- Exercises app shell and shared layout
- Helps catch global regressions before validating more complex pages

Primary spec:

```bash
npx playwright test --config playwright.pyserver.config.ts tests/server/nav.spec.ts --grep "nav bar is visible on home page" --project=desktop
```

Feature checklist:

- Nav renders on `/` and destination pages
- Brand link behavior matches expected redirect flow
- Desktop and mobile nav both behave correctly
- Active-link styling is correct

Likely files:

- `src/components/layout.py`
- `src/main.py`
- `tests/server/nav.spec.ts`

Validation notes:

- Shared FastHTML nav layout passed as-is on both desktop and mobile
- Verified active-link styling for Accounts and Categories pages
- Verified `/` brand-link flow lands on `/dashboard` through the root redirect

### 3. Dashboard

Status: Completed

Why here:

- Read-only feature with seeded-data dependencies
- Builds confidence in routing, charts/summary rendering, and shared navigation
- Lower risk than account/transaction mutation flows

Primary spec:

```bash
npx playwright test --config playwright.pyserver.config.ts tests/server/dashboard.spec.ts --grep "dashboard page loads" --project=desktop
```

Feature checklist:

- `/` redirects to `/dashboard`
- Dashboard header renders
- Summary stats render
- Expenses section renders
- Net worth section renders
- Category table or empty state renders correctly
- Dashboard nav state is active

Likely files:

- `src/routes/dashboard.py`
- `src/components/dashboard.py`
- `src/components/layout.py`
- `tests/server/pages/dashboard.page.ts`

Validation notes:

- Dashboard route and component passed as-is against the Python test DB seed data
- Verified `/` redirect, summary stats, expenses section, net worth section, and active dashboard nav state
- Verified the category table path under seeded expense data on desktop and mobile

### 4. Accounts

Status: Completed

Why after dashboard:

- Medium-complexity CRUD
- Similar inline-edit HTMX patterns to categories
- Introduces archive behavior and transaction label sync side effects

Primary spec:

```bash
npx playwright test --config playwright.pyserver.config.ts tests/server/accounts.spec.ts --grep "create account" --project=desktop
```

Feature checklist:

- Create net worth account
- Create expenses account
- Edit account label
- Cancel edit
- Toggle account type
- Archive and unarchive
- Delete account
- Active vs archived sections render correctly
- Account rename side effects update transaction labels correctly

Likely files:

- `src/routes/accounts.py`
- `src/components/accounts.py`
- `src/services/account.py`
- `src/repository/account.py`
- `src/repository/transaction.py`
- `tests/server/pages/accounts.page.ts`

Watch-outs:

- Accounts routes likely need the same explicit `methods=["GET"]` treatment as categories
- Account label validation may still be missing
- Account delete/archive side effects may need cleanup or verification

Validation notes:

- Fixed the FastHTML route-method issue on `/accounts` and account partial routes so HTMX POST/GET swaps return partials instead of nesting a full page
- Added basic account label validation in the service layer and returned `400` responses for invalid create/edit submissions
- Verified create, edit, cancel, type toggle, archive/unarchive, and delete flows via the full accounts spec on desktop and mobile
- Verified account rename side effects update `transactions.account_label` with a targeted temporary-DB check

### 5. Transactions

Status: Completed

Why later:

- Highest complexity feature
- Depends on accounts, categories, date handling, filters, and HTMX push-url behavior
- Best validated after accounts/categories/dashboard basics are stable

Primary spec:

```bash
npx playwright test --config playwright.pyserver.config.ts tests/server/transactions.spec.ts --grep "transactions page loads" --project=desktop
```

Feature checklist:

- Transactions page loads
- Seeded rows render
- Default preset is correct
- Create form renders
- Create transaction
- Edit transaction
- Cancel edit
- Delete transaction
- Filter UI renders
- Label filter updates results
- URL updates on preset/filter change
- Daily subtotal updates after create/delete
- URL params restore state on reload

Likely files:

- `src/routes/transactions.py`
- `src/components/transactions.py`
- `src/services/transaction.py`
- `src/repository/transaction.py`
- `src/utils/dates.py`
- `tests/server/pages/transactions.page.ts`

Watch-outs:

- HTMX partial responses that should set `HX-Push-Url`
- Date formatting and date preset logic
- Form field names/selectors drifting from the legacy test assumptions
- Side effects when account/category IDs are missing or invalid

Validation notes:

- Fixed the preset date-range helper in `src/utils/dates.py` so `this_month` and `last_month` compute month-end correctly instead of crashing `/transactions`
- Verified the transactions page, seeded rows, create/edit/cancel/delete flows, filter UI, `HX-Push-Url`-driven URL updates, daily subtotal updates, and reload-state restoration
- Full transactions spec passed on desktop and mobile without page-object changes

### 6. Settings / Import-Export / Admin Flows

Status: Completed

Why last:

- Operational surface area rather than core daily-product flow
- Likely to involve file handling, CSV import/export, and dev-only behavior
- May not yet have full Playwright coverage, so this likely needs mixed manual + automated validation

Suggested starting point:

- Audit existing `src/routes/settings.py` and related components
- Identify whether there is Playwright coverage already
- If coverage is missing, define focused validation steps before writing or updating tests

Likely files:

- `src/routes/settings.py`
- `src/components/settings.py`
- `tests/server/` for any related specs

Validation notes:

- No existing Playwright coverage was present for settings/admin flows, so validation used focused HTTP/manual checks against a temp dev DB
- Fixed `src/routes/settings.py` date parsing so CSV imports accept ISO timestamps with timezone offsets like `-07:00` in addition to plain dates and `Z` timestamps
- Verified `/settings` page render, expenses export, accounts export, expenses import redirect/message/count, accounts import redirect/message/count, and dev-only reset redirect/message
- Verified imported expense/account CSV rows round-trip into the export endpoints correctly, and that reset leaves exports empty again

## Status Board

| Order | Feature | Status | Notes |
|---|---|---|---|
| 1 | Categories | Completed | Create path fixed, route methods corrected, full categories spec passing |
| 2 | Navigation | Completed | Shared nav/layout validated; desktop + mobile nav spec passing without code changes |
| 3 | Dashboard | Completed | Seeded dashboard rendering validated; full dashboard spec passing without code changes |
| 4 | Accounts | Completed | Route methods corrected, label validation added, full accounts spec and rename side-effect check passing |
| 5 | Transactions | Completed | Month-end preset bug fixed; full transactions spec passing on desktop and mobile |
| 6 | Settings / Import-Export | Completed | Offset timestamp import fixed; focused settings/import/export/reset checks passed on a temp dev DB |

## Per-Feature Validation Workflow

For each feature:

1. Read the relevant Python route/component/service/repository files.
2. Read the matching Playwright spec and page object.
3. Run only one small test from that feature with `--grep`.
4. Fix the Python app first when the behavior is wrong.
5. Fix the Playwright page object/spec when selectors or assumptions are stale.
6. Re-run the isolated test until green.
7. Run the full feature spec.
8. Record what changed in this file and mark the feature `Completed`.

## Reusable System Prompt

Use this as the system prompt for an agent that should pick up the next validation item automatically.

```text
You are validating the CashCompass Python/FastHTML migration one feature at a time.

Repository context:
- The Python app under `src/` is the primary target.
- The Go app under `server/` is legacy/reference only.
- Playwright tests for the Python app must be run with `playwright.pyserver.config.ts`.
- The repo includes `AGENTS.md` and `PLAN.md`; follow both.

Your task:
1. Open `PLAN.md`.
2. Find the first feature in the validation order whose status is `Pending`.
3. Validate only that feature in this turn.
4. Start by reading the relevant Python route/component/service/repository files and the matching Playwright spec/page object.
5. Run the smallest isolated Playwright test for that feature first, not the whole suite.
6. Fix real feature bugs in the Python app.
7. Update stale Playwright selectors/page objects/specs only as needed to reflect the FastHTML app.
8. Once the isolated test passes, run the full Playwright spec for that feature.
9. If useful, run one or two targeted non-Playwright checks for important side effects or data integrity.
10. Update `PLAN.md` to mark that feature as `Completed` and add a short note about what was fixed and what was verified.

Rules:
- Do not move on to the next feature in the same turn.
- Prefer small focused edits.
- Preserve any existing user changes you did not make.
- If a full-page HTMX swap appears where a partial is expected, inspect FastHTML route method declarations.
- If the feature is blocked by missing coverage or unclear expected behavior, document the blocker in `PLAN.md` and stop.

Deliverable:
- Make the code/test fixes.
- Verify the feature.
- Update `PLAN.md`.
- Report the feature you completed, what changed, and what tests/checks passed.
```

## Manual Invocation Prompt

If you want a shorter handoff message after setting the system prompt above, use:

```text
Take the next pending feature from PLAN.md, validate it in isolation, fix issues, run the full feature spec, and then update PLAN.md to mark it completed with short notes.
```
