from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from decimal import Decimal, DecimalException
from typing import Callable
from urllib.parse import urlencode

from src.models import Category, CategoryBreakdown, CategoryTotal, Transaction, TransactionFilter
from src.repository.budget import BudgetRepository
from src.services.category import CategoryService
from src.services.transaction import TransactionService
from src.utils.dates import local_today


def category_breakdown(txns: list[Transaction], categories: list[Category] | None = None) -> CategoryBreakdown:
    """Group by identity, preserving credits and uncategorized activity."""
    totals = {c.id: CategoryTotal(category_id=c.id, label=c.label) for c in categories or []}
    for txn in txns:
        key = txn.category_id
        if key not in totals:
            totals[key] = CategoryTotal(category_id=key, label=(txn.category_label or "Uncategorized") if key is not None else "Uncategorized")
        row = totals[key]
        row.spending += max(-txn.amount, 0)
        row.credits += max(txn.amount, 0)
        row.count += 1
    rows = sorted(totals.values(), key=lambda row: (-row.net_expenses, row.label.casefold(), row.category_id or 0))
    return CategoryBreakdown(
        rows=rows,
        spending=sum(row.spending for row in rows),
        credits=sum(row.credits for row in rows),
        count=sum(row.count for row in rows),
    )


def month_bounds(month: str) -> tuple[str, str]:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("month must be YYYY-MM")
    try:
        first = datetime.strptime(month, "%Y-%m").date()
    except ValueError as exc:
        raise ValueError("month must be a valid YYYY-MM") from exc
    last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
    return f"{first.year:04d}_{first.month:02d}_01", f"{last.year:04d}_{last.month:02d}_{last.day:02d}"


def adjacent_month(month: str, offset: int) -> str:
    year, number = map(int, month.split("-"))
    year, number = divmod(year * 12 + number - 1 + offset, 12)
    return f"{year:04d}-{number + 1:02d}" if 1 <= year <= 9999 else ""


def transactions_url(month: str, category_id: int | None = None, *, category_filter: bool = False) -> str:
    first, last = month_bounds(month)
    params = {
        "account_type": "expenses",
        "date_preset": "custom",
        "date_from": first.replace("_", "-"),
        "date_to": last.replace("_", "-"),
    }
    if category_filter:
        params["category_id"] = str(category_id or 0)
    return "/transactions?" + urlencode(params)


class BudgetService:
    def __init__(self, txn_svc: TransactionService, cat_svc: CategoryService, repo: BudgetRepository,
                 today_fn: Callable[[], date] = local_today):
        self.txn_svc = txn_svc
        self.cat_svc = cat_svc
        self.repo = repo
        self.today_fn = today_fn

    def save_limits(self, month: str, raw_limits: dict[int, str]):
        month_bounds(month)
        valid_ids = {category.id for category in self.cat_svc.list()} | {0}
        normalized = {}
        for category_id, raw in raw_limits.items():
            if category_id not in valid_ids:
                raise ValueError("budget category is invalid")
            normalized[category_id or None] = parse_budget_limit(raw)
        self.repo.save_limits(month, normalized)

    def clear_limits(self):
        self.repo.clear()

    def build(self, requested_month: str = "") -> dict:
        month = requested_month or self.today_fn().strftime("%Y-%m")
        first, last = month_bounds(month)
        previous = adjacent_month(month, -1)
        next_month = adjacent_month(month, 1)
        current = category_breakdown(self.txn_svc.list(TransactionFilter(
            date_from=first, date_to=last, account_type="expenses",
        )), self.cat_svc.list())
        limits = {limit.category_id: limit.amount_cents for limit in self.repo.list(month)}
        if not any(row.category_id is None for row in current.rows):
            current.rows.append(CategoryTotal(label="Uncategorized"))
        prior = CategoryBreakdown()
        if previous:
            prev_first, prev_last = month_bounds(previous)
            prior = category_breakdown(self.txn_svc.list(TransactionFilter(
                date_from=prev_first, date_to=prev_last, account_type="expenses",
            )))
        return {
            "month": month,
            "month_label": datetime.strptime(month, "%Y-%m").strftime("%B %Y"),
            "previous_month": previous,
            "next_month": next_month,
            "breakdown": current,
            "previous_breakdown": prior,
            "transactions_url": transactions_url(month),
            "limits": limits,
            "total_limits": sum(limits.values()),
            "budgeted_expenses": sum(row.net_expenses for row in current.rows if row.category_id in limits),
        }


def parse_budget_limit(raw: str) -> int | None:
    if not raw.strip():
        return None
    try:
        amount = Decimal(raw.strip())
        if not amount.is_finite() or amount < 0 or amount > Decimal(2**63 - 1) / 100 or amount != amount.quantize(Decimal("0.01")):
            raise ValueError("budget limits must be non-negative amounts with at most two decimal places")
        cents = amount * 100
        return int(cents)
    except (DecimalException, ValueError) as exc:
        raise ValueError("budget limits must be non-negative amounts with at most two decimal places") from exc
