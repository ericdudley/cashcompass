from src.db import Database
from src.models import MonthlyBudget


class BudgetRepository:
    def __init__(self, db: Database):
        self.db = db

    def list(self, month: str = "") -> list[MonthlyBudget]:
        sql = "SELECT month, category_id, amount_cents FROM monthly_budgets"
        rows = self.db.execute(sql + (" WHERE month = ?" if month else "") + " ORDER BY month, COALESCE(category_id, 0)",
                               [month] if month else []).fetchall()
        return [MonthlyBudget(month=row["month"], category_id=row["category_id"], amount_cents=row["amount_cents"]) for row in rows]

    def save_limits(self, month: str, limits: dict[int | None, int | None]):
        try:
            self.db.conn.execute("BEGIN")
            for category_id, amount in limits.items():
                self.db.execute("DELETE FROM monthly_budgets WHERE month = ? AND category_id IS ?", [month, category_id])
                if amount is not None:
                    self.db.execute("INSERT INTO monthly_budgets (month, category_id, amount_cents) VALUES (?, ?, ?)",
                                    [month, category_id, amount])
            self.db.commit()
        except Exception:
            self.db.conn.rollback()
            raise

    def clear(self):
        self.db.execute("DELETE FROM monthly_budgets")
        self.db.commit()
