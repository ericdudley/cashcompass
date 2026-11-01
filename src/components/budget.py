from fasthtml.common import *
from datetime import datetime

from src.models import CategoryBreakdown
from src.services.budget import transactions_url
from src.utils.format import cents_dollars, cents_diff, cents_input


def breakdown_stats(data: CategoryBreakdown, *, expenses: bool = True, compact: bool = False):
    stats = [
        ("Spending" if expenses else "Outflows", data.spending, "spending"),
        ("Refunds / credits" if expenses else "Inflows", data.credits, "credits"),
        ("Net expenses" if expenses else "Net change", data.net_expenses if expenses else -data.net_expenses, "net"),
    ]
    if compact:
        return Div(*[
            Span(Span(f"{label}: ", cls="cc-muted"),
                 Span(cents_dollars(amount), cls="font-mono font-semibold tabular-nums", data_testid=f"category-total-{key}"))
            for label, amount, key in stats
        ], cls="flex flex-wrap gap-x-5 gap-y-1 text-sm")
    return Div(*[
        Div(
            P(label, cls="text-xs cc-muted"),
            P(cents_dollars(amount), cls="text-xl sm:text-2xl font-semibold font-mono tabular-nums", data_testid=f"category-total-{key}"),
            cls="min-w-0 rounded-xl bg-base-200/60 p-3",
        ) for label, amount, key in stats
    ], cls="grid gap-3 sm:grid-cols-3")


def category_breakdown_panel(data: CategoryBreakdown, *, expenses: bool = True):
    rows = []
    for row in data.rows:
        share = row.spending * 100 / data.spending if data.spending else 0
        rows.append(Tr(
            Td(row.label, cls="font-medium max-w-48 break-words whitespace-normal"),
            Td(cents_dollars(row.net_expenses if expenses else -row.net_expenses), cls="text-right font-mono font-medium", data_testid="category-net"),
            Td(str(row.count), cls="text-right tabular-nums"),
            Td(cents_dollars(row.spending), cls="text-right font-mono"),
            Td(cents_dollars(row.credits), cls="text-right font-mono"),
            Td(f"{share:.1f}%", cls="text-right tabular-nums"),
            data_category_id=str(row.category_id or 0),
            data_testid="category-breakdown-row",
        ))
    return Details(
        Summary(
            Div(
                Div(H2("Category breakdown", cls="text-sm font-semibold"),
                    Span(f"{data.count} {'transaction' if data.count == 1 else 'transactions'}", cls="text-xs cc-muted"),
                    cls="flex flex-wrap items-center gap-x-3 gap-y-1"),
                Span(
                    Span("Show categories", cls="group-open:hidden"),
                    Span("Hide categories", cls="hidden group-open:inline"),
                    Span(" ▸", cls="inline-block transition-transform group-open:rotate-90", aria_hidden="true"),
                    cls="text-xs text-primary shrink-0",
                ), cls="flex items-center justify-between gap-3",
            ),
            breakdown_stats(data, expenses=expenses, compact=True),
            cls="list-none cursor-pointer space-y-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary",
            data_testid="category-breakdown-toggle",
        ),
        Div(
            P("Totals follow the selected dates, categories, and search.", cls="text-xs cc-muted"),
            Div(
                Table(
                    Thead(Tr(*[Th(label, cls="text-right" if index else "") for index, label in enumerate([
                        "Category", "Net expenses" if expenses else "Net change", "Count", "Spending" if expenses else "Outflows",
                        "Credits" if expenses else "Inflows", "Share of spending" if expenses else "Share of outflows",
                    ])])),
                    Tbody(*rows), cls="table table-sm w-full",
                ), cls="overflow-x-auto",
            ) if rows else P("No category activity for these filters.", cls="text-sm cc-muted py-2"),
            P("Net expenses = spending − refunds / credits. Shares use spending before credits." if expenses else
              "Net change = inflows − outflows. Shares use outflows.", cls="text-xs cc-subtle"),
            cls="space-y-3 mt-3 pt-3 border-t border-base-300",
        ),
        cls="cc-glass rounded-xl p-4 mb-4 group",
        id="transaction-category-breakdown", data_testid="transaction-category-breakdown",
    )


def budget_progress(spent: int, available: int, remaining: int):
    if remaining < 0:
        return 100
    return min(100, max(0, spent) * 100 / available) if available > 0 else 0


def remaining_label(remaining: int) -> str:
    return f"Over by {cents_dollars(-remaining)}" if remaining < 0 else f"{cents_dollars(remaining)} remaining"


def budget_limits(data: dict):
    cards = []
    for row in data["breakdown"].rows:
        budget = data["budgets"][row.category_id]
        limit = budget["contribution"]
        remaining = budget["remaining"]
        next_change = budget["next_change"]
        annual_limit = budget["annual_limit"]
        annual_spent = budget["annual_expenses"]
        annual_remaining = annual_limit - annual_spent if annual_limit is not None else None
        cards.append(Div(
            Div(
                H3(row.label, cls="font-semibold break-words min-w-0"),
                Span(f"{cents_dollars(row.net_expenses)} net this month", cls="text-xs font-mono cc-muted"),
                cls="flex items-start justify-between gap-2",
            ),
            Div(
                Label("Monthly contribution ($)", fr=f"budget-limit-{row.category_id or 0}", cls="text-xs cc-muted"),
                Input(type="number", name=f"limit_{row.category_id or 0}", id=f"budget-limit-{row.category_id or 0}",
                      value=cents_input(limit) if limit is not None else "", min="0", step="0.01", placeholder="No limit",
                      cls="input input-bordered input-sm w-full", aria_label=f"{row.label} monthly contribution"),
                cls="space-y-1",
            ),
            P(
                f"Next change: {datetime.strptime(next_change.month, '%Y-%m').strftime('%B %Y')} · "
                + (f"{cents_dollars(next_change.amount_cents)}/month" if next_change.amount_cents is not None else "Tracking stops"),
                cls="text-xs cc-muted", data_testid="budget-next-change",
            ) if next_change else "",
            Dl(*[
                Div(Dt(label, cls="cc-muted"), Dd(cents_dollars(amount), cls="font-mono", data_testid=f"budget-{key}"),
                    cls="flex justify-between gap-2")
                for label, amount, key in [
                    ("Rollover into this month", budget["rollover"], "rollover"),
                    ("Available this month", budget["available"], "available"),
                ]
            ], cls="text-sm space-y-1") if limit is not None else "",
            Progress(value=budget_progress(row.net_expenses, budget["available"], remaining), max="100",
                     cls=f"progress {'progress-error' if remaining < 0 else 'progress-primary'} w-full",
                     aria_label=f"{row.label} budget used") if limit is not None else "",
            P(remaining_label(remaining) if remaining is not None else "No limit set",
              cls="text-sm font-medium text-error" if remaining is not None and remaining < 0 else "text-sm cc-muted",
              data_testid="budget-limit-status", role="status"),
            Div(
                P(f"Annual net spending · {data['annual_period']}", cls="text-xs cc-muted"),
                P(f"{cents_dollars(annual_spent)} of {cents_dollars(annual_limit)}", cls="text-sm font-mono",
                  data_testid="budget-annual-spending"),
                Progress(value=budget_progress(annual_spent, annual_limit, annual_remaining), max="100",
                         cls=f"progress {'progress-error' if annual_remaining < 0 else 'progress-secondary'} w-full",
                         aria_label=f"{row.label} annual budget used"),
                P(remaining_label(annual_remaining), cls="text-sm text-error" if annual_remaining < 0 else "text-sm cc-muted",
                  data_testid="budget-annual-status"),
                cls="border-t border-base-300 pt-3 space-y-1",
            ) if annual_limit is not None else "",
            cls="rounded-xl border border-base-300 p-4 space-y-3 min-w-0", data_testid="budget-limit-card", data_category_id=str(row.category_id or 0),
        ))
    return Section(
        Div(
            H2("Category budgets", cls="text-xl font-semibold"),
            P("Changes apply from this month until the next saved change. Unused funds and deficits roll over; balances reset each January.",
              cls="text-sm cc-muted mt-1"),
            P("Zero pauses contributions and keeps rollover. Clear an amount to stop tracking and reset its balance.", cls="text-sm cc-muted mt-1"),
        ),
        Div(
            Span(f"Monthly contributions: {cents_dollars(data['total_limits'])}", data_testid="budget-total-limits"),
            Span(f"Available: {cents_dollars(data['total_available'])}", data_testid="budget-total-available"),
            Span(f"Remaining: {cents_dollars(data['total_remaining'])}", data_testid="budget-remaining"),
            cls="flex flex-wrap gap-x-6 gap-y-2 text-sm font-mono",
        ) if data["limits"] else P("Set a monthly contribution below to start tracking a category budget.", cls="text-sm cc-muted"),
        P(f"Annual budget: {cents_dollars(data['annual_limit'])} · Net spending ({data['annual_period']}): {cents_dollars(data['annual_expenses'])}",
          cls="text-sm font-mono", data_testid="budget-annual-summary")
        if any(budget["annual_limit"] is not None for budget in data["budgets"].values()) else "",
        Form(
            Input(type="hidden", name="month", value=data["month"]),
            Div(*cards, cls="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"),
            Button("Save contributions", type="submit", cls="btn btn-primary btn-sm"),
            action="/budget/limits", method="post", cls="space-y-4", data_testid="budget-limits-form",
        ),
        cls="cc-glass rounded-2xl p-5 space-y-4", data_testid="budget-limits",
    )


def budget_page(data: dict, *, saved: bool = False):
    breakdown = data["breakdown"]
    prior = {row.category_id: row for row in data["previous_breakdown"].rows}
    current = {row.category_id: row for row in breakdown.rows}
    # Keep categories with only prior-month activity visible for comparison.
    rows = sorted({**prior, **current}.values(), key=lambda row: (
        -current[row.category_id].net_expenses if row.category_id in current else 0,
        row.label.casefold(), row.category_id or 0,
    ))
    table_rows = []
    for row in rows:
        now = current.get(row.category_id)
        before = prior.get(row.category_id)
        spending = now.spending if now else 0
        credits = now.credits if now else 0
        net = now.net_expenses if now else 0
        previous_net = before.net_expenses if before else 0
        share = spending * 100 / breakdown.spending if breakdown.spending else 0
        table_rows.append(Tr(
            Td(
                A(row.label, href=transactions_url(data["month"], row.category_id, category_filter=True), cls="link link-hover font-semibold"),
                Div(f"{now.count if now else 0} {'transaction' if now and now.count == 1 else 'transactions'}", cls="text-xs cc-muted mt-1"),
                cls="min-w-40 max-w-64 whitespace-normal break-words",
            ),
            Td(cents_dollars(net), cls="text-right font-mono font-semibold", data_testid="budget-category-net"),
            Td(cents_dollars(spending), cls="text-right font-mono", data_testid="budget-category-spending"),
            Td(cents_dollars(credits), cls="text-right font-mono"),
            Td(
                Div(f"{share:.1f}%", cls="text-right text-xs tabular-nums mb-1"),
                Progress(value=round(share, 2), max="100", cls="progress progress-primary w-24", aria_label=f"{row.label}: {share:.1f}% of spending"),
            ),
            Td(cents_dollars(previous_net), cls="text-right font-mono cc-muted"),
            Td(cents_diff(net - previous_net), cls="text-right font-mono", data_testid="budget-category-change"),
            data_category_id=str(row.category_id or 0), data_testid="budget-category-row",
        ))
    delta = breakdown.net_expenses - data["previous_breakdown"].net_expenses
    return (
        Header(
            Div(H1("Budget", cls="cc-page-title text-4xl font-semibold"),
                P("Understand where your money goes, one month at a time.", cls="cc-muted mt-2")),
            A("View transactions", href=data["transactions_url"], cls="btn btn-outline btn-sm"),
            cls="flex flex-wrap items-center justify-between gap-4",
        ),
        Section(
            Div(
                Div(H2(data["month_label"], cls="text-2xl font-semibold", data_testid="budget-month-label"),
                    P("All expense accounts · Net worth activity excluded", cls="text-sm cc-muted mt-1")),
                Div(
                    A("← Previous", href=f"/budget?month={data['previous_month']}", cls="btn btn-ghost btn-sm", aria_label="Previous month") if data["previous_month"] else "",
                    Form(
                        Label("Month", fr="budget-month", cls="sr-only"),
                        Input(type="month", id="budget-month", name="month", value=data["month"], required=True,
                              min="0001-01", max="9999-12", cls="input input-bordered input-sm w-44"),
                        Button("Go", type="submit", cls="btn btn-primary btn-sm"),
                        action="/budget", method="get", cls="flex items-center gap-2",
                    ),
                    A("Next →", href=f"/budget?month={data['next_month']}", cls="btn btn-ghost btn-sm", aria_label="Next month") if data["next_month"] else "",
                    cls="flex flex-wrap items-center gap-2",
                ), cls="flex flex-wrap items-center justify-between gap-4",
            ),
            breakdown_stats(breakdown),
            P(f"{cents_diff(delta)} in net expenses compared with the previous month.", cls="text-sm cc-muted", data_testid="budget-month-change") if data["previous_month"] else "",
            cls="cc-glass rounded-2xl p-5 space-y-5",
        ),
        Div("Budget changes saved from this month until the next saved change.", cls="alert alert-success", role="status", data_testid="budget-saved") if saved else "",
        budget_limits(data),
        Section(
            Div(H2("Expenses by category", cls="text-xl font-semibold"),
                P("Net expenses = spending − refunds / credits. Shares use spending before credits.", cls="text-sm cc-muted mt-1")),
            Div("No expenses recorded this month. Add transactions to start tracking your spending.",
                cls="border border-dashed border-base-300 rounded-xl p-5 text-sm cc-muted", data_testid="budget-empty") if not breakdown.count else "",
            Div(
                Table(
                    Thead(Tr(*[Th(label, cls="text-right" if index else "") for index, label in enumerate([
                        "Category", "Net expenses", "Spending", "Credits", "Share of spending", "Previous month", "Change",
                    ])])),
                    Tbody(*table_rows), cls="table w-full",
                ), cls="overflow-x-auto",
            ) if table_rows else P("Create categories to organize your monthly expenses.", cls="text-sm cc-muted"),
            cls="cc-glass rounded-2xl p-5 space-y-4", data_testid="budget-categories",
        ),
    )
