CREATE TABLE IF NOT EXISTS annual_incomes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    uid                 TEXT NOT NULL UNIQUE,
    tax_year            INTEGER NOT NULL UNIQUE CHECK(tax_year BETWEEN 1900 AND 9999),
    gross_income_cents  INTEGER NOT NULL CHECK(gross_income_cents > 0),
    federal_tax_cents   INTEGER NOT NULL DEFAULT 0 CHECK(federal_tax_cents >= 0),
    state_tax_cents     INTEGER NOT NULL DEFAULT 0 CHECK(state_tax_cents >= 0),
    notes               TEXT NOT NULL DEFAULT '',
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK(federal_tax_cents + state_tax_cents <= gross_income_cents)
);

CREATE INDEX IF NOT EXISTS idx_annual_incomes_tax_year ON annual_incomes(tax_year);
