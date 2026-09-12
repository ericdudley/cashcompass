from __future__ import annotations

import json

from fasthtml.common import *

from src.utils.format import cents_dollars


def flow_page(data: dict):
    header = Header(
        Div(
            Div(
                H1("Flow", cls="cc-page-title text-4xl font-semibold text-base-content"),
                P(
                    "See how annual gross income moves through taxes, categorized expenses, and what remains.",
                    cls="text-sm cc-muted",
                ),
                cls="space-y-2",
            ),
            _year_selector(data),
            cls="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between",
        )
    )

    if not data["has_income"]:
        return (
            header,
            Div(
                H2(f"No income summary for {data['selected_year']}", cls="text-xl font-semibold text-base-content"),
                P(
                    "Add gross income and federal and state total tax for this year to build its flow.",
                    cls="text-sm cc-muted",
                ),
                A(
                    "Add annual income",
                    href="/income",
                    cls="btn btn-primary btn-sm self-start",
                ),
                data_testid="flow-empty-income",
                cls="cc-glass rounded-2xl p-8 flex flex-col gap-3",
            ),
        )

    result_label = "Left Over" if data["shortfall"] == 0 else "Savings / Debt Used"
    result_value = data["left_over_fmt"] if data["shortfall"] == 0 else data["shortfall_fmt"]
    result_cls = "text-success" if data["shortfall"] == 0 else "text-warning"

    summary = Section(
        _summary_stat("Gross Income", data["gross_income_fmt"], data["tax_rate"] + " combined tax"),
        _summary_stat("Listed Taxes", data["combined_tax_fmt"], "Federal + state"),
        _summary_stat("Net Expenses", data["net_expenses_fmt"], "Expense credits included"),
        _summary_stat(result_label, result_value, "After listed taxes and expenses", result_cls),
        data_testid="flow-summary",
        cls="grid grid-cols-2 gap-4 lg:grid-cols-4",
    )

    comparison = _net_worth_comparison(data)

    graph_json = json.dumps(data["graph"], separators=(",", ":"))
    chart = Section(
        Div(
            Div(
                data_flow_graph=graph_json,
                data_testid="flow-chart",
                aria_label=f"Income flow for {data['selected_year']}",
                cls="cc-flow-chart",
            ),
            cls="cc-flow-scroll",
        ),
        Div(
            Span(cls="inline-block h-3 w-3 rounded-sm bg-success"),
            Span("Income / left over", cls="text-xs cc-muted"),
            Span(cls="inline-block h-3 w-3 rounded-sm bg-error ml-2"),
            Span("Taxes / expenses", cls="text-xs cc-muted"),
            Span(cls="inline-block h-3 w-3 rounded-sm bg-warning ml-2"),
            Span("Shortfall funding", cls="text-xs cc-muted"),
            cls="flex flex-wrap items-center gap-2",
        ),
        P(
            "Hover or focus a node to trace its path. Select an expense category to open its transactions.",
            cls="text-xs cc-subtle",
        ),
        Div(
            id="flow-tooltip",
            data_testid="flow-tooltip",
            role="status",
            cls="cc-flow-tooltip cc-glass hidden",
        ),
        data_testid="flow-chart-section",
        cls="cc-glass relative min-w-0 rounded-2xl p-4 sm:p-6 space-y-4",
    )

    table = _flow_table(data)
    return (
        header,
        summary,
        comparison,
        chart,
        table,
        P(
            "Income after listed taxes is not the same as paycheck take-home pay. Payroll taxes, benefits, and retirement deductions are outside this annual summary.",
            data_testid="flow-method-note",
            cls="text-xs cc-subtle",
        ),
        Script(src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"),
        Script(src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12.3/dist/d3-sankey.min.js"),
        Script(src="/static/flow.js"),
    )


def _year_selector(data: dict):
    years = list(data["years"])
    if data["selected_year"] not in years:
        years.append(data["selected_year"])
        years.sort(reverse=True)
    return Form(
        Label(
            Span("Tax year", cls="text-xs font-medium cc-muted"),
            Select(
                *[
                    Option(str(year), value=str(year), selected=(year == data["selected_year"]))
                    for year in years
                ],
                name="year",
                onchange="this.form.submit()",
                data_testid="flow-year-select",
                cls="select select-bordered select-sm w-32",
            ),
            cls="flex flex-col gap-1",
        ),
        method="get",
        action="/flow",
    )


def _summary_stat(label: str, value: str, detail: str, value_cls: str = ""):
    return Div(
        P(label, cls="text-xs uppercase tracking-wider cc-subtle"),
        P(value, cls=f"text-xl font-semibold text-base-content {value_cls}".strip()),
        P(detail, cls="text-xs cc-muted"),
        cls="cc-glass rounded-xl p-4 space-y-1",
    )


def _net_worth_comparison(data: dict):
    has_activity = data["has_net_worth_activity"]
    status = data["net_worth_comparison_status"]
    status_label = {
        "more": "Above cash flow",
        "less": "Below cash flow",
        "matched": "Matched",
        "unavailable": "Comparison unavailable",
    }[status]
    status_cls = {
        "more": "text-success border-success/30 bg-success/10",
        "less": "text-warning border-warning/30 bg-warning/10",
        "matched": "text-success border-success/30 bg-success/10",
        "unavailable": "cc-muted border-base-300 bg-base-200/50",
    }[status]
    net_worth_row = (
        _comparison_bar(
            "Net Worth Change",
            data["net_worth_change_fmt"],
            data["net_worth_change"],
            data["net_worth_comparison_scale"],
            "bg-info",
            "flow-comparison-net-worth",
        )
        if has_activity
        else Div(
            Div(
                P("Net Worth Change", cls="text-sm font-medium text-base-content"),
                P("Not available", cls="text-sm font-semibold cc-muted"),
                cls="flex items-baseline justify-between gap-4",
            ),
            Div(
                "No recorded net-worth activity",
                cls="flex h-8 items-center justify-center rounded-lg border border-dashed border-base-300 text-xs cc-subtle",
            ),
            data_testid="flow-comparison-net-worth",
            cls="space-y-2",
        )
    )

    return Section(
        Div(
            Div(
                H2("Left over vs. net worth", cls="text-xl font-semibold text-base-content"),
                P(
                    "Compare the year's cash-flow result with its recorded change in total net worth.",
                    cls="text-sm cc-muted",
                ),
                cls="space-y-1",
            ),
            Span(
                status_label,
                data_comparison_status=status,
                cls=f"rounded-full border px-3 py-1 text-xs font-medium {status_cls}",
            ),
            cls="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between",
        ),
        Div(
            _comparison_bar(
                data["cash_flow_label"],
                data["cash_flow_result_fmt"],
                data["cash_flow_result"],
                data["net_worth_comparison_scale"],
                "bg-success" if data["cash_flow_result"] >= 0 else "bg-warning",
                "flow-comparison-cash-result",
            ),
            net_worth_row,
            cls="grid gap-5 lg:grid-cols-2",
        ),
        Div(
            Span("Decrease / shortfall", cls="text-[11px] cc-subtle"),
            Span("0", cls="text-[11px] cc-subtle"),
            Span("Increase / left over", cls="text-[11px] cc-subtle"),
            cls="grid grid-cols-3 text-center",
        ),
        Div(
            P(
                data["net_worth_comparison_message"],
                data_testid="flow-comparison-message",
                cls="text-sm font-medium text-base-content",
            ),
            P(
                "Based on recorded activity across all net-worth accounts. Differences can reflect market returns, account-value changes, untracked cash flow, or timing.",
                cls="text-xs cc-subtle",
            ),
            cls="space-y-1",
        ),
        data_testid="flow-net-worth-comparison",
        cls="cc-glass rounded-2xl p-4 sm:p-6 space-y-5",
    )


def _comparison_bar(
    label: str,
    value_fmt: str,
    value: int,
    scale: int,
    color_cls: str,
    test_id: str,
):
    width = abs(value) / scale * 50 if scale else 0
    if value > 0:
        bar_style = f"left:50%;width:{width:.1f}%"
    elif value < 0:
        bar_style = f"right:50%;width:{width:.1f}%"
    else:
        bar_style = "left:calc(50% - 1px);width:2px"

    return Div(
        Div(
            P(label, cls="text-sm font-medium text-base-content"),
            P(value_fmt, cls="text-sm font-semibold font-mono text-base-content"),
            cls="flex items-baseline justify-between gap-4",
        ),
        Div(
            Span(cls="absolute inset-y-0 left-1/2 w-px bg-base-content/25"),
            Span(
                style=bar_style,
                cls=f"absolute inset-y-1 rounded-md {color_cls}",
            ),
            role="img",
            aria_label=f"{label}: {value_fmt}",
            cls="relative h-8 overflow-hidden rounded-lg bg-base-200/70",
        ),
        data_testid=test_id,
        data_comparison_value=str(value),
        cls="space-y-2",
    )


def _flow_table(data: dict):
    rows = [
        ("Gross income", data["gross_income_fmt"], "Income"),
        ("Federal total tax", data["federal_tax_fmt"], "Tax"),
        ("State total tax", data["state_tax_fmt"], "Tax"),
        ("Income after listed taxes", data["after_tax_income_fmt"], "Available"),
    ]
    rows.extend((row["label"], row["amount_fmt"], "Expense") for row in data["categories"])
    if data["refunds"]:
        rows.append(("Expense refunds / credits", data["refunds_fmt"], "Inflow"))
    if data["shortfall"]:
        rows.append(("Savings / debt used", data["shortfall_fmt"], "Shortfall"))
    else:
        rows.append(("Left over", data["left_over_fmt"], "Result"))
    if data["has_net_worth_activity"]:
        rows.extend([
            ("Net worth change", data["net_worth_change_fmt"], "Comparison"),
            ("Difference from cash flow", data["net_worth_difference_fmt"], "Comparison"),
        ])

    return Section(
        Div(
            H2("Flow details", cls="text-xl font-semibold text-base-content"),
            P("Exact values used to construct the diagram and comparison.", cls="text-sm cc-muted"),
            cls="space-y-1",
        ),
        Div(
            Table(
                Thead(
                    Tr(
                        Th("Item", cls="px-4 py-3 text-left font-medium cc-muted"),
                        Th("Type", cls="px-4 py-3 text-left font-medium cc-muted"),
                        Th("Amount", cls="px-4 py-3 text-right font-medium cc-muted"),
                        cls="border-b border-base-300",
                    )
                ),
                Tbody(
                    *[
                        Tr(
                            Td(label, cls="px-4 py-3 text-base-content"),
                            Td(kind, cls="px-4 py-3 cc-muted"),
                            Td(amount, cls="px-4 py-3 text-right font-mono text-base-content"),
                            cls="border-b border-base-300/60 last:border-0",
                        )
                        for label, amount, kind in rows
                    ]
                ),
                cls="table w-full text-sm",
            ),
            cls="cc-glass overflow-x-auto rounded-xl",
        ),
        data_testid="flow-details",
        cls="space-y-4",
    )
