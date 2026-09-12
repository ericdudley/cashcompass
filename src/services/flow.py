from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode

from src.models import AnnualIncome, Transaction, TransactionFilter
from src.services.annual_income import AnnualIncomeService
from src.services.transaction import TransactionService
from src.utils.format import cents_abs, cents_diff, cents_dollars


class FlowService:
    def __init__(self, income_svc: AnnualIncomeService, txn_svc: TransactionService):
        self.income_svc = income_svc
        self.txn_svc = txn_svc

    def build(self, requested_year: str = "") -> dict:
        incomes = self.income_svc.list()
        expense_history = self.txn_svc.list(TransactionFilter(account_type="expenses"))
        years = self._available_years(incomes, expense_history)
        selected_year = self._selected_year(requested_year, incomes, years)
        income = self.income_svc.get_by_year(selected_year) if selected_year else None

        base = {
            "years": years,
            "selected_year": selected_year,
            "income": income,
            "has_income": income is not None,
        }
        if income is None:
            return base

        txns = self.txn_svc.list(TransactionFilter(
            date_from=f"{selected_year}_01_01",
            date_to=f"{selected_year}_12_31",
            account_type="expenses",
        ))
        net_worth_txns = self.txn_svc.list(TransactionFilter(
            date_from=f"{selected_year}_01_01",
            date_to=f"{selected_year}_12_31",
            account_type="net_worth",
        ))
        return {**base, **build_flow_view_model(income, txns, net_worth_txns)}

    @staticmethod
    def _available_years(incomes: list[AnnualIncome], txns: list[Transaction]) -> list[int]:
        years = {income.tax_year for income in incomes}
        for txn in txns:
            raw = (txn.date or "")[:4]
            if raw.isdigit():
                years.add(int(raw))
        return sorted(years, reverse=True)

    @staticmethod
    def _selected_year(
        requested_year: str,
        incomes: list[AnnualIncome],
        years: list[int],
    ) -> int:
        try:
            requested = int(requested_year)
        except (TypeError, ValueError):
            requested = 0
        if requested in years:
            return requested
        if incomes:
            return incomes[0].tax_year
        if years:
            return years[0]
        return datetime.now().year


def build_flow_view_model(
    income: AnnualIncome,
    txns: list[Transaction],
    net_worth_txns: list[Transaction] | None = None,
) -> dict:
    net_worth_txns = net_worth_txns or []
    category_totals: dict[tuple[int | None, str], int] = {}
    for txn in txns:
        key = (txn.category_id, txn.category_label or "Uncategorized")
        category_totals[key] = category_totals.get(key, 0) + (-txn.amount)

    positive_categories = sorted(
        (
            {
                "category_id": category_id,
                "label": label,
                "amount": amount,
            }
            for (category_id, label), amount in category_totals.items()
            if amount > 0
        ),
        key=lambda row: (-row["amount"], row["label"]),
    )
    refunds = sum(-amount for amount in category_totals.values() if amount < 0)
    positive_expenses = sum(row["amount"] for row in positive_categories)
    net_expenses = positive_expenses - refunds
    after_tax = income.after_tax_income_cents
    cash_flow_result = after_tax - net_expenses
    left_over = max(cash_flow_result, 0)
    shortfall = max(-cash_flow_result, 0)
    net_worth_change = sum(txn.amount for txn in net_worth_txns)
    has_net_worth_activity = bool(net_worth_txns)
    net_worth_difference = net_worth_change - cash_flow_result
    cash_flow_label = "Left Over" if cash_flow_result >= 0 else "Cash-flow Shortfall"

    nodes = [
        _node("gross", "Gross Income", "income", income.gross_income_cents, income.gross_income_cents, sort_order=0),
        _node("after-tax", "Income After Listed Taxes", "after_tax", after_tax, income.gross_income_cents, sort_order=0),
        _node("available", "Available Funds", "pool", after_tax + refunds + shortfall, after_tax, sort_order=0),
    ]
    links = []

    if income.federal_tax_cents:
        nodes.append(_node(
            "federal-tax", "Federal Tax", "tax", income.federal_tax_cents, income.gross_income_cents,
            group="taxes", group_label="Taxes", sort_order=0,
        ))
        links.append(_link("gross", "federal-tax", income.federal_tax_cents, "Federal tax"))
    if income.state_tax_cents:
        nodes.append(_node(
            "state-tax", "State Tax", "tax", income.state_tax_cents, income.gross_income_cents,
            group="taxes", group_label="Taxes", sort_order=1,
        ))
        links.append(_link("gross", "state-tax", income.state_tax_cents, "State tax"))
    if after_tax:
        links.append(_link("gross", "after-tax", after_tax, "After listed taxes"))
        links.append(_link("after-tax", "available", after_tax, "Available after listed taxes"))

    if refunds:
        nodes.append(_node(
            "refunds", "Expense Refunds / Credits", "refund", refunds, after_tax,
            sort_order=1,
        ))
        links.append(_link("refunds", "available", refunds, "Expense refunds and credits"))
    if shortfall:
        nodes.append(_node(
            "shortfall", "Savings / Debt Used", "shortfall", shortfall, after_tax,
            group="funding-gap", group_label="Funding Gap", sort_order=2,
        ))
        links.append(_link("shortfall", "available", shortfall, "Shortfall funding"))

    for index, row in enumerate(positive_categories):
        node_id = f"category-{index}"
        row["node_id"] = node_id
        row["amount_fmt"] = cents_dollars(row["amount"])
        row["transactions_url"] = _transactions_url(income.tax_year, row["category_id"])
        nodes.append(_node(
            node_id,
            row["label"],
            "expense",
            row["amount"],
            after_tax,
            row["transactions_url"],
            group="expenses",
            group_label="Expenses",
            sort_order=100 + index,
        ))
        links.append(_link("available", node_id, row["amount"], row["label"]))

    if left_over:
        nodes.append(_node(
            "left-over", "Left Over", "leftover", left_over, after_tax,
            group="left-over", group_label="Left Over", sort_order=10_000,
        ))
        links.append(_link("available", "left-over", left_over, "Left over"))

    combined_tax = income.federal_tax_cents + income.state_tax_cents
    comparison_message = _comparison_message(
        has_net_worth_activity,
        net_worth_difference,
        cash_flow_result,
    )
    return {
        "gross_income": income.gross_income_cents,
        "gross_income_fmt": cents_dollars(income.gross_income_cents),
        "federal_tax_fmt": cents_dollars(income.federal_tax_cents),
        "state_tax_fmt": cents_dollars(income.state_tax_cents),
        "combined_tax_fmt": cents_dollars(combined_tax),
        "after_tax_income": after_tax,
        "after_tax_income_fmt": cents_dollars(after_tax),
        "net_expenses": net_expenses,
        "net_expenses_fmt": cents_dollars(net_expenses),
        "refunds": refunds,
        "refunds_fmt": cents_dollars(refunds),
        "left_over": left_over,
        "left_over_fmt": cents_dollars(left_over),
        "shortfall": shortfall,
        "shortfall_fmt": cents_dollars(shortfall),
        "cash_flow_result": cash_flow_result,
        "cash_flow_result_fmt": cents_dollars(cash_flow_result),
        "cash_flow_label": cash_flow_label,
        "has_net_worth_activity": has_net_worth_activity,
        "net_worth_change": net_worth_change,
        "net_worth_change_fmt": cents_diff(net_worth_change),
        "net_worth_difference": net_worth_difference,
        "net_worth_difference_fmt": cents_diff(net_worth_difference),
        "net_worth_comparison_scale": max(abs(cash_flow_result), abs(net_worth_change), 1),
        "net_worth_comparison_status": _comparison_status(has_net_worth_activity, net_worth_difference),
        "net_worth_comparison_message": comparison_message,
        "net_worth_activity_count": len(net_worth_txns),
        "tax_rate": f"{combined_tax / income.gross_income_cents * 100:.1f}%",
        "categories": positive_categories,
        "graph": {
            "year": income.tax_year,
            "gross_income": income.gross_income_cents,
            "after_tax_income": after_tax,
            "nodes": nodes,
            "links": links,
        },
    }


def _node(
    node_id: str,
    label: str,
    kind: str,
    value: int,
    percentage_basis: int,
    url: str = "",
    group: str = "",
    group_label: str = "",
    sort_order: int = 0,
) -> dict:
    percentage = value / percentage_basis * 100 if percentage_basis else 0
    percentage_label = (
        "of gross income"
        if kind in ("income", "after_tax", "tax")
        else "of income after listed taxes"
    )
    return {
        "id": node_id,
        "label": label,
        "kind": kind,
        "value_cents": value,
        "value_fmt": cents_dollars(value),
        "percentage": f"{percentage:.1f}%",
        "percentage_label": percentage_label,
        "url": url,
        "group": group,
        "group_label": group_label,
        "sort_order": sort_order,
    }


def _comparison_status(has_activity: bool, difference: int) -> str:
    if not has_activity:
        return "unavailable"
    if difference > 0:
        return "more"
    if difference < 0:
        return "less"
    return "matched"


def _comparison_message(has_activity: bool, difference: int, cash_flow_result: int) -> str:
    if not has_activity:
        return "No net-worth activity was recorded for this year."

    basis = "the recorded left over" if cash_flow_result >= 0 else "the cash-flow result"
    if difference > 0:
        return f"Net worth change was {cents_abs(difference)} more than {basis}."
    if difference < 0:
        return f"Net worth change was {cents_abs(difference)} less than {basis}."
    return f"Net worth change matched {basis}."


def _link(source: str, target: str, value: int, label: str) -> dict:
    return {
        "source": source,
        "target": target,
        "value": value,
        "label": label,
        "value_fmt": cents_dollars(value),
    }


def _transactions_url(tax_year: int, category_id: int | None) -> str:
    params = [
        ("account_type", "expenses"),
        ("date_from", f"{tax_year}-01-01"),
        ("date_to", f"{tax_year}-12-31"),
    ]
    if category_id is not None:
        params.append(("category_id", str(category_id)))
    return "/transactions?" + urlencode(params)
