import math
from fasthtml.common import *
from src.utils.format import cents_abs, cents_dollars


def dash_month_label(yyyy_mm: str) -> str:
    try:
        from datetime import datetime
        t = datetime.strptime(yyyy_mm, "%Y-%m")
        return t.strftime("%b '%y")
    except Exception:
        return yyyy_mm


NW_COLORS = [
    "#34d399",  # emerald-400
    "#60a5fa",  # blue-400
    "#f472b6",  # pink-400
    "#fbbf24",  # amber-400
    "#a78bfa",  # violet-400
    "#fb923c",  # orange-400
]


def dashboard_page(data: dict):
    # Summary stats
    change_cls = "text-success" if data.get("expense_change_pos") else "text-error"
    change_p = P(f"{data['expense_change_pct']} vs last month", cls=f"text-xs {change_cls}") if data.get("expense_change_pct") else ""

    summary = Section(
        Div(
            P("This Month", cls="text-xs uppercase tracking-wider cc-subtle"),
            P(data["this_month_expenses"], cls="text-2xl font-semibold text-base-content"),
            change_p,
            data_testid="stat-this-month",
            cls="cc-glass rounded-xl p-4 space-y-1",
        ),
        Div(
            P("Monthly Avg", cls="text-xs uppercase tracking-wider cc-subtle"),
            P(data["avg_monthly_expenses"], cls="text-2xl font-semibold text-base-content"),
            P("full months only", cls="text-xs cc-muted"),
            cls="cc-glass rounded-xl p-4 space-y-1",
        ),
        Div(
            P("Net Worth", cls="text-xs uppercase tracking-wider cc-subtle"),
            P(data["current_net_worth"], cls="text-2xl font-semibold text-base-content"),
            cls="cc-glass rounded-xl p-4 space-y-1 col-span-2",
        ),
        data_testid="summary-stats",
        cls="grid grid-cols-2 md:grid-cols-4 gap-4",
    )

    # Expense bars
    if data.get("expense_bars"):
        bar_divs = []
        for bar in data["expense_bars"]:
            bar_divs.append(
                Div(
                    Span(bar["amt_fmt"],
                         cls="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 text-xs text-base-content bg-base-300 rounded px-1.5 py-0.5 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10"),
                    Div(cls="w-full rounded-t bg-success opacity-75 transition-opacity group-hover:opacity-100",
                        style=bar["height_style"]),
                    cls="group flex-1 flex flex-col items-end justify-end relative h-full",
                )
            )
        month_labels = [Div(m, cls="flex-1 truncate text-center text-xs cc-subtle") for m in data["expense_months"]]
        bars_section = Div(
            Div(*bar_divs, cls="flex items-end gap-1 h-36"),
            Div(*month_labels, cls="flex gap-1 mt-1"),
            cls="cc-glass rounded-xl p-4",
        )
    else:
        bars_section = P("No expense data yet. Add some transactions to see your spending trends.", cls="text-sm cc-muted")

    # Category table
    cat_table = ""
    if data.get("cat_month_rows"):
        header_cells = [Th("Category", cls="px-4 py-2 text-left font-medium cc-muted")]
        for m in data["cat_months"]:
            header_cells.append(Th(m, cls="px-3 py-2 text-right font-medium cc-muted"))
        header_cells.append(Th("Total", cls="px-4 py-2 text-right font-medium cc-muted"))

        body_rows = []
        for row in data["cat_month_rows"]:
            cells = [Td(row["category"], cls="px-4 py-2 text-base-content")]
            for t in row["totals"]:
                cells.append(Td(t, cls="px-3 py-2 text-right cc-muted"))
            cells.append(Td(row["total"], cls="px-4 py-2 text-right font-medium text-base-content"))
            body_rows.append(Tr(*cells, cls="border-b border-base-300/70 hover:bg-base-200/60"))

        cat_table = Div(
            Table(
                Thead(Tr(*header_cells, cls="border-b border-base-300")),
                Tbody(*body_rows),
                cls="table w-full text-sm",
            ),
            cls="cc-glass overflow-x-auto rounded-xl",
        )

    expenses_section = Section(
        H2("Expenses", cls="text-xl font-semibold text-base-content"),
        bars_section,
        cat_table,
        data_testid="expenses-section",
        cls="space-y-4",
    )

    # Net worth chart
    nw_chart = ""
    if data.get("nw_lines") and len(data["nw_lines"]) >= 1:
        polylines = []
        legends = []
        for line in data["nw_lines"]:
            polylines.append(
                ft(
                    "polyline",
                    points=line["points"],
                    fill="none",
                    stroke=line["color"],
                    stroke_width="2",
                    vector_effect="non-scaling-stroke",
                )
            )
            legends.append(
                Div(
                    Span(cls="inline-block h-2 w-5 rounded", style=f"background:{line['color']}"),
                    Span(line["label"], cls="text-xs cc-muted"),
                    cls="flex items-center gap-1.5",
                )
            )

        nw_chart = Div(
            Svg(*polylines, viewBox="0 0 400 150", cls="w-full h-40", preserveAspectRatio="none"),
            Div(*legends, cls="flex flex-wrap gap-4 mt-2"),
            data_testid="net-worth-chart",
            cls="cc-glass rounded-xl p-4",
        )

    # Net worth table
    nw_table = ""
    if data.get("nw_table_rows"):
        header_cells = [Th("Account", cls="px-4 py-2 text-left font-medium cc-muted")]
        for m in data["nw_months"]:
            header_cells.append(Th(m, cls="px-3 py-2 text-right font-medium cc-muted"))

        body_rows = []
        for row in data["nw_table_rows"]:
            cells = [Td(row["label"], cls="px-4 py-2 text-base-content")]
            for b in row["balances"]:
                cells.append(Td(b, cls="px-3 py-2 text-right cc-muted"))
            body_rows.append(Tr(*cells, cls="border-b border-base-300/70 hover:bg-base-200/60"))

        nw_table = Div(
            Table(
                Thead(Tr(*header_cells, cls="border-b border-base-300")),
                Tbody(*body_rows),
                cls="table w-full text-sm",
            ),
            data_testid="net-worth-table",
            cls="cc-glass overflow-x-auto rounded-xl",
        )
    else:
        nw_table = P("No net worth data yet. Import account balances or add net worth transactions.", cls="text-sm cc-muted")

    nw_section = Section(
        H2("Net Worth", cls="text-xl font-semibold text-base-content"),
        nw_chart,
        nw_table,
        data_testid="net-worth-section",
        cls="space-y-4",
    )

    return (
        Header(H1("Dashboard", cls="cc-page-title text-4xl font-semibold text-base-content"), cls="space-y-2"),
        summary,
        expenses_section,
        nw_section,
    )
