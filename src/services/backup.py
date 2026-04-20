from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from src.db import Database
from src.repository.account import AccountRepository
from src.repository.category import CategoryRepository
from src.repository.transaction import TransactionRepository

SUPPORTED_FORMAT = "cashcompass.backup"
SUPPORTED_VERSION = 1


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _format_timestamp(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.endswith("Z") or ("T" in raw and ("+" in raw[10:] or "-" in raw[10:])):
        return raw
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    return raw


def _parse_timestamp(value: str, field_name: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    normalized = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    for fmt in ("%Y-%m-%d %H:%M:%S",):
        try:
            dt = datetime.strptime(normalized, fmt).replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name}: {value!r}") from exc
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _require_date(value: str, field_name: str) -> str:
    raw = (value or "").strip()
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"invalid {field_name}: {value!r}") from exc
    return raw


def _require_bool(value, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"{field_name} must be a boolean")


def _require_int(value, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _require_str(value, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


class BackupService:
    def __init__(
        self,
        db: Database,
        acct_repo: AccountRepository,
        cat_repo: CategoryRepository,
        txn_repo: TransactionRepository,
    ):
        self.db = db
        self.acct_repo = acct_repo
        self.cat_repo = cat_repo
        self.txn_repo = txn_repo

    def export_backup(self) -> dict:
        accounts = sorted(self.acct_repo.list(), key=lambda a: a.id)
        categories = sorted(self.cat_repo.list(), key=lambda c: c.id)
        transactions = sorted(self.txn_repo.list_all(), key=lambda t: t.id)

        return {
            "format": SUPPORTED_FORMAT,
            "version": SUPPORTED_VERSION,
            "exported_at": _now_utc(),
            "app": {"name": "CashCompass"},
            "schema": {"entities": ["accounts", "categories", "transactions"]},
            "accounts": [
                {
                    "id": acct.uid,
                    "legacy_numeric_id": acct.id,
                    "label": acct.label,
                    "account_type": acct.account_type,
                    "is_archived": acct.is_archived,
                    "created_at": _format_timestamp(acct.created_at),
                    "updated_at": _format_timestamp(acct.updated_at),
                }
                for acct in accounts
            ],
            "categories": [
                {
                    "id": cat.uid,
                    "legacy_numeric_id": cat.id,
                    "label": cat.label,
                    "created_at": _format_timestamp(cat.created_at),
                    "updated_at": _format_timestamp(cat.updated_at),
                }
                for cat in categories
            ],
            "transactions": [
                {
                    "id": txn.uid,
                    "legacy_numeric_id": txn.id,
                    "occurred_at": txn.iso8601 or txn.date.replace("_", "-"),
                    "amount_cents": txn.amount,
                    "label": txn.label,
                    "account_id": txn.account_uid,
                    "category_id": txn.category_uid,
                    "created_at": _format_timestamp(txn.created_at),
                    "updated_at": _format_timestamp(txn.updated_at),
                }
                for txn in transactions
            ],
        }

    def export_backup_json(self) -> str:
        return json.dumps(self.export_backup(), indent=2, sort_keys=False) + "\n"

    def export_transactions_csv(self) -> str:
        accounts = {acct.id: acct for acct in self.acct_repo.list()}
        transactions = sorted(self.txn_repo.list_all(), key=lambda t: (t.date, t.id), reverse=True)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "transaction_id",
            "date",
            "amount_cents",
            "amount",
            "label",
            "account",
            "account_type",
            "category",
            "archived_account",
        ])

        for txn in transactions:
            acct = accounts.get(txn.account_id) if txn.account_id is not None else None
            writer.writerow([
                txn.uid,
                txn.iso8601 or txn.date.replace("_", "-"),
                txn.amount,
                f"{txn.amount / 100:.2f}",
                txn.label,
                txn.account_label,
                acct.account_type if acct else "",
                txn.category_label,
                "true" if acct and acct.is_archived else "false",
            ])

        return buf.getvalue()

    def parse_backup_upload(self, content: bytes) -> dict:
        try:
            payload = json.loads(content.decode("utf-8"))
        except Exception as exc:
            raise ValueError("invalid backup JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("backup payload must be a JSON object")
        self._validate_backup(payload)
        return payload

    def restore_backup(self, payload: dict) -> dict:
        accounts = payload["accounts"]
        categories = payload["categories"]
        transactions = payload["transactions"]

        account_rows = []
        account_uid_to_id = {}
        for acct in accounts:
            label = _require_str(acct.get("label"), "account label")
            account_type = _require_str(acct.get("account_type"), "account_type")
            if account_type not in ("expenses", "net_worth"):
                raise ValueError(f"unsupported account_type: {account_type}")
            uid = _require_str(acct.get("id"), "account id")
            legacy_id = _require_int(acct.get("legacy_numeric_id"), "account legacy_numeric_id")
            is_archived = _require_bool(acct.get("is_archived"), "account is_archived")
            created_at = _parse_timestamp(acct.get("created_at", ""), "account created_at")
            updated_at = _parse_timestamp(acct.get("updated_at", ""), "account updated_at")
            account_rows.append((legacy_id, uid, label, account_type, 1 if is_archived else 0, created_at, updated_at))
            account_uid_to_id[uid] = legacy_id

        category_rows = []
        category_uid_to_id = {}
        category_uid_to_label = {}
        for cat in categories:
            uid = _require_str(cat.get("id"), "category id")
            legacy_id = _require_int(cat.get("legacy_numeric_id"), "category legacy_numeric_id")
            label = _require_str(cat.get("label"), "category label")
            created_at = _parse_timestamp(cat.get("created_at", ""), "category created_at")
            updated_at = _parse_timestamp(cat.get("updated_at", ""), "category updated_at")
            category_rows.append((legacy_id, uid, label, created_at, updated_at))
            category_uid_to_id[uid] = legacy_id
            category_uid_to_label[uid] = label

        account_uid_to_label = {acct[1]: acct[2] for acct in account_rows}

        transaction_rows = []
        for txn in transactions:
            uid = _require_str(txn.get("id"), "transaction id")
            legacy_id = _require_int(txn.get("legacy_numeric_id"), "transaction legacy_numeric_id")
            occurred_at = _require_date(txn.get("occurred_at"), "occurred_at")
            amount = _require_int(txn.get("amount_cents"), "amount_cents")
            if amount == 0:
                raise ValueError("amount_cents must be non-zero")
            label = _require_str(txn.get("label"), "transaction label")
            account_uid = txn.get("account_id")
            if account_uid is not None:
                account_uid = _require_str(account_uid, "transaction account_id")
            category_uid = txn.get("category_id")
            if category_uid is not None:
                category_uid = _require_str(category_uid, "transaction category_id")

            if account_uid is not None and account_uid not in account_uid_to_id:
                raise ValueError(f"transaction account_id does not resolve: {account_uid}")
            if category_uid is not None and category_uid not in category_uid_to_id:
                raise ValueError(f"transaction category_id does not resolve: {category_uid}")

            created_at = _parse_timestamp(txn.get("created_at", ""), "transaction created_at")
            updated_at = _parse_timestamp(txn.get("updated_at", ""), "transaction updated_at")

            transaction_rows.append((
                legacy_id,
                uid,
                occurred_at,
                occurred_at.replace("-", "_"),
                amount,
                label,
                account_uid_to_id.get(account_uid) if account_uid is not None else None,
                account_uid_to_label.get(account_uid, ""),
                category_uid_to_id.get(category_uid) if category_uid is not None else None,
                category_uid_to_label.get(category_uid, ""),
                created_at,
                updated_at,
            ))

        try:
            self.db.conn.execute("BEGIN")
            self.db.execute("DELETE FROM transactions")
            self.db.execute("DELETE FROM categories")
            self.db.execute("DELETE FROM accounts")
            self.db.execute("DELETE FROM sqlite_sequence WHERE name IN ('transactions','categories','accounts')")

            self.db.conn.executemany(
                """
                INSERT INTO accounts (id, uid, label, account_type, is_archived, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                account_rows,
            )
            self.db.conn.executemany(
                """
                INSERT INTO categories (id, uid, label, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                category_rows,
            )
            self.db.conn.executemany(
                """
                INSERT INTO transactions (
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                transaction_rows,
            )
            self.db.commit()
        except Exception:
            self.db.conn.rollback()
            raise

        return {
            "accounts": len(account_rows),
            "categories": len(category_rows),
            "transactions": len(transaction_rows),
        }

    def _validate_backup(self, payload: dict):
        if payload.get("format") != SUPPORTED_FORMAT:
            raise ValueError("unsupported backup format")
        if payload.get("version") != SUPPORTED_VERSION:
            raise ValueError("unsupported backup version")

        for field in ("accounts", "categories", "transactions"):
            if not isinstance(payload.get(field), list):
                raise ValueError(f"{field} must be an array")

        self._validate_unique_ids(payload["accounts"], "accounts")
        self._validate_unique_ids(payload["categories"], "categories")
        self._validate_unique_ids(payload["transactions"], "transactions")
        self._validate_unique_legacy_ids(payload["accounts"], "accounts")
        self._validate_unique_legacy_ids(payload["categories"], "categories")
        self._validate_unique_legacy_ids(payload["transactions"], "transactions")

    @staticmethod
    def _validate_unique_ids(records: list[dict], field_name: str):
        seen = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise ValueError(f"{field_name}[{index}] must be an object")
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id.strip():
                raise ValueError(f"{field_name}[{index}].id must be a non-empty string")
            if record_id in seen:
                raise ValueError(f"duplicate {field_name} id: {record_id}")
            seen.add(record_id)

    @staticmethod
    def _validate_unique_legacy_ids(records: list[dict], field_name: str):
        seen = set()
        for index, record in enumerate(records):
            legacy_id = record.get("legacy_numeric_id")
            if isinstance(legacy_id, bool) or not isinstance(legacy_id, int):
                raise ValueError(f"{field_name}[{index}].legacy_numeric_id must be an integer")
            if legacy_id in seen:
                raise ValueError(f"duplicate {field_name} legacy_numeric_id: {legacy_id}")
            seen.add(legacy_id)
