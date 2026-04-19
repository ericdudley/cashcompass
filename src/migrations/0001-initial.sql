CREATE TABLE IF NOT EXISTS accounts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    label        TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'net_worth'
                     CHECK(account_type IN ('expenses','net_worth')),
    is_archived  INTEGER NOT NULL DEFAULT 0 CHECK(is_archived IN (0,1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    label      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
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

CREATE INDEX IF NOT EXISTS idx_transactions_yyyy_mm_dd ON transactions(yyyy_mm_dd);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id);
