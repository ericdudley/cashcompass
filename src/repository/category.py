from __future__ import annotations
from src.db import Database
from src.models import Category
from src.utils.ids import generate_uid


def _row_to_category(row) -> Category:
    return Category(
        id=row["id"],
        uid=row["uid"],
        label=row["label"],
        created_at=row["created_at"] or "",
        updated_at=row["updated_at"] or "",
    )


class CategoryRepository:
    def __init__(self, db: Database):
        self.db = db

    def list(self) -> list[Category]:
        rows = self.db.execute(
            "SELECT id, uid, label, created_at, updated_at FROM categories ORDER BY label ASC"
        ).fetchall()
        return [_row_to_category(r) for r in rows]

    def get_by_id(self, id: int) -> Category:
        row = self.db.execute(
            "SELECT id, uid, label, created_at, updated_at FROM categories WHERE id = ?", [id]
        ).fetchone()
        if row is None:
            raise ValueError(f"category {id} not found")
        return _row_to_category(row)

    def create(self, label: str) -> Category:
        cur = self.db.execute("INSERT INTO categories (uid, label) VALUES (?, ?)", [generate_uid("cat"), label])
        self.db.commit()
        return self.get_by_id(cur.lastrowid)

    def update_label(self, id: int, label: str):
        self.db.execute(
            "UPDATE categories SET label = ?, updated_at = datetime('now') WHERE id = ?", [label, id]
        )
        self.db.commit()

    def delete(self, id: int):
        self.db.execute("DELETE FROM categories WHERE id = ?", [id])
        self.db.commit()
