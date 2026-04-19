from __future__ import annotations
from src.models import Account
from src.repository.account import AccountRepository
from src.repository.transaction import TransactionRepository


class AccountService:
    def __init__(self, repo: AccountRepository, txn_repo: TransactionRepository):
        self.repo = repo
        self.txn_repo = txn_repo

    @staticmethod
    def _normalize_label(label: str) -> str:
        normalized = label.strip()
        if not normalized:
            raise ValueError("account label is required")
        return normalized

    def list(self) -> list[Account]:
        return self.repo.list()

    def get_by_id(self, id: int) -> Account:
        return self.repo.get_by_id(id)

    def create(self, label: str, account_type: str) -> Account:
        return self.repo.create(self._normalize_label(label), account_type)

    def update_label(self, id: int, label: str):
        label = self._normalize_label(label)
        self.repo.update_label(id, label)
        self.txn_repo.sync_account_label(id, label)

    def update_type(self, id: int, account_type: str):
        self.repo.update_type(id, account_type)

    def toggle_archived(self, id: int) -> Account:
        acct = self.repo.get_by_id(id)
        self.repo.set_archived(id, not acct.is_archived)
        return self.repo.get_by_id(id)

    def delete(self, id: int):
        self.repo.delete(id)
