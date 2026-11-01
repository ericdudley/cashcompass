from fasthtml.common import *

from src.models import CategoryBreakdown
from src.services.budget import transactions_url
from src.utils.format import cents_dollars, cents_diff, cents_input


def breakdown_stats(data: CategoryBreakdown, *, expenses: bool = True):
    stats = [
        ("Spending" if expenses else "Outflows", data.spending, "spending"),
        ("Refunds / credits" if expenses else "Inflows", data.credits, "credits"),
        ("Net expenses" if expenses else "Net change", data.net_expenses if expenses else -data.net_expenses, "net"),
    ]
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
    return Section(
        Div(
            H2("Category breakdown", cls="text-lg font-semibold"),
            Span(f"{data.count} {'transaction' if data.count == 1 else 'transactions'}", cls="text-xs cc-muted"),
            cls="flex flex-wrap items-center justify-between gap-2",
        ),
        P("Totals follow the selected dates, categories, and search.", cls="text-xs cc-muted"),
        breakdown_stats(data, expenses=expenses),
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
        cls="cc-glass rounded-xl p-4 mb-6 space-y-3",
        data_testid="transaction-category-breakdown",
    )


def budget_limits(data: dict):
    cards = []
    for row in data["breakdown"].rows:
        limit = data["limits"].get(row.category_id)
        remaining = limit - row.net_expenses if limit is not None else None
        status = "No limit set"
        if remaining is not None:
            status = f"Over by {cents_dollars(-remaining)}" if remaining < 0 else f"{cents_dollars(remaining)} remaining"
        progress = min(100, max(0, row.net_expenses) * 100 / limit) if limit else (100 if row.net_expenses > 0 else 0)
        cards.append(Div(
            Div(
                H3(row.label, cls="font-semibold break-words min-w-0"),
                Span(f"{cents_dollars(row.net_expenses)} net", cls="text-xs font-mono cc-muted shrink-0"),
                cls="flex items-start justify-between gap-2",
            ),
            Div(
                Label("Monthly limit ($)", fr=f"budget-limit-{row.category_id or 0}", cls="text-xs cc-muted"),
                Input(type="number", name=f"limit_{row.category_id or 0}", id=f"budget-limit-{row.category_id or 0}",
                      value=cents_input(limit) if limit is not None else "", min="0", step="0.01", placeholder="No limit",
                      cls="input input-bordered input-sm w-full", aria_label=f"{row.label} monthly limit"),
                cls="space-y-1",
            ),
            Progress(value=progress, max="100", cls=f"progress {'progress-error' if remaining is not None and remaining < 0 else 'progress-primary'} w-full",
                     aria_label=f"{row.label} budget used") if limit is not None else "",
            P(status, cls="text-sm font-medium text-error" if remaining is not None and remaining < 0 else "text-sm cc-muted",
              data_testid="budget-limit-status", role="status"),
            cls="rounded-xl border border-base-300 p-4 space-y-3 min-w-0", data_testid="budget-limit-card", data_category_id=str(row.category_id or 0),
        ))
    return Section(
        Div(
            H2("Monthly category limits", cls="text-xl font-semibold"),
            P("Limits apply to this month only. Clear an amount to remove its limit; zero means no spending planned.", cls="text-sm cc-muted mt-1"),
        ),
        Div(
            Span(f"Total limits: {cents_dollars(data['total_limits'])}", data_testid="budget-total-limits"),
            Span(f"Remaining in set limits: {cents_dollars(data['total_limits'] - data['budgeted_expenses'])}", data_testid="budget-remaining"),
            cls="flex flex-wrap gap-x-6 gap-y-2 text-sm font-mono",
        ) if data["limits"] else P("Set a limit below to track remaining spending for a category.", cls="text-sm cc-muted"),
        Form(
            Input(type="hidden", name="month", value=data["month"]),
            Div(*cards, cls="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"),
            Button("Save limits", type="submit", cls="btn btn-primary btn-sm"),
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
        Div("Monthly limits saved.", cls="alert alert-success", role="status", data_testid="budget-saved") if saved else "",
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
