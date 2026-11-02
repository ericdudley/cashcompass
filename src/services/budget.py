from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from decimal import Decimal, DecimalException
from typing import Callable
from urllib.parse import urlencode

from src.models import BudgetPlan, MonthlyBudget, MonthlyRolloverChange, Category, CategoryBreakdown, CategoryTotal, Transaction, TransactionFilter
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


def transactions_url(month: str, category_id: int | None = None, *, category_filter: bool = False,
                     date_from: str = "", date_to: str = "") -> str:
    first, last = month_bounds(month)
    params = {
        "account_type": "expenses", "date_preset": "custom",
        "date_from": date_from or first.replace("_", "-"),
        "date_to": date_to or last.replace("_", "-"),
    }
    if category_filter:
        params["category_id"] = str(category_id or 0)
    return "/transactions?" + urlencode(params)


def budget_year(raw: str | int) -> int:
    if isinstance(raw, bool) or not isinstance(raw, (str, int)) or (isinstance(raw, str) and not re.fullmatch(r"\d{1,4}", raw)):
        raise ValueError("year must be YYYY")
    try:
        year = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("year must be YYYY") from exc
    if not 1 <= year <= 9999:
        raise ValueError("year must be between 0001 and 9999")
    return year


def budget_segments(contribution: int, rollover: int, spent: int) -> dict:
    """Allocate the bar without negative widths or changing its scale on overspend."""
    available = max(0, contribution + rollover)
    base = max(0, contribution + min(rollover, 0))
    reserve = max(0, rollover)
    used = max(0, spent)
    parts = [
        ("spent", "Spent", min(used, available)),
        ("monthly", "Monthly remaining", max(0, base - used)),
        ("rollover", "Rollover remaining", max(0, reserve - max(0, used - base))),
    ]
    return {
        "segments": [{"key": key, "label": label, "amount": amount, "percent": amount * 100 / available}
                     for key, label, amount in parts if amount > 0 and available > 0],
        "boundary": contribution * 100 / available if rollover > 0 and contribution > 0 else None,
    }


class BudgetService:
    def __init__(self, txn_svc: TransactionService, cat_svc: CategoryService, repo: BudgetRepository,
                 today_fn: Callable[[], date] = local_today):
        self.txn_svc, self.cat_svc, self.repo, self.today_fn = txn_svc, cat_svc, repo, today_fn

    def validate_category(self, category_id: int):
        if category_id == 0:
            return None
        if category_id not in {category.id for category in self.cat_svc.list()}:
            raise ValueError("budget category is invalid")
        return category_id

    def _plan(self, category_id: int | None, year: int, plans=None) -> BudgetPlan:
        result = BudgetPlan(year, category_id)
        for plan in self.repo.list_plans() if plans is None else plans:
            if plan.category_id == category_id and plan.year <= year:
                result = plan
        return result

    def _contribution(self, category_id, month, changes=None):
        amount = None
        for change in self.repo.list() if changes is None else changes:
            if change.category_id == category_id and change.month <= month:
                amount = change.amount_cents
        return amount

    def _rollover_enabled(self, category_id, month, changes=None):
        enabled = False
        for change in self.repo.list_rollover() if changes is None else changes:
            if change.category_id == category_id and change.month <= month:
                enabled = change.enabled
        return enabled

    def save_limits(self, month: str, raw_limits: dict[int, str]):
        month_bounds(month)
        normalized = {}
        for raw_id, raw in raw_limits.items():
            category_id = self.validate_category(raw_id)
            if self._plan(category_id, int(month[:4])).period == "annual":
                raise ValueError("annual categories must be edited using their annual budget")
            amount = parse_budget_limit(raw)
            if amount != self._contribution(category_id, month):
                normalized[category_id] = amount
        if normalized:
            self.repo.save_limits(month, normalized)

    def save_category(self, category_id: int, month: str, period: str, raw_amount: str, rollover: bool):
        month_bounds(month)
        category_id = self.validate_category(category_id)
        year = int(month[:4])
        if period not in ("monthly", "annual") or not isinstance(rollover, bool):
            raise ValueError("invalid budget type or rollover setting")
        amount = parse_budget_limit(raw_amount)
        previous = self._plan(category_id, year)
        switching = previous.period != period
        if switching and amount is None:
            raise ValueError("enter an amount when changing budget type")
        plans, limits, changes = [], [], []
        if period == "annual":
            if switching or amount != previous.annual_amount_cents:
                plans.append(BudgetPlan(year, category_id, period, amount))
        else:
            if switching:
                plans.append(BudgetPlan(year, category_id, period))
            effective = f"{year:04d}-01" if switching else month
            if amount != self._contribution(category_id, effective):
                limits.append(MonthlyBudget(effective, category_id, amount))
            if rollover != self._rollover_enabled(category_id, month):
                changes.append(MonthlyRolloverChange(month, category_id, rollover))
        if plans or limits or changes:
            self.repo.save_changes(plans=plans, limits=limits, rollover=changes)

    def clear_limits(self):
        self.repo.clear()

    def _transactions(self, start: date, end: date | None):
        if end is None or end < start:
            return []
        return self.txn_svc.list(TransactionFilter(date_from=start.isoformat().replace("-", "_"),
                              date_to=end.isoformat().replace("-", "_"), account_type="expenses"))

    def build(self, requested_month: str = "", *, view: str = "monthly", requested_year: str = "") -> dict:
        if view not in ("monthly", "annual"):
            raise ValueError("view must be monthly or annual")
        today = self.today_fn()
        month = requested_month or today.strftime("%Y-%m")
        month_bounds(month)
        year = budget_year(requested_year) if requested_year else int(month[:4])
        if view == "monthly":
            year = int(month[:4])
        elif year != int(month[:4]):
            month = f"{year:04d}-{today.month:02d}"
        first = date(year, int(month[5:]), 1)
        last = first.replace(day=calendar.monthrange(year, first.month)[1])
        annual_start = date(year, 1, 1)
        annual_end = min(today, date(year, 12, 31) if view == "annual" else last)
        annual_cutoff = annual_end if annual_end >= annual_start else None
        monthly_cutoff = min(today, last) if first <= today else None
        annual_txns = self._transactions(annual_start, annual_cutoff)
        monthly_txns = [txn for txn in annual_txns if txn.date[:7].replace("_", "-") == month]
        categories = self.cat_svc.list()
        current = category_breakdown(annual_txns if view == "annual" else monthly_txns, categories)
        if not any(row.category_id is None for row in current.rows):
            current.rows.append(CategoryTotal(label="Uncategorized"))
        prior = CategoryBreakdown()
        previous, next_month = adjacent_month(month, -1), adjacent_month(month, 1)
        if view == "monthly" and previous:
            prev_first = date.fromisoformat(previous + "-01")
            prev_last = prev_first.replace(day=calendar.monthrange(prev_first.year, prev_first.month)[1])
            prior = category_breakdown(self._transactions(prev_first, min(today, prev_last)))
        elif view == "annual" and year > 1:
            prior = category_breakdown(self._transactions(date(year - 1, 1, 1), min(today, date(year - 1, 12, 31))))
        budgets = self._build_budgets(month, year, annual_cutoff, monthly_cutoff, current.rows, annual_txns)
        limits = {key: b["contribution"] for key, b in budgets.items() if b["period"] == "monthly" and b["contribution"] is not None}
        report_start = annual_start if view == "annual" else first
        report_end = annual_cutoff if view == "annual" else monthly_cutoff
        return {
            "view": view, "year": year, "month": month,
            "month_label": first.strftime("%B %Y"),
            "previous_month": previous, "next_month": next_month,
            "breakdown": current, "previous_breakdown": prior,
            "transactions_url": transactions_url(month, date_from=report_start.isoformat(), date_to=(report_end or report_start).isoformat()),
            "report_start": report_start.isoformat(), "report_end": report_end.isoformat() if report_end else None,
            "budgets": budgets, "limits": limits,
            "total_limits": sum(limits.values()),
            "total_available": sum(budgets[key]["available"] for key in limits),
            "total_remaining": sum(budgets[key]["remaining"] for key in limits),
            "budgeted_expenses": sum(budgets[key]["monthly_expenses"] for key in limits),
            "annual_limit": sum(b["annual_limit"] for b in budgets.values() if b["annual_limit"] is not None),
            "annual_expenses": sum(b["annual_expenses"] for b in budgets.values() if b["annual_limit"] is not None),
            "annual_period": f"January 1–{annual_cutoff.isoformat()}" if annual_cutoff else f"{year} plan",
            "annual_cutoff": annual_cutoff.isoformat() if annual_cutoff else None,
        }

    def _build_budgets(self, month, year, annual_cutoff, monthly_cutoff, rows, transactions):
        expenses, annual_expenses = {}, {}
        for txn in transactions:
            key = (txn.date[:7].replace("_", "-"), txn.category_id)
            expenses[key] = expenses.get(key, 0) - txn.amount
            annual_expenses[txn.category_id] = annual_expenses.get(txn.category_id, 0) - txn.amount
        limits, plans, rollover_changes = self.repo.list(), self.repo.list_plans(), self.repo.list_rollover()
        result = {}
        for row in rows:
            category_id = row.category_id
            plan = self._plan(category_id, year, plans)
            contribution = self._contribution(category_id, f"{year:04d}-01", limits)
            enabled = self._rollover_enabled(category_id, f"{year:04d}-01", rollover_changes)
            amounts = {c.month: c.amount_cents for c in limits if c.category_id == category_id}
            flags = {c.month: c.enabled for c in rollover_changes if c.category_id == category_id}
            balance, annual_limit = 0, None
            selected = {}
            for number in range(1, 13):
                period = f"{year:04d}-{number:02d}"
                if period in amounts:
                    contribution = amounts[period]
                if period in flags:
                    if flags[period] != enabled:
                        balance = 0
                    enabled = flags[period]
                if contribution is None:
                    balance, incoming = 0, 0
                    available = remaining = None
                else:
                    annual_limit = (annual_limit or 0) + contribution
                    incoming = balance if enabled else 0
                    available = contribution + incoming
                    remaining = available - expenses.get((period, category_id), 0)
                    balance = remaining if enabled else 0
                if period == month:
                    selected = dict(contribution=contribution, rollover=incoming, available=available,
                                    remaining=remaining, rollover_enabled=enabled)
            if plan.period == "annual":
                annual_limit = plan.annual_amount_cents
            annual_spent = annual_expenses.get(category_id, 0)
            monthly_spent = expenses.get((month, category_id), 0)
            elapsed_days = (annual_cutoff - date(year, 1, 1)).days + 1 if annual_cutoff else None
            year_days = 366 if calendar.isleap(year) else 365
            pace = elapsed_days / year_days if elapsed_days is not None else None
            result[category_id] = {
                **selected, "period": plan.period, "category_id": category_id, "label": row.label,
                "annual_limit": annual_limit, "annual_expenses": annual_spent,
                "annual_remaining": annual_limit - annual_spent if annual_limit is not None else None,
                "monthly_expenses": monthly_spent,
                "monthly_as_of": monthly_cutoff.isoformat() if monthly_cutoff else None,
                "annual_as_of": annual_cutoff.isoformat() if annual_cutoff else None,
                "pace": pace,
                "pace_amount_cents": (annual_limit * elapsed_days + year_days // 2) // year_days
                if annual_limit is not None and elapsed_days is not None else None,
                "next_change": next((c for c in limits if c.category_id == category_id and c.month > month), None),
                "next_plan": next((p for p in plans if p.category_id == category_id and p.year > year), None),
                "next_rollover": next((c for c in rollover_changes if c.category_id == category_id and c.month > month), None),
                "bar": budget_segments(selected["contribution"] or 0, selected["rollover"], monthly_spent),
                "annual_bar": budget_segments(annual_limit or 0, 0, annual_spent),
            }
        return result


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
