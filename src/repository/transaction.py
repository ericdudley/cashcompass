from __future__ import annotations
from typing import Optional
from src.db import Database
from src.models import Transaction, TransactionFilter, MonthSum, AccountMonthBalance

_COLS = "id, iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label, created_at, updated_at"


def _row_to_txn(row) -> Transaction:
    return Transaction(
        id=row["id"],
        iso8601=row["iso8601"] or "",
        date=row["yyyy_mm_dd"] or "",
        amount=row["amount"],
        label=row["label"] or "",
        account_id=row["account_id"],
        account_label=row["account_label"] or "",
        category_id=row["category_id"],
        category_label=row["category_label"] or "",
        created_at=row["created_at"] or "",
        updated_at=row["updated_at"] or "",
    )


class TransactionRepository:
    def __init__(self, db: Database):
        self.db = db

    def list(self, f: TransactionFilter) -> list[Transaction]:
        sql = f"SELECT {_COLS} FROM transactions WHERE 1=1"
        args = []

        if f.date_from:
            sql += " AND yyyy_mm_dd >= ?"
            args.append(f.date_from)
        if f.date_to:
            sql += " AND yyyy_mm_dd <= ?"
            args.append(f.date_to)
        if f.label:
            sql += " AND label LIKE ?"
            args.append(f"%{f.label}%")
        if f.account_ids:
            placeholders = ",".join("?" * len(f.account_ids))
            sql += f" AND account_id IN ({placeholders})"
            args.extend(f.account_ids)
        if f.category_ids:
            placeholders = ",".join("?" * len(f.category_ids))
            sql += f" AND category_id IN ({placeholders})"
            args.extend(f.category_ids)
        if f.account_type:
            sql += " AND account_id IN (SELECT id FROM accounts WHERE account_type = ?)"
            args.append(f.account_type)

        sql += " ORDER BY yyyy_mm_dd DESC, id DESC"
        rows = self.db.execute(sql, args).fetchall()
        return [_row_to_txn(r) for r in rows]

    def get_by_id(self, id: int) -> Transaction:
        row = self.db.execute(
            f"SELECT {_COLS} FROM transactions WHERE id = ?", [id]
        ).fetchone()
        if row is None:
            raise ValueError(f"transaction {id} not found")
        return _row_to_txn(row)

    def create(self, iso8601: str, date: str, amount: int, label: str,
               account_id: Optional[int], account_label: str,
               category_id: Optional[int], category_label: str) -> Transaction:
        cur = self.db.execute(
            "INSERT INTO transactions (iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [iso8601, date, amount, label, account_id, account_label, category_id, category_label],
        )
        self.db.commit()
        return self.get_by_id(cur.lastrowid)

    def update_amount(self, id: int, amount: int):
        self.db.execute("UPDATE transactions SET amount = ?, updated_at = datetime('now') WHERE id = ?", [amount, id])
        self.db.commit()

    def update_label(self, id: int, label: str):
        self.db.execute("UPDATE transactions SET label = ?, updated_at = datetime('now') WHERE id = ?", [label, id])
        self.db.commit()

    def update_account(self, id: int, account_id: Optional[int], account_label: str):
        self.db.execute(
            "UPDATE transactions SET account_id = ?, account_label = ?, updated_at = datetime('now') WHERE id = ?",
            [account_id, account_label, id],
        )
        self.db.commit()

    def update_category(self, id: int, category_id: Optional[int], category_label: str):
        self.db.execute(
            "UPDATE transactions SET category_id = ?, category_label = ?, updated_at = datetime('now') WHERE id = ?",
            [category_id, category_label, id],
        )
        self.db.commit()

    def update_date(self, id: int, iso8601: str, date: str):
        self.db.execute(
            "UPDATE transactions SET iso8601 = ?, yyyy_mm_dd = ?, updated_at = datetime('now') WHERE id = ?",
            [iso8601, date, id],
        )
        self.db.commit()

    def delete(self, id: int):
        self.db.execute("DELETE FROM transactions WHERE id = ?", [id])
        self.db.commit()

    def sum_by_month(self, account_type: str, date_from: str = "", date_to: str = "") -> list[MonthSum]:
        sql = """
            SELECT replace(substr(t.yyyy_mm_dd, 1, 7), '_', '-') AS month, SUM(t.amount) AS total
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            WHERE a.account_type = ?
        """
        args = [account_type]
        if date_from:
            sql += " AND t.yyyy_mm_dd >= ?"
            args.append(date_from)
        if date_to:
            sql += " AND t.yyyy_mm_dd <= ?"
            args.append(date_to)
        sql += " GROUP BY month ORDER BY month DESC"
        rows = self.db.execute(sql, args).fetchall()
        return [MonthSum(month=r["month"], amount=r["total"]) for r in rows]

    def balances_by_month(self, account_ids: list[int]) -> list[AccountMonthBalance]:
        if not account_ids:
            return []
        placeholders = ",".join("?" * len(account_ids))
        sql = f"""
            SELECT account_id, account_label, replace(substr(yyyy_mm_dd, 1, 7), '_', '-') AS month, SUM(amount) AS monthly_sum
            FROM transactions
            WHERE account_id IN ({placeholders})
            GROUP BY account_id, month
            ORDER BY account_id, month
        """
        rows = self.db.execute(sql, account_ids).fetchall()

        cumulative = {}
        result = []
        for r in rows:
            aid = r["account_id"]
            cumulative[aid] = cumulative.get(aid, 0) + r["monthly_sum"]
            result.append(AccountMonthBalance(
                account_id=aid,
                account_label=r["account_label"] or "",
                month=r["month"],
                balance=cumulative[aid],
            ))
        return result

    def sync_account_label(self, account_id: int, label: str):
        self.db.execute(
            "UPDATE transactions SET account_label = ?, updated_at = datetime('now') WHERE account_id = ?",
            [label, account_id],
        )
        self.db.commit()

    def sync_category_label(self, category_id: int, label: str):
        self.db.execute(
            "UPDATE transactions SET category_label = ?, updated_at = datetime('now') WHERE category_id = ?",
            [label, category_id],
        )
        self.db.commit()

    def clear_category(self, category_id: int):
        self.db.execute(
            "UPDATE transactions SET category_id = NULL, category_label = '', updated_at = datetime('now') WHERE category_id = ?",
            [category_id],
        )
        self.db.commit()
