from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from src.db import Database
from src.repository.account import AccountRepository
from src.repository.annual_income import AnnualIncomeRepository
from src.repository.budget import BudgetRepository
from src.repository.category import CategoryRepository
from src.repository.transaction import TransactionRepository
from src.services.budget import month_bounds

SUPPORTED_FORMAT = "cashcompass.backup"
SUPPORTED_VERSION = 5
IMPORTABLE_VERSIONS = {1, 2, 3, 4, 5}


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


def _parse_occurred_at(value, field_name: str) -> str:
    """Return a transaction's calendar date from canonical or legacy input.

    Backups represent when a transaction occurred as a date.  Older data may
    contain an ISO-8601 timestamp in this field, so retain the date written in
    that timestamp rather than converting it across time zones.
    """
    if not isinstance(value, str):
        raise ValueError(f"invalid {field_name}: {value!r}")
    raw = value.strip()
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        pass

    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        occurred_at = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name}: {value!r}") from exc
    return occurred_at.date().isoformat()


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
        income_repo: AnnualIncomeRepository,
        budget_repo: BudgetRepository,
    ):
        self.db = db
        self.acct_repo = acct_repo
        self.cat_repo = cat_repo
        self.txn_repo = txn_repo
        self.income_repo = income_repo
        self.budget_repo = budget_repo

    def export_backup(self) -> dict:
        accounts = sorted(self.acct_repo.list(), key=lambda a: a.id)
        categories = sorted(self.cat_repo.list(), key=lambda c: c.id)
        transactions = sorted(self.txn_repo.list_all(), key=lambda t: t.id)
        annual_incomes = sorted(self.income_repo.list(), key=lambda income: income.tax_year)
        category_uids = {category.id: category.uid for category in categories}

        return {
            "format": SUPPORTED_FORMAT,
            "version": SUPPORTED_VERSION,
            "exported_at": _now_utc(),
            "app": {"name": "CashCompass"},
            "schema": {"entities": ["accounts", "categories", "transactions", "annual_incomes", "monthly_budgets", "budget_plans", "monthly_budget_rollover"]},
            "budget_plans": [
                {"year": plan.year, "category_id": category_uids.get(plan.category_id), "period": plan.period,
                 "annual_amount_cents": plan.annual_amount_cents} for plan in self.budget_repo.list_plans()
            ],
            "monthly_budget_rollover": [
                {"month": change.month, "category_id": category_uids.get(change.category_id), "enabled": change.enabled}
                for change in self.budget_repo.list_rollover()
            ],
            "monthly_budgets": [
                {"month": budget.month, "category_id": category_uids.get(budget.category_id), "amount_cents": budget.amount_cents}
                for budget in self.budget_repo.list()
            ],
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
            "annual_incomes": [
                {
                    "id": income.uid,
                    "legacy_numeric_id": income.id,
                    "tax_year": income.tax_year,
                    "gross_income_cents": income.gross_income_cents,
                    "federal_tax_cents": income.federal_tax_cents,
                    "state_tax_cents": income.state_tax_cents,
                    "notes": income.notes,
                    "created_at": _format_timestamp(income.created_at),
                    "updated_at": _format_timestamp(income.updated_at),
                }
                for income in annual_incomes
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
        self._validate_backup(payload)
        accounts = payload["accounts"]
        categories = payload["categories"]
        transactions = payload["transactions"]
        annual_incomes = payload.get("annual_incomes", [])
        monthly_budgets = payload.get("monthly_budgets", []) if payload["version"] >= 3 else []

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
            occurred_at = _parse_occurred_at(txn.get("occurred_at"), "occurred_at")
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

        annual_income_rows = []
        annual_income_years = set()
        for income in annual_incomes:
            uid = _require_str(income.get("id"), "annual income id")
            legacy_id = _require_int(income.get("legacy_numeric_id"), "annual income legacy_numeric_id")
            tax_year = _require_int(income.get("tax_year"), "annual income tax_year")
            gross_income = _require_int(income.get("gross_income_cents"), "annual income gross_income_cents")
            federal_tax = _require_int(income.get("federal_tax_cents"), "annual income federal_tax_cents")
            state_tax = _require_int(income.get("state_tax_cents"), "annual income state_tax_cents")
            notes = income.get("notes", "")
            if not isinstance(notes, str):
                raise ValueError("annual income notes must be a string")
            if not 1900 <= tax_year <= 9999:
                raise ValueError("annual income tax_year must be between 1900 and 9999")
            if tax_year in annual_income_years:
                raise ValueError(f"duplicate annual income tax_year: {tax_year}")
            if gross_income <= 0:
                raise ValueError("annual income gross_income_cents must be greater than zero")
            if federal_tax < 0 or state_tax < 0:
                raise ValueError("annual income tax amounts cannot be negative")
            if federal_tax + state_tax > gross_income:
                raise ValueError("annual income taxes cannot exceed gross income")
            annual_income_years.add(tax_year)
            created_at = _parse_timestamp(income.get("created_at", ""), "annual income created_at")
            updated_at = _parse_timestamp(income.get("updated_at", ""), "annual income updated_at")
            annual_income_rows.append((
                legacy_id,
                uid,
                tax_year,
                gross_income,
                federal_tax,
                state_tax,
                notes.strip(),
                created_at,
                updated_at,
            ))

        budget_rows = []
        budget_keys = set()
        for budget in monthly_budgets:
            if not isinstance(budget, dict):
                raise ValueError("monthly budget must be an object")
            month = _require_str(budget.get("month"), "budget month")
            month_bounds(month)
            if "amount_cents" not in budget:
                raise ValueError("budget amount_cents is required")
            amount = budget["amount_cents"]
            if amount is not None or payload["version"] < 4:
                amount = _require_int(amount, "budget amount_cents")
                if not 0 <= amount <= 2**63 - 1:
                    raise ValueError("budget amount_cents must be a non-negative SQLite integer")
            category_uid = budget.get("category_id")
            if category_uid is not None:
                category_uid = _require_str(category_uid, "budget category_id")
                if category_uid not in category_uid_to_id:
                    raise ValueError(f"budget category_id does not resolve: {category_uid}")
            key = (month, category_uid)
            if key in budget_keys:
                raise ValueError("duplicate monthly budget category")
            budget_keys.add(key)
            budget_rows.append((month, category_uid_to_id.get(category_uid), amount))

        def budget_category(record):
            uid = record.get("category_id")
            if uid is not None:
                uid = _require_str(uid, "budget category_id")
                if uid not in category_uid_to_id:
                    raise ValueError("budget category_id does not resolve")
            return category_uid_to_id.get(uid)

        plan_rows, rollover_rows = [], []
        plan_keys, rollover_keys = set(), set()
        if payload["version"] >= 5:
            for plan in payload["budget_plans"]:
                if not isinstance(plan, dict):
                    raise ValueError("budget plan must be an object")
                year = _require_int(plan.get("year"), "budget plan year")
                if not 1 <= year <= 9999 or plan.get("period") not in ("monthly", "annual"):
                    raise ValueError("invalid budget plan year or period")
                if "annual_amount_cents" not in plan:
                    raise ValueError("annual_amount_cents is required")
                amount = plan["annual_amount_cents"]
                if amount is not None:
                    amount = _require_int(amount, "annual_amount_cents")
                    if not 0 <= amount <= 2**63 - 1 or plan["period"] != "annual":
                        raise ValueError("invalid annual budget amount")
                category_id = budget_category(plan)
                key = (year, category_id)
                if key in plan_keys:
                    raise ValueError("duplicate budget plan")
                plan_keys.add(key)
                plan_rows.append((year, category_id, plan["period"], amount))
            for change in payload["monthly_budget_rollover"]:
                if not isinstance(change, dict):
                    raise ValueError("rollover change must be an object")
                month = _require_str(change.get("month"), "rollover month")
                month_bounds(month)
                category_id = budget_category(change)
                enabled = _require_bool(change.get("enabled"), "rollover enabled")
                key = (month, category_id)
                if key in rollover_keys:
                    raise ValueError("duplicate rollover change")
                rollover_keys.add(key)
                rollover_rows.append((month, category_id, int(enabled)))
        else:
            earliest = {}
            for month, category_id, _ in budget_rows:
                earliest[category_id] = min(month, earliest.get(category_id, month))
            plan_rows = [(int(month[:4]), key, "monthly", None) for key, month in earliest.items()]
            rollover_rows = [(month, key, 1) for key, month in earliest.items()]

        try:
            self.db.conn.execute("BEGIN")
            self.db.execute("DELETE FROM budget_plans")
            self.db.execute("DELETE FROM monthly_budget_rollover")
            self.db.execute("DELETE FROM monthly_budgets")
            self.db.execute("DELETE FROM annual_incomes")
            self.db.execute("DELETE FROM transactions")
            self.db.execute("DELETE FROM categories")
            self.db.execute("DELETE FROM accounts")
            self.db.execute("DELETE FROM sqlite_sequence WHERE name IN ('annual_incomes','transactions','categories','accounts')")

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
                "INSERT INTO monthly_budgets (month, category_id, amount_cents) VALUES (?, ?, ?)", budget_rows,
            )
            self.db.conn.executemany(
                "INSERT INTO budget_plans (year, category_id, period, annual_amount_cents) VALUES (?, ?, ?, ?)", plan_rows,
            )
            self.db.conn.executemany(
                "INSERT INTO monthly_budget_rollover (month, category_id, enabled) VALUES (?, ?, ?)", rollover_rows,
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
            self.db.conn.executemany(
                """
                INSERT INTO annual_incomes (
                    id,
                    uid,
                    tax_year,
                    gross_income_cents,
                    federal_tax_cents,
                    state_tax_cents,
                    notes,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                annual_income_rows,
            )
            self.db.commit()
        except Exception:
            self.db.conn.rollback()
            raise

        return {
            "accounts": len(account_rows),
            "categories": len(category_rows),
            "transactions": len(transaction_rows),
            "annual_incomes": len(annual_income_rows),
            "monthly_budgets": len(budget_rows),
            "budget_plans": len(plan_rows),
            "monthly_budget_rollover": len(rollover_rows),
        }

    def _validate_backup(self, payload: dict):
        if payload.get("format") != SUPPORTED_FORMAT:
            raise ValueError("unsupported backup format")
        version = payload.get("version")
        if isinstance(version, bool) or not isinstance(version, int) or version not in IMPORTABLE_VERSIONS:
            raise ValueError("unsupported backup version")

        for field in ("accounts", "categories", "transactions"):
            if not isinstance(payload.get(field), list):
                raise ValueError(f"{field} must be an array")

        if version >= 2 and not isinstance(payload.get("annual_incomes"), list):
            raise ValueError("annual_incomes must be an array")
        if version >= 3 and not isinstance(payload.get("monthly_budgets"), list):
            raise ValueError("monthly_budgets must be an array")
        if version >= 5:
            for field in ("budget_plans", "monthly_budget_rollover"):
                if not isinstance(payload.get(field), list):
                    raise ValueError(f"{field} must be an array")

        self._validate_unique_ids(payload["accounts"], "accounts")
        self._validate_unique_ids(payload["categories"], "categories")
        self._validate_unique_ids(payload["transactions"], "transactions")
        self._validate_unique_legacy_ids(payload["accounts"], "accounts")
        self._validate_unique_legacy_ids(payload["categories"], "categories")
        self._validate_unique_legacy_ids(payload["transactions"], "transactions")
        if version >= 2:
            self._validate_unique_ids(payload["annual_incomes"], "annual_incomes")
            self._validate_unique_legacy_ids(payload["annual_incomes"], "annual_incomes")

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
