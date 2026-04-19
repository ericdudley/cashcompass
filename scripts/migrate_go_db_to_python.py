#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


PYTHON_INITIAL_MIGRATION = "0001-initial"
LEGACY_ARCHIVE_TABLE = "schema_migrations_go_legacy"


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        [name],
    ).fetchone()
    return row is not None


def get_table_columns(conn: sqlite3.Connection, name: str) -> list[sqlite3.Row]:
    return conn.execute(f"PRAGMA table_info({name})").fetchall()


def validate_expected_tables(conn: sqlite3.Connection) -> None:
    required = {
        "accounts": {"id", "label", "account_type", "is_archived", "created_at", "updated_at"},
        "categories": {"id", "label", "created_at", "updated_at"},
        "transactions": {
            "id",
            "iso8601",
            "yyyy_mm_dd",
            "amount",
            "label",
            "account_id",
            "account_label",
            "category_id",
            "category_label",
            "created_at",
            "updated_at",
        },
    }

    for table, expected_cols in required.items():
        if not table_exists(conn, table):
            raise RuntimeError(f"expected table '{table}' was not found")
        actual_cols = {row["name"] for row in get_table_columns(conn, table)}
        missing = expected_cols - actual_cols
        if missing:
            raise RuntimeError(
                f"table '{table}' is missing expected columns: {', '.join(sorted(missing))}"
            )


def create_backup(db_path: Path, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, backup_path)


def ensure_python_schema_migrations(conn: sqlite3.Connection) -> str:
    if not table_exists(conn, "schema_migrations"):
        conn.execute(
            """
            CREATE TABLE schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
            [PYTHON_INITIAL_MIGRATION],
        )
        return "created Python schema_migrations and marked 0001-initial"

    columns = get_table_columns(conn, "schema_migrations")
    version_col = next((col for col in columns if col["name"] == "version"), None)
    if version_col is None:
        raise RuntimeError("schema_migrations exists but has no 'version' column")

    existing_versions = [str(row[0]) for row in conn.execute("SELECT version FROM schema_migrations").fetchall()]

    # Already Python-compatible text table
    if version_col["type"].upper() == "TEXT":
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
            [PYTHON_INITIAL_MIGRATION],
        )
        if PYTHON_INITIAL_MIGRATION in existing_versions:
            return "schema_migrations already Python-compatible; no conversion needed"
        return "schema_migrations already Python-compatible; inserted 0001-initial"

    # Legacy Go integer table
    applied_at = conn.execute("SELECT MAX(applied_at) FROM schema_migrations").fetchone()[0]
    if not applied_at:
        applied_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if table_exists(conn, LEGACY_ARCHIVE_TABLE):
        conn.execute(f"DROP TABLE {LEGACY_ARCHIVE_TABLE}")

    conn.execute(f"ALTER TABLE schema_migrations RENAME TO {LEGACY_ARCHIVE_TABLE}")
    conn.execute(
        """
        CREATE TABLE schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        [PYTHON_INITIAL_MIGRATION, applied_at],
    )
    return (
        "converted legacy integer schema_migrations to Python-compatible text table "
        f"and archived the old entries in {LEGACY_ARCHIVE_TABLE}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a legacy Go CashCompass SQLite DB to Python-app compatibility."
    )
    parser.add_argument("db_path", help="Path to the existing CashCompass SQLite DB")
    parser.add_argument(
        "--backup-path",
        help="Optional backup path. Defaults to <db>.pre-python-migration.bak",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup copy before mutating the DB",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path).expanduser().resolve()
    if not db_path.exists():
        print(f"error: database file not found: {db_path}", file=sys.stderr)
        return 1

    backup_path = None
    if not args.no_backup:
        backup_path = (
            Path(args.backup_path).expanduser().resolve()
            if args.backup_path
            else db_path.with_suffix(db_path.suffix + ".pre-python-migration.bak")
        )
        create_backup(db_path, backup_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = 1")

    try:
        validate_expected_tables(conn)
        with conn:
            message = ensure_python_schema_migrations(conn)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    print(f"updated database: {db_path}")
    if backup_path is not None:
        print(f"backup created: {backup_path}")
    print(message)
    print(
        "next step: start the Python app against this DB and verify /healthz and /dashboard "
        "before switching production traffic"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
