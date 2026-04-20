from __future__ import annotations
from src.db import Database
from src.models import Account
from src.utils.ids import generate_uid


def _row_to_account(row) -> Account:
    return Account(
        id=row["id"],
        uid=row["uid"],
        label=row["label"],
        account_type=row["account_type"],
        is_archived=bool(row["is_archived"]),
        created_at=row["created_at"] or "",
        updated_at=row["updated_at"] or "",
    )


class AccountRepository:
    def __init__(self, db: Database):
        self.db = db

    def list(self) -> list[Account]:
        rows = self.db.execute(
            "SELECT id, uid, label, account_type, is_archived, created_at, updated_at FROM accounts ORDER BY is_archived ASC, label ASC"
        ).fetchall()
        return [_row_to_account(r) for r in rows]

    def get_by_id(self, id: int) -> Account:
        row = self.db.execute(
            "SELECT id, uid, label, account_type, is_archived, created_at, updated_at FROM accounts WHERE id = ?", [id]
        ).fetchone()
        if row is None:
            raise ValueError(f"account {id} not found")
        return _row_to_account(row)

    def create(self, label: str, account_type: str) -> Account:
        cur = self.db.execute(
            "INSERT INTO accounts (uid, label, account_type) VALUES (?, ?, ?)",
            [generate_uid("acct"), label, account_type],
        )
        self.db.commit()
        return self.get_by_id(cur.lastrowid)

    def update_label(self, id: int, label: str):
        self.db.execute(
            "UPDATE accounts SET label = ?, updated_at = datetime('now') WHERE id = ?", [label, id]
        )
        self.db.commit()

    def update_type(self, id: int, account_type: str):
        self.db.execute(
            "UPDATE accounts SET account_type = ?, updated_at = datetime('now') WHERE id = ?", [account_type, id]
        )
        self.db.commit()

    def set_archived(self, id: int, archived: bool):
        self.db.execute(
            "UPDATE accounts SET is_archived = ?, updated_at = datetime('now') WHERE id = ?",
            [1 if archived else 0, id],
        )
        self.db.commit()

    def delete(self, id: int):
        self.db.execute("DELETE FROM accounts WHERE id = ?", [id])
        self.db.commit()
