from __future__ import annotations

from src.db import Database
from src.models import BudgetPlan, MonthlyBudget, MonthlyRolloverChange


class BudgetRepository:
    def __init__(self, db: Database):
        self.db = db

    def list(self, month: str = "") -> list[MonthlyBudget]:
        sql = "SELECT month, category_id, amount_cents FROM monthly_budgets"
        rows = self.db.execute(sql + (" WHERE month = ?" if month else "") + " ORDER BY month, COALESCE(category_id, 0)",
                               [month] if month else []).fetchall()
        return [MonthlyBudget(month=row["month"], category_id=row["category_id"], amount_cents=row["amount_cents"]) for row in rows]

    def save_limits(self, month: str, limits: dict[int | None, int | None]):
        self.save_changes(limits=[MonthlyBudget(month, category_id, amount) for category_id, amount in limits.items()])

    def list_plans(self) -> list[BudgetPlan]:
        return [BudgetPlan(**dict(row)) for row in self.db.execute(
            "SELECT year, category_id, period, annual_amount_cents FROM budget_plans ORDER BY year, COALESCE(category_id, 0)"
        ).fetchall()]

    def list_rollover(self) -> list[MonthlyRolloverChange]:
        return [MonthlyRolloverChange(row["month"], row["category_id"], bool(row["enabled"])) for row in self.db.execute(
            "SELECT month, category_id, enabled FROM monthly_budget_rollover ORDER BY month, COALESCE(category_id, 0)"
        ).fetchall()]

    def save_changes(self, *, limits=(), plans=(), rollover=()):
        try:
            self.db.conn.execute("BEGIN")
            for change in limits:
                self.db.execute("DELETE FROM monthly_budgets WHERE month = ? AND category_id IS ?", [change.month, change.category_id])
                self.db.execute("INSERT INTO monthly_budgets (month, category_id, amount_cents) VALUES (?, ?, ?)",
                                [change.month, change.category_id, change.amount_cents])
            for plan in plans:
                self.db.execute("DELETE FROM budget_plans WHERE year = ? AND category_id IS ?", [plan.year, plan.category_id])
                self.db.execute("INSERT INTO budget_plans (year, category_id, period, annual_amount_cents) VALUES (?, ?, ?, ?)",
                                [plan.year, plan.category_id, plan.period, plan.annual_amount_cents])
            for change in rollover:
                self.db.execute("DELETE FROM monthly_budget_rollover WHERE month = ? AND category_id IS ?", [change.month, change.category_id])
                self.db.execute("INSERT INTO monthly_budget_rollover (month, category_id, enabled) VALUES (?, ?, ?)",
                                [change.month, change.category_id, int(change.enabled)])
            self.db.commit()
        except Exception:
            self.db.conn.rollback()
            raise

    def clear(self):
        self.db.execute("DELETE FROM budget_plans")
        self.db.execute("DELETE FROM monthly_budget_rollover")
        self.db.execute("DELETE FROM monthly_budgets")
        self.db.commit()
