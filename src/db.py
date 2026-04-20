import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from src.utils.ids import generate_uid


class Database:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = 1")
        self.conn.commit()

    def execute(self, sql: str, params=()):
        return self.conn.execute(sql, params)

    def commit(self):
        self.conn.commit()

    def run_migrations(self, migrations_path: str):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self.conn.commit()

        mig_dir = Path(migrations_path)
        for mig_file in sorted(mig_dir.glob("*.sql")):
            version = mig_file.stem
            exists = self.conn.execute(
                "SELECT COUNT(1) FROM schema_migrations WHERE version = ?", [version]
            ).fetchone()[0]
            if exists:
                continue
            sql = mig_file.read_text()
            self.conn.executescript(sql)
            self.conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", [version])
            self.conn.commit()


def seed_if_empty(db: Database):
    count = db.execute("SELECT COUNT(1) FROM accounts").fetchone()[0]
    if count > 0:
        return False

    db.execute(
        "INSERT INTO accounts (uid, label, account_type) VALUES (?, 'Checking', 'net_worth')",
        [generate_uid("acct")],
    )
    db.execute(
        "INSERT INTO accounts (uid, label, account_type) VALUES (?, 'Savings', 'net_worth')",
        [generate_uid("acct")],
    )
    db.execute(
        "INSERT INTO accounts (uid, label, account_type) VALUES (?, 'Daily Expenses', 'expenses')",
        [generate_uid("acct")],
    )
    db.commit()

    db.execute("INSERT INTO categories (uid, label) VALUES (?, 'Groceries')", [generate_uid("cat")])
    db.execute("INSERT INTO categories (uid, label) VALUES (?, 'Utilities')", [generate_uid("cat")])
    db.execute("INSERT INTO categories (uid, label) VALUES (?, 'Transport')", [generate_uid("cat")])
    db.commit()

    daily_id = db.execute("SELECT id FROM accounts WHERE label = 'Daily Expenses'").fetchone()[0]
    groc_id = db.execute("SELECT id FROM categories WHERE label = 'Groceries'").fetchone()[0]
    util_id = db.execute("SELECT id FROM categories WHERE label = 'Utilities'").fetchone()[0]
    trans_id = db.execute("SELECT id FROM categories WHERE label = 'Transport'").fetchone()[0]

    now = datetime.now(timezone.utc)
    year, month = now.year, now.month

    def d(day):
        dt = date(year, month, day)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%Y_%m_%d")

    d1_iso, d1_ymd = d(1)
    d2_iso, d2_ymd = d(2)
    d3_iso, d3_ymd = d(3)

    db.execute(
        """
        INSERT INTO transactions (
            uid, iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label
        ) VALUES (?, ?, ?, -5432, 'Weekly shop', ?, 'Daily Expenses', ?, 'Groceries')
        """,
        [generate_uid("txn"), d1_iso, d1_ymd, daily_id, groc_id],
    )
    db.execute(
        """
        INSERT INTO transactions (
            uid, iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label
        ) VALUES (?, ?, ?, -9800, 'Electric bill', ?, 'Daily Expenses', ?, 'Utilities')
        """,
        [generate_uid("txn"), d2_iso, d2_ymd, daily_id, util_id],
    )
    db.execute(
        """
        INSERT INTO transactions (
            uid, iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label
        ) VALUES (?, ?, ?, -3200, 'Bus pass', ?, 'Daily Expenses', ?, 'Transport')
        """,
        [generate_uid("txn"), d3_iso, d3_ymd, daily_id, trans_id],
    )
    db.commit()
    return True
