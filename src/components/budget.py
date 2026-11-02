from fasthtml.common import *

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


def remaining_label(remaining: int) -> str:
    return f"Over by {cents_dollars(-remaining)}" if remaining < 0 else f"{cents_dollars(remaining)} remaining"


def context_url(data):
    from urllib.parse import urlencode
    return "/budget?" + urlencode({"view": data["view"], "month": data["month"], "year": f"{data['year']:04d}"})


def combined_bar(budget, *, annual=False):
    bar = budget["annual_bar"] if annual else budget["bar"]
    remaining = budget["annual_remaining"] if annual else budget["remaining"]
    spent = budget["annual_expenses"] if annual else budget["monthly_expenses"]
    labels = {"spent": "Spent", "monthly": "Remaining" if annual else "Monthly left", "rollover": "Rollover left"}
    parts = bar["segments"]
    description = "; ".join(f"{labels[part['key']]} {cents_dollars(spent if part['key'] == 'spent' else part['amount'])}" for part in parts)
    if remaining < 0:
        description += f"; {remaining_label(remaining)}"
    if spent < 0:
        description += f"; {cents_dollars(-spent)} net credits"
    pace = budget["pace"] if annual else None
    if pace is not None:
        description += f"; {pace:.1%} of calendar year elapsed"
    return Div(
        Div(
            Div(*[Div(cls=f"cc-budget-segment cc-budget-{part['key']}" + (" cc-budget-over" if remaining < 0 else ""),
                      style=f"width:{part['percent']:.6f}%", data_testid=f"budget-segment-{part['key']}") for part in parts],
                Div(cls="cc-budget-segment cc-budget-over", style="width:100%") if not parts and remaining < 0 else "",
                cls="cc-budget-track"),
            Span(cls="cc-budget-marker", style=f"left:{bar['boundary']:.6f}%", aria_hidden="true")
            if not annual and bar["boundary"] is not None else "",
            Span(cls="cc-budget-marker cc-budget-pace", style=f"left:{pace * 100:.6f}%", aria_hidden="true",
                 data_testid="budget-pace-marker") if pace is not None else "",
            cls="cc-budget-meter", role="img", aria_label=f"{budget['label']}: {description or 'No positive allowance'}",
            data_testid="budget-bar",
        ),
        Div(*[Span(Span(cls=f"cc-budget-swatch cc-budget-{part['key']}" + (" cc-budget-over" if remaining < 0 and part["key"] == "spent" else "")),
                   f"{labels[part['key']]} {cents_dollars(spent if part['key'] == 'spent' else part['amount'])}") for part in parts],
            cls="flex flex-wrap gap-x-4 gap-y-1 text-xs", data_testid="budget-bar-labels"),
        P(f"Even-spending pace: {pace:.0%} of year · {cents_dollars(budget['pace_amount_cents'])}",
          cls="text-xs cc-muted", data_testid="budget-pace-label") if pace is not None else "",
        cls="space-y-2",
    )


def budget_card(budget, data, *, annual=False):
    annual = annual or budget["period"] == "annual"
    amount = budget["annual_limit"] if annual else budget["contribution"]
    remaining = budget["annual_remaining"] if annual else budget["remaining"]
    spent = budget["annual_expenses"] if annual else budget["monthly_expenses"]
    cutoff = budget["annual_as_of"] if annual else budget["monthly_as_of"]
    planned = cutoff is None
    start = f"{data['year']:04d}-01-01" if annual else data["month"] + "-01"
    subtitle = "Annual" if budget["period"] == "annual" else "Annualized monthly" if annual else "Monthly"
    status = "No budget set" if amount is None else f"Planned {cents_dollars(amount)}" if planned else remaining_label(remaining)
    details = [("Net spending", spent)]
    if annual:
        details += [("Annual budget", amount)] if amount is not None else []
    elif amount is not None:
        details += [("Monthly contribution", amount), ("Rollover into this month", budget["rollover"]),
                    ("Available this month", budget["available"])]
    next_change = budget["next_change"]
    next_plan = budget["next_plan"]
    next_rollover = budget["next_rollover"]
    from urllib.parse import urlencode
    edit_url = f"/budget/categories/{budget['category_id'] or 0}/edit?" + urlencode({
        "view": data["view"], "month": data["month"], "year": f"{data['year']:04d}",
    })
    return Article(
        Div(
            Div(H3(budget["label"], cls="font-semibold break-words"), P(subtitle, cls="text-xs cc-muted")),
            A("Edit budget", href=edit_url, cls="btn btn-ghost btn-xs shrink-0",
              aria_label=f"Edit {budget['label']} budget"),
            cls="flex justify-between gap-3 items-start",
        ),
        P(status, cls="text-xl font-semibold font-mono break-words text-error" if remaining is not None and remaining < 0 and not planned else "text-xl font-semibold font-mono break-words",
          data_testid="budget-limit-status", role="status"),
        combined_bar(budget, annual=annual) if amount is not None and not planned else "",
        P(f"{cents_dollars(amount)} annual budget" if annual else
          f"{cents_dollars(amount)} this month" + (f" + {cents_dollars(budget['rollover'])} rollover" if budget["rollover"] > 0 else ""),
          cls="text-sm cc-muted", data_testid="budget-allowance") if amount is not None else "",
        P(f"{cents_dollars(-budget['rollover'])} carried overspend reduces this month's allowance.", cls="text-xs cc-muted")
        if not annual and budget["rollover"] < 0 else "",
        P("Using rollover", cls="text-xs cc-muted", data_testid="budget-using-rollover")
        if not annual and amount is not None and budget["rollover"] > 0 and amount < spent <= budget["available"] else "",
        P(f"Includes {cents_dollars(-spent)} net credits.", cls="text-xs cc-muted") if spent < 0 else "",
        A(f"Net spending through {cutoff}",
          href=transactions_url(data["month"], budget["category_id"], category_filter=True, date_from=start, date_to=cutoff),
          cls="text-xs link link-hover cc-muted", data_testid="budget-drilldown") if cutoff else
        P("Planned period · spending progress starts when this period begins.", cls="text-xs cc-muted"),
        Details(
            Summary("Budget details", cls="cursor-pointer text-sm cc-muted"),
            Dl(*[Div(Dt(label, cls="cc-muted"), Dd(cents_dollars(value), cls="font-mono"),
                     cls="flex flex-wrap justify-between gap-x-3 gap-y-1") for label, value in details], cls="text-sm space-y-2 mt-3"),
            P("Sum of scheduled monthly contributions; rollover is excluded.", cls="text-xs cc-muted mt-3")
            if annual and budget["period"] == "monthly" else "",
            P("Rollover on · balances reset each January" if budget["rollover_enabled"] else "Rollover off · each month starts fresh",
              cls="text-xs cc-muted mt-3") if not annual else "",
            P(f"Next contribution change: {next_change.month} · " +
              (f"{cents_dollars(next_change.amount_cents)}/month" if next_change.amount_cents is not None else "Tracking stops"),
              cls="text-xs cc-muted mt-3", data_testid="budget-next-change") if next_change and not annual else "",
            P(f"Next rollover change: {next_rollover.month} · {'On' if next_rollover.enabled else 'Off'}", cls="text-xs cc-muted mt-2")
            if next_rollover and not annual else "",
            P(f"Next plan: {next_plan.year} · {next_plan.period}" +
              (f" · {cents_dollars(next_plan.annual_amount_cents)}" if next_plan.annual_amount_cents is not None else ""),
              cls="text-xs cc-muted mt-2") if next_plan else "",
        ),
        cls="cc-glass rounded-xl p-5 space-y-3 min-w-0", data_testid="budget-limit-card",
        data_category_id=str(budget["category_id"] or 0), data_period=budget["period"], data_representation="annual" if annual else "monthly",
    )


def budget_group(title, budgets, data, *, annual=False):
    if not budgets:
        return ""
    tracked = [b for b in budgets if (b["annual_limit"] if annual else b["contribution"]) is not None]
    total = sum(b["annual_limit"] if annual else b["contribution"] for b in tracked)
    remaining = sum(b["annual_remaining"] if annual else b["remaining"] for b in tracked)
    planned = data["annual_cutoff"] is None if annual else data["report_end"] is None
    return Section(
        Div(H2(title, cls="text-xl font-semibold"),
            P(f"{'Annual plan' if annual else 'Monthly plan'}: {cents_dollars(total)}" +
              (f" · {remaining_label(remaining)}" if tracked and not planned else ""), cls="text-sm cc-muted font-mono",
              data_testid="budget-annual-summary" if annual else "budget-monthly-summary"),
            cls="space-y-1"),
        Div(*[budget_card(b, data, annual=annual) for b in budgets], cls="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"),
        cls="space-y-4", data_testid="budget-annual-group" if annual else "budget-monthly-group",
    )


def budget_expenses(data):
    breakdown = data["breakdown"]
    prior = {row.category_id: row for row in data["previous_breakdown"].rows}
    current = {row.category_id: row for row in breakdown.rows}
    rows = sorted({**prior, **current}.values(), key=lambda row: (-current[row.category_id].net_expenses if row.category_id in current else 0,
                                                              row.label.casefold(), row.category_id or 0))
    table_rows = []
    for row in rows:
        now, before = current.get(row.category_id), prior.get(row.category_id)
        spending, credits, net = (now.spending, now.credits, now.net_expenses) if now else (0, 0, 0)
        previous_net = before.net_expenses if before else 0
        share = spending * 100 / breakdown.spending if breakdown.spending else 0
        table_rows.append(Tr(
            Td(A(row.label, href=transactions_url(data["month"], row.category_id, category_filter=True,
                                                  date_from=data["report_start"], date_to=data["report_end"]),
                 cls="link link-hover font-semibold") if data["report_end"] else row.label,
               Div(f"{now.count if now else 0} transactions", cls="text-xs cc-muted mt-1"), cls="min-w-40 max-w-64 whitespace-normal break-words"),
            Td(cents_dollars(net), cls="text-right font-mono font-semibold", data_testid="budget-category-net"),
            Td(cents_dollars(spending), cls="text-right font-mono", data_testid="budget-category-spending"),
            Td(cents_dollars(credits), cls="text-right font-mono"),
            Td(Div(f"{share:.1f}%", cls="text-right text-xs mb-1"),
               Progress(value=round(share, 2), max="100", cls="progress progress-primary w-24", aria_label=f"{row.label}: {share:.1f}% of spending")),
            Td(cents_dollars(previous_net), cls="text-right font-mono cc-muted"),
            Td(cents_diff(net - previous_net), cls="text-right font-mono", data_testid="budget-category-change"),
            data_category_id=str(row.category_id or 0), data_testid="budget-category-row",
        ))
    return Section(
        H2("Expenses by category", cls="text-xl font-semibold"),
        P("Net expenses = spending − refunds / credits. Shares use spending before credits.", cls="text-sm cc-muted"),
        P("No expenses recorded this period. Add transactions to start tracking your spending.", cls="text-sm cc-muted", data_testid="budget-empty")
        if not breakdown.count else "",
        Div(Table(Thead(Tr(*[Th(label, cls="text-right" if index else "") for index, label in enumerate([
            "Category", "Net expenses", "Spending", "Credits", "Share of spending", "Previous year" if data["view"] == "annual" else "Previous month", "Change",
        ])])), Tbody(*table_rows), cls="table w-full"), cls="overflow-x-auto"),
        cls="cc-glass rounded-2xl p-5 space-y-4", data_testid="budget-categories",
    )


def budget_page(data, *, saved=False):
    annual = data["view"] == "annual"
    year, month = data["year"], data["month"]
    period_label = str(year) if annual else data["month_label"]
    previous = year - 1 if annual else data["previous_month"]
    following = year + 1 if annual else data["next_month"]
    def period_url(value):
        return f"/budget?view=annual&year={value:04d}" if annual else f"/budget?month={value}"
    monthly_budgets = [b for b in data["budgets"].values() if b["period"] == "monthly"]
    annual_budgets = [b for b in data["budgets"].values() if b["period"] == "annual"]
    delta = data["breakdown"].net_expenses - data["previous_breakdown"].net_expenses
    return (
        Header(Div(H1("Budget", cls="cc-page-title text-4xl font-semibold"),
                   P("Your spending, at the pace you plan it.", cls="cc-muted mt-2")),
               A("View transactions", href=data["transactions_url"], cls="btn btn-outline btn-sm") if data["report_end"] else "",
               cls="flex flex-wrap justify-between items-center gap-4"),
        Nav(A("Monthly", href=f"/budget?month={month}", cls="btn btn-sm " + ("btn-ghost" if annual else "btn-primary"),
              aria_current="page" if not annual else None),
            A("Annual", href=f"/budget?view=annual&year={year:04d}&month={month}", cls="btn btn-sm " + ("btn-primary" if annual else "btn-ghost"),
              aria_current="page" if annual else None), cls="flex gap-2", aria_label="Budget view"),
        Section(
            Div(H2(period_label, cls="text-2xl font-semibold", data_testid="budget-month-label"),
                Div(
                    A("← Previous", href=period_url(previous), cls="btn btn-ghost btn-sm", aria_label="Previous year" if annual else "Previous month")
                    if previous and (not annual or previous >= 1) else "",
                    Form(Input(type="hidden", name="view", value=data["view"]),
                         Label("Year" if annual else "Month", fr="budget-year" if annual else "budget-month", cls="sr-only"),
                         Input(type="number" if annual else "month", id="budget-year" if annual else "budget-month",
                               name="year" if annual else "month", value=year if annual else month,
                               min="1" if annual else "0001-01", max="9999" if annual else "9999-12", required=True,
                               cls="input input-bordered input-sm w-40"),
                         Button("Go", type="submit", cls="btn btn-primary btn-sm"), action="/budget", method="get", cls="flex gap-2"),
                    A("Next →", href=period_url(following), cls="btn btn-ghost btn-sm", aria_label="Next year" if annual else "Next month")
                    if following and (not annual or following <= 9999) else "",
                    cls="flex flex-wrap items-center gap-2"), cls="flex flex-wrap justify-between items-center gap-4"),
            P(f"All expense accounts · Net worth activity excluded · Through {data['report_end']}" if data["report_end"] else
              "Planned period · future-dated spending is excluded", cls="text-sm cc-muted", data_testid="budget-cutoff"),
            breakdown_stats(data["breakdown"]),
            P(f"{cents_diff(delta)} in net expenses compared with the previous {'year' if annual else 'month'}.",
              cls="text-sm cc-muted", data_testid="budget-month-change"),
            cls="cc-glass rounded-2xl p-5 space-y-4"),
        Div("Budget saved.", role="status", cls="alert alert-success", data_testid="budget-saved") if saved else "",
        budget_group("Annual budgets", annual_budgets, data, annual=True) if annual else budget_group("Monthly budgets", monthly_budgets, data),
        budget_group("Annualized monthly budgets", monthly_budgets, data, annual=True) if annual else budget_group("Annual budgets", annual_budgets, data, annual=True),
        budget_expenses(data),
    )


def budget_edit(data, budget):
    annual = budget["period"] == "annual"
    amount = budget["annual_limit"] if annual else budget["contribution"]
    return (
        Header(H1(f"Edit {budget['label']} budget", cls="cc-page-title text-3xl font-semibold"), cls="space-y-2"),
        Form(
            Input(type="hidden", name="view", value=data["view"]),
            Input(type="hidden", name="month", value=data["month"]),
            Input(type="hidden", name="year", value=f"{data['year']:04d}"),
            Div(Label("Budget type", fr="budget-type", cls="text-sm"),
                Select(Option("Monthly", value="monthly", selected=not annual), Option("Annual", value="annual", selected=annual),
                       id="budget-type", name="period", cls="select select-bordered w-full", data_initial_period=budget["period"]), cls="space-y-2"),
            Div(Label("Annual amount ($)" if annual else "Monthly amount ($)", fr="budget-amount", id="budget-amount-label", cls="text-sm"),
                Input(type="number", name="amount", id="budget-amount", value=cents_input(amount) if amount is not None else "",
                      min="0", step="0.01", cls="input input-bordered w-full", data_initial_amount=cents_input(amount) if amount is not None else ""),
                cls="space-y-2"),
            Div(Label("Effective month", fr="budget-effective-month", cls="text-sm"),
                Input(type="month", name="effective_month", id="budget-effective-month", value=data["month"],
                      min=f"{data['year']:04d}-01", max=f"{data['year']:04d}-12", cls="input input-bordered w-full"),
                Label(Input(type="checkbox", name="rollover", value="true", checked=budget["rollover_enabled"], cls="checkbox checkbox-sm"),
                      Span("Carry unused funds and deficits into the next month"), cls="flex items-start gap-3 text-sm"),
                P("Amount and rollover changes apply from the effective month until their next saved change. Enabling rollover starts with zero carry-in; disabling clears it.", cls="text-sm cc-muted"),
                cls="space-y-3" + (" hidden" if annual else ""), data_monthly_only="true"),
            P(f"Type changes apply to the whole of {data['year']} and inherit into later years. Converting to monthly starts its amount in January; later scheduled changes are preserved.", cls="text-sm cc-muted"),
            P(f"Annual amounts replace the full {data['year']} limit, including earlier spending, and inherit into later years. Blank stops tracking; zero is an active budget.", cls="text-sm cc-muted"),
            P(f"Next saved contribution: {budget['next_change'].month}" , cls="text-sm cc-muted") if budget["next_change"] else "",
            P(f"Next saved plan: {budget['next_plan'].year} · {budget['next_plan'].period}", cls="text-sm cc-muted") if budget["next_plan"] else "",
            Div(Button("Save budget", type="submit", cls="btn btn-primary"), A("Cancel", href=context_url(data), cls="btn btn-ghost"), cls="flex gap-3"),
            action=f"/budget/categories/{budget['category_id'] or 0}", method="post", cls="cc-glass rounded-xl p-5 space-y-5 max-w-xl",
            data_testid="budget-edit-form",
        ),
    )
