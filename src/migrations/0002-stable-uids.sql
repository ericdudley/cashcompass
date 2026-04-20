PRAGMA foreign_keys=OFF;

CREATE TABLE accounts_new (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    uid          TEXT NOT NULL UNIQUE,
    label        TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'net_worth'
                     CHECK(account_type IN ('expenses','net_worth')),
    is_archived  INTEGER NOT NULL DEFAULT 0 CHECK(is_archived IN (0,1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO accounts_new (id, uid, label, account_type, is_archived, created_at, updated_at)
SELECT
    id,
    'acct_' || lower(hex(randomblob(16))),
    label,
    account_type,
    is_archived,
    created_at,
    updated_at
FROM accounts;

CREATE TABLE categories_new (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    uid        TEXT NOT NULL UNIQUE,
    label      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO categories_new (id, uid, label, created_at, updated_at)
SELECT
    id,
    'cat_' || lower(hex(randomblob(16))),
    label,
    created_at,
    updated_at
FROM categories;

CREATE TABLE transactions_new (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    uid            TEXT NOT NULL UNIQUE,
    iso8601        TEXT NOT NULL,
    yyyy_mm_dd     TEXT NOT NULL,
    amount         INTEGER NOT NULL,
    label          TEXT NOT NULL DEFAULT '',
    account_id     INTEGER REFERENCES accounts_new(id) ON DELETE SET NULL,
    account_label  TEXT NOT NULL DEFAULT '',
    category_id    INTEGER REFERENCES categories_new(id) ON DELETE SET NULL,
    category_label TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO transactions_new (
    id,
    uid,
    iso8601,
    yyyy_mm_dd,
    amount,
    label,
    account_id,
    account_label,
    category_id,
    category_label,
    created_at,
    updated_at
)
SELECT
    id,
    'txn_' || lower(hex(randomblob(16))),
    iso8601,
    yyyy_mm_dd,
    amount,
    label,
    account_id,
    account_label,
    category_id,
    category_label,
    created_at,
    updated_at
FROM transactions;

DROP TABLE transactions;
DROP TABLE categories;
DROP TABLE accounts;

ALTER TABLE accounts_new RENAME TO accounts;
ALTER TABLE categories_new RENAME TO categories;
ALTER TABLE transactions_new RENAME TO transactions;

CREATE INDEX idx_transactions_yyyy_mm_dd ON transactions(yyyy_mm_dd);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);

PRAGMA foreign_keys=ON;
