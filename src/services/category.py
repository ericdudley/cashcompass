from __future__ import annotations
from src.models import Category
from src.repository.category import CategoryRepository
from src.repository.transaction import TransactionRepository


class CategoryService:
    def __init__(self, repo: CategoryRepository, txn_repo: TransactionRepository):
        self.repo = repo
        self.txn_repo = txn_repo

    @staticmethod
    def _normalize_label(label: str) -> str:
        normalized = label.strip()
        if not normalized:
            raise ValueError("category label is required")
        return normalized

    def list(self) -> list[Category]:
        return self.repo.list()

    def get_by_id(self, id: int) -> Category:
        return self.repo.get_by_id(id)

    def create(self, label: str) -> Category:
        return self.repo.create(self._normalize_label(label))

    def update_label(self, id: int, label: str):
        label = self._normalize_label(label)
        self.repo.update_label(id, label)
        self.txn_repo.sync_category_label(id, label)

    def delete(self, id: int):
        self.txn_repo.clear_category(id)
        self.repo.delete(id)
