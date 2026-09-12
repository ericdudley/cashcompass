from __future__ import annotations

from datetime import datetime

from fasthtml.common import *

from src.components.layout import crud_page_layout
from src.models import AnnualIncome
from src.utils.format import cents_dollars, cents_input


def annual_income_card(income: AnnualIncome):
    return Div(
        Div(
            Div(
                H2(str(income.tax_year), cls="text-2xl font-semibold text-base-content"),
                P(
                    f"{cents_dollars(income.after_tax_income_cents)} after listed taxes",
                    cls="text-sm cc-muted",
                ),
                cls="space-y-1",
            ),
            Div(
                A(
                    "View flow",
                    href=f"/flow?year={income.tax_year}",
                    cls="btn btn-primary btn-sm",
                ),
                Button(
                    "Edit",
                    hx_get=f"/partials/income/{income.id}/edit",
                    hx_target=f"#annual-income-{income.id}",
                    hx_swap="outerHTML",
                    cls="btn btn-ghost btn-sm",
                ),
                cls="flex items-center gap-2",
            ),
            cls="flex flex-wrap items-start justify-between gap-4",
        ),
        Div(
            _amount_stat("Gross income", income.gross_income_cents),
            _amount_stat("Federal total tax", income.federal_tax_cents),
            _amount_stat("State total tax", income.state_tax_cents),
            cls="grid grid-cols-1 gap-3 sm:grid-cols-3",
        ),
        *(
            [P(income.notes, cls="whitespace-pre-wrap text-sm cc-muted")]
            if income.notes
            else []
        ),
        Div(
            Button(
                "Delete",
                hx_delete=f"/income/{income.id}",
                hx_target="#annual-income-list",
                hx_swap="outerHTML",
                hx_confirm=f"Delete annual income for {income.tax_year}?",
                cls="btn btn-ghost btn-xs text-error ml-auto",
            ),
            cls="flex",
        ),
        id=f"annual-income-{income.id}",
        data_testid="annual-income-card",
        data_year=str(income.tax_year),
        cls="cc-glass rounded-2xl p-5 space-y-5",
    )


def annual_income_card_edit(income: AnnualIncome):
    return Form(
        Div(
            H2(f"Edit {income.tax_year}", cls="text-lg font-semibold text-base-content"),
            P("Amounts should match the totals reported on that year's returns.", cls="text-xs cc-muted"),
            cls="space-y-1",
        ),
        Div(
            _money_input("Gross income", "gross_income", income.gross_income_cents, required=True),
            _money_input("Federal total tax", "federal_tax", income.federal_tax_cents),
            _money_input("State total tax", "state_tax", income.state_tax_cents),
            cls="grid grid-cols-1 gap-3 sm:grid-cols-3",
        ),
        Label(
            Span("Tax year", cls="label-text"),
            Input(
                type="number",
                name="tax_year",
                value=str(income.tax_year),
                min="1900",
                max="9999",
                required=True,
                cls="input input-bordered w-full",
            ),
            cls="flex flex-col gap-1",
        ),
        Label(
            Span("Notes", cls="label-text"),
            Textarea(income.notes, name="notes", rows="2", cls="textarea textarea-bordered w-full"),
            cls="flex flex-col gap-1",
        ),
        Div(
            Button("Save", type="submit", cls="btn btn-primary btn-sm"),
            Button(
                "Cancel",
                type="button",
                hx_get=f"/partials/income/{income.id}",
                hx_target=f"#annual-income-{income.id}",
                hx_swap="outerHTML",
                cls="btn btn-ghost btn-sm",
            ),
            cls="flex gap-2",
        ),
        id=f"annual-income-{income.id}",
        hx_put=f"/income/{income.id}",
        hx_target="#annual-income-list",
        hx_swap="outerHTML",
        hx_on="htmx:responseError: alert(event.detail.xhr.responseText)",
        data_testid="annual-income-edit-form",
        data_year=str(income.tax_year),
        cls="cc-glass rounded-2xl p-5 space-y-4",
    )


def annual_income_list(incomes: list[AnnualIncome]):
    content = [annual_income_card(income) for income in incomes]
    if not content:
        content = [
            Div(
                H2("No annual income yet", cls="text-lg font-semibold text-base-content"),
                P(
                    "Add a tax year to compare income, taxes, and categorized expenses on the Flow page.",
                    cls="text-sm cc-muted",
                ),
                data_testid="annual-income-empty",
                cls="rounded-2xl border border-dashed border-base-300 p-8 space-y-2",
            )
        ]
    return Div(*content, id="annual-income-list", cls="flex flex-col gap-4")


def annual_income_form(current_year: int | None = None):
    current_year = current_year or datetime.now().year
    return Div(
        Div(
            H2("Add tax year", cls="text-sm font-semibold text-base-content/80"),
            P(
                "Use total tax liability, not withholding. Income after listed taxes is calculated automatically.",
                cls="text-xs cc-muted",
            ),
            cls="space-y-1",
        ),
        Form(
            Label(
                Span("Tax year", cls="label-text"),
                Input(
                    id="income-tax-year",
                    type="number",
                    name="tax_year",
                    value=str(current_year),
                    min="1900",
                    max="9999",
                    required=True,
                    cls="input input-bordered w-full",
                ),
                cls="flex flex-col gap-1",
            ),
            _money_input("Gross income", "gross_income", 0, required=True, input_id="income-gross"),
            _money_input("Federal total tax", "federal_tax", 0, input_id="income-federal-tax"),
            _money_input("State total tax", "state_tax", 0, input_id="income-state-tax"),
            Label(
                Span("Notes (optional)", cls="label-text"),
                Textarea(
                    name="notes",
                    rows="3",
                    placeholder="Return lines used, unusual items, or other context",
                    cls="textarea textarea-bordered w-full",
                ),
                cls="flex flex-col gap-1",
            ),
            Button("Add annual income", type="submit", cls="btn btn-primary w-full sm:w-auto"),
            id="annual-income-form",
            hx_post="/income",
            hx_target="#annual-income-list",
            hx_swap="outerHTML",
            hx_on="htmx:afterRequest: if(event.detail.successful) this.reset(); htmx:responseError: alert(event.detail.xhr.responseText)",
            cls="cc-form-stack",
        ),
        cls="cc-crud-panel",
    )


def annual_income_page(incomes: list[AnnualIncome]):
    header = Header(
        H1("Annual Income", cls="cc-page-title text-4xl font-semibold text-base-content"),
        P(
            "Store one tax-return summary per year. CashCompass uses it for annual Flow reporting.",
            cls="text-sm cc-muted",
        ),
        cls="space-y-2",
    )
    return crud_page_layout(header, annual_income_form(), annual_income_list(incomes))


def _amount_stat(label: str, cents: int):
    return Div(
        P(label, cls="text-xs uppercase tracking-wider cc-subtle"),
        P(cents_dollars(cents), cls="font-mono text-base font-medium text-base-content"),
        cls="rounded-xl bg-base-200/50 p-3 space-y-1",
    )


def _money_input(
    label: str,
    name: str,
    cents: int,
    required: bool = False,
    input_id: str = "",
):
    return Label(
        Span(label, cls="label-text"),
        Input(
            id=input_id or None,
            type="number",
            name=name,
            value=cents_input(cents) if cents else "",
            placeholder="0.00",
            min="0",
            step="0.01",
            required=required,
            cls="input input-bordered w-full",
        ),
        cls="flex flex-col gap-1",
    )
