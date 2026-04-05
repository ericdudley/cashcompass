package db

import (
	"database/sql"
	"fmt"
	"time"
	_ "modernc.org/sqlite"
)

func Open(path string) (*sql.DB, error) {
	dsn := fmt.Sprintf("file:%s?_pragma=foreign_keys(1)", path)
	return sql.Open("sqlite", dsn)
}

const migrationV1 = `
CREATE TABLE accounts_new (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    label        TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'net_worth'
                     CHECK(account_type IN ('expenses','net_worth')),
    is_archived  INTEGER NOT NULL DEFAULT 0 CHECK(is_archived IN (0,1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
INSERT INTO accounts_new (id, label, account_type, is_archived, created_at)
    SELECT id, name, 'net_worth', 0, created_at FROM accounts;
DROP TABLE accounts;
ALTER TABLE accounts_new RENAME TO accounts;
`

const migrationV2 = `
CREATE TABLE categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    label      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
`

const migrationV3 = `
CREATE TABLE transactions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    iso8601        TEXT NOT NULL,
    yyyy_mm_dd     TEXT NOT NULL,
    amount         INTEGER NOT NULL,
    label          TEXT NOT NULL DEFAULT '',
    account_id     INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    account_label  TEXT NOT NULL DEFAULT '',
    category_id    INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    category_label TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_transactions_yyyy_mm_dd ON transactions(yyyy_mm_dd);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
`

var migrations = []struct {
	version int
	sql     string
}{
	{1, migrationV1},
	{2, migrationV2},
	{3, migrationV3},
}

// MigrateResult reports which migrations were applied vs already present.
type MigrateResult struct {
	Applied []int
	Skipped []int
}

func Migrate(db *sql.DB) (MigrateResult, error) {
	var result MigrateResult

	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version    INTEGER PRIMARY KEY,
			applied_at TEXT NOT NULL DEFAULT (datetime('now'))
		);
		CREATE TABLE IF NOT EXISTS accounts (
			id           INTEGER PRIMARY KEY AUTOINCREMENT,
			name         TEXT NOT NULL,
			balance_cents INTEGER NOT NULL DEFAULT 0,
			created_at   TEXT NOT NULL DEFAULT (datetime('now'))
		);
	`)
	if err != nil {
		return result, fmt.Errorf("create bootstrap tables: %w", err)
	}

	for _, m := range migrations {
		var applied int
		err := db.QueryRow("SELECT COUNT(1) FROM schema_migrations WHERE version = ?", m.version).Scan(&applied)
		if err != nil {
			return result, fmt.Errorf("check migration %d: %w", m.version, err)
		}
		if applied > 0 {
			result.Skipped = append(result.Skipped, m.version)
			continue
		}

		tx, err := db.Begin()
		if err != nil {
			return result, fmt.Errorf("begin migration %d: %w", m.version, err)
		}
		if _, err := tx.Exec(m.sql); err != nil {
			_ = tx.Rollback()
			return result, fmt.Errorf("run migration %d: %w", m.version, err)
		}
		if _, err := tx.Exec("INSERT INTO schema_migrations (version) VALUES (?)", m.version); err != nil {
			_ = tx.Rollback()
			return result, fmt.Errorf("record migration %d: %w", m.version, err)
		}
		if err := tx.Commit(); err != nil {
			return result, fmt.Errorf("commit migration %d: %w", m.version, err)
		}
		result.Applied = append(result.Applied, m.version)
	}
	return result, nil
}

// SeedIfEmpty inserts sample data when the accounts table is empty.
// Returns true if seeding occurred.
func SeedIfEmpty(db *sql.DB) (bool, error) {
	var count int
	if err := db.QueryRow("SELECT COUNT(1) FROM accounts").Scan(&count); err != nil {
		return false, err
	}
	if count > 0 {
		return false, nil
	}

	_, err := db.Exec(`
		INSERT INTO accounts (label, account_type) VALUES
			('Checking', 'net_worth'),
			('Savings', 'net_worth'),
			('Daily Expenses', 'expenses');
	`)
	if err != nil {
		return false, fmt.Errorf("seed accounts: %w", err)
	}

	_, err = db.Exec(`
		INSERT INTO categories (label) VALUES
			('Groceries'),
			('Utilities'),
			('Transport');
	`)
	if err != nil {
		return false, fmt.Errorf("seed categories: %w", err)
	}

	// Use current-month dates so seeded transactions appear with the default "this_month" filter.
	now := time.Now().UTC()
	d1 := time.Date(now.Year(), now.Month(), 1, 10, 0, 0, 0, time.UTC)
	d2 := time.Date(now.Year(), now.Month(), 2, 9, 0, 0, 0, time.UTC)
	d3 := time.Date(now.Year(), now.Month(), 3, 8, 30, 0, 0, time.UTC)

	_, err = db.Exec(`
		INSERT INTO transactions (iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label) VALUES
			(?, ?, -5432, 'Weekly shop', 3, 'Daily Expenses', 1, 'Groceries'),
			(?, ?, -9800, 'Electric bill', 3, 'Daily Expenses', 2, 'Utilities'),
			(?, ?, -3200, 'Bus pass', 3, 'Daily Expenses', 3, 'Transport');
	`,
		d1.Format(time.RFC3339), d1.Format("2006_01_02"),
		d2.Format(time.RFC3339), d2.Format("2006_01_02"),
		d3.Format(time.RFC3339), d3.Format("2006_01_02"),
	)
	if err != nil {
		return false, fmt.Errorf("seed transactions: %w", err)
	}

	return true, nil
}
