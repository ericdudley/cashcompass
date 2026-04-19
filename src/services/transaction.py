from __future__ import annotations
from datetime import datetime
from typing import Optional
from src.models import Transaction, TransactionFilter, MonthSum, AccountMonthBalance
from src.repository.transaction import TransactionRepository


class TransactionService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    @staticmethod
    def _normalize_label(label: str) -> str:
        normalized = label.strip()
        if not normalized:
            raise ValueError("transaction label is required")
        return normalized

    @staticmethod
    def _normalize_amount(amount: int) -> int:
        if amount == 0:
            raise ValueError("transaction amount must be non-zero")
        return amount

    @staticmethod
    def _normalize_date(iso8601: str, date: str) -> tuple[str, str]:
        iso_date = (iso8601 or "").strip()[:10]
        storage_date = (date or "").strip()
        if not iso_date or not storage_date:
            raise ValueError("transaction date is required")
        try:
            datetime.strptime(iso_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("transaction date must be YYYY-MM-DD") from exc
        if storage_date != iso_date.replace("-", "_"):
            raise ValueError("transaction date is invalid")
        return iso_date, storage_date

    @staticmethod
    def _require_account(account_id: Optional[int], account_label: str) -> tuple[int, str]:
        if account_id is None or not account_label.strip():
            raise ValueError("transaction account is required")
        return account_id, account_label.strip()

    def list(self, f: TransactionFilter) -> list[Transaction]:
        return self.repo.list(f)

    def get_by_id(self, id: int) -> Transaction:
        return self.repo.get_by_id(id)

    def create(self, iso8601: str, date: str, amount: int, label: str,
               account_id: Optional[int], account_label: str,
               category_id: Optional[int], category_label: str) -> Transaction:
        iso8601, date = self._normalize_date(iso8601, date)
        label = self._normalize_label(label)
        amount = self._normalize_amount(amount)
        account_id, account_label = self._require_account(account_id, account_label)
        return self.repo.create(iso8601, date, amount, label, account_id, account_label, category_id, category_label)

    def update_amount(self, id: int, amount: int):
        self.repo.update_amount(id, self._normalize_amount(amount))

    def update_label(self, id: int, label: str):
        self.repo.update_label(id, self._normalize_label(label))

    def update_account(self, id: int, account_id: Optional[int], account_label: str):
        account_id, account_label = self._require_account(account_id, account_label)
        self.repo.update_account(id, account_id, account_label)

    def update_category(self, id: int, category_id: Optional[int], category_label: str):
        self.repo.update_category(id, category_id, category_label)

    def update_date(self, id: int, iso8601: str, date: str):
        iso8601, date = self._normalize_date(iso8601, date)
        self.repo.update_date(id, iso8601, date)

    def delete(self, id: int):
        self.repo.delete(id)

    def sum_by_month(self, account_type: str, date_from: str = "", date_to: str = "") -> list[MonthSum]:
        return self.repo.sum_by_month(account_type, date_from, date_to)

    def balances_by_month(self, account_ids: list[int]) -> list[AccountMonthBalance]:
        return self.repo.balances_by_month(account_ids)
