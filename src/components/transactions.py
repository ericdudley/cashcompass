from fasthtml.common import *
from src.models import Transaction, Category, Account
from src.utils.format import cents_display, cents_input
from src.utils.dates import fmt_date

PRESETS = [
    ("this_month", "This Month"),
    ("last_month", "Last Month"),
    ("this_year", "This Year"),
    ("all_time", "All Time"),
]


def transaction_row(txn: Transaction):
    amt_cls = "text-red-400" if txn.amount < 0 else "text-emerald-400"
    label_content = txn.label if txn.label else Span("—", cls="text-slate-500")
    acct_content = txn.account_label if txn.account_label else "—"
    cat_content = txn.category_label if txn.category_label else "—"

    return Div(
        Span(cents_display(txn.amount), cls=f"w-20 sm:w-24 shrink-0 text-right font-mono font-medium {amt_cls}"),
        Span(label_content, cls="flex-1 min-w-0 truncate text-slate-100"),
        Span(acct_content, cls="hidden sm:block w-32 shrink-0 truncate text-slate-400"),
        Span(cat_content, cls="hidden sm:block w-28 shrink-0 truncate text-slate-400"),
        Div(
            Button(
                "Edit",
                hx_get=f"/partials/transactions/{txn.id}/edit",
                hx_target=f"#transaction-{txn.id}",
                hx_swap="outerHTML",
                cls="text-xs px-2 py-1 bg-slate-700 text-slate-300 rounded hover:bg-slate-600",
            ),
            Button(
                "Delete",
                hx_delete=f"/transactions/{txn.id}",
                hx_target="#transaction-list",
                hx_swap="outerHTML",
                hx_include="#transaction-filters",
                hx_confirm="Delete this transaction?",
                cls="text-xs px-2 py-1 bg-red-900/50 text-red-400 rounded hover:bg-red-900",
            ),
            cls="flex gap-2 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity",
        ),
        id=f"transaction-{txn.id}",
        data_testid="transaction-row",
        cls="flex items-center gap-2 sm:gap-4 px-4 py-3 text-sm group hover:bg-slate-800/50",
    )


def transaction_row_edit(txn: Transaction, accounts: list[Account], categories: list[Category]):
    iso_date = txn.iso8601[:10] if txn.iso8601 else txn.date.replace("_", "-")[:10]

    acct_options = [
        Option(a.label, value=str(a.id), selected=(a.id == txn.account_id))
        for a in accounts
    ]
    cat_options = [Option("None", value="0", selected=(txn.category_id is None))] + [
        Option(c.label, value=str(c.id), selected=(c.id == txn.category_id))
        for c in categories
    ]

    return Div(
        Input(type="date", name="date", value=iso_date,
              cls="w-32 text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
        Input(type="text", name="label", value=txn.label,
              cls="flex-1 text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
        Div(
            Input(type="number", name="amount", value=cents_input(txn.amount), step="0.01", min="0",
                  cls="w-24 text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
            Select(
                Option("Debit", value="debit", selected=(txn.amount < 0)),
                Option("Credit", value="credit", selected=(txn.amount >= 0)),
                name="amount_mode",
                cls="text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1",
            ),
            cls="flex items-center gap-1",
        ),
        Select(*acct_options, name="account_id",
               cls="w-32 text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
        Select(*cat_options, name="category_id",
               cls="w-28 text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
        Button(
            "Save",
            hx_put=f"/transactions/{txn.id}",
            hx_include=f"#transaction-{txn.id} input, #transaction-{txn.id} select",
            hx_target=f"#transaction-{txn.id}",
            hx_swap="outerHTML",
            cls="text-xs px-2 py-1 bg-emerald-900/50 text-emerald-400 rounded hover:bg-emerald-900",
        ),
        Button(
            "Cancel",
            hx_get=f"/partials/transactions/{txn.id}",
            hx_target=f"#transaction-{txn.id}",
            hx_swap="outerHTML",
            cls="text-xs px-2 py-1 bg-slate-700 text-slate-300 rounded hover:bg-slate-600",
        ),
        id=f"transaction-{txn.id}",
        data_testid="transaction-row-edit",
        onkeydown="if(event.key==='Enter'&&event.target.tagName==='INPUT'){event.preventDefault();this.querySelector('button[hx-put]').click()}",
        cls="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-emerald-400/20 bg-slate-800/70",
    )


def transaction_form(accounts: list[Account], categories: list[Category],
                     today: str, last_account_id: int, account_type: str):
    acct_options = [
        Option(a.label, value=str(a.id), selected=(a.id == last_account_id))
        for a in accounts
    ]
    cat_options = [Option("None", value="0")] + [
        Option(c.label, value=str(c.id)) for c in categories
    ]

    return Div(
        H2("Add Transaction", cls="text-sm font-semibold text-slate-300 mb-3"),
        Form(
            Input(type="hidden", name="account_type", value=account_type),
            Div(
                Label("Date", cls="text-xs text-slate-500"),
                Input(type="date", name="date", value=today, required=True,
                      cls="text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Label", cls="text-xs text-slate-500"),
                Input(type="text", name="label", placeholder="Description", required=True,
                      cls="text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
                cls="flex flex-col gap-1 flex-1 min-w-32",
            ),
            Div(
                Label("Amount", cls="text-xs text-slate-500"),
                Div(
                    Input(type="number", name="amount", placeholder="0.00", step="0.01", min="0", required=True,
                          cls="w-24 text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
                    Select(
                        Option("Debit", value="debit"),
                        Option("Credit", value="credit"),
                        name="amount_mode",
                        cls="text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1",
                    ),
                    cls="flex gap-1",
                ),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Account", cls="text-xs text-slate-500"),
                Select(*acct_options, name="account_id", required=True,
                       cls="text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Category", cls="text-xs text-slate-500"),
                Select(*cat_options, name="category_id",
                       cls="text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1"),
                cls="flex flex-col gap-1",
            ),
            Button("Add", type="submit",
                   cls="px-3 py-1.5 bg-emerald-600 text-white text-sm rounded hover:bg-emerald-700"),
            id="transaction-form",
            hx_post="/transactions",
            hx_target="#transaction-list",
            hx_swap="outerHTML",
            hx_on="htmx:afterRequest: if(event.detail.successful){ var d=this.querySelector('[name=date]').value; this.reset(); this.querySelector('[name=date]').value=d; }",
            cls="flex flex-wrap items-end gap-3",
        ),
        cls="rounded-xl border border-slate-800 bg-slate-900/70 p-4 mb-4",
    )


def transactions_list(groups: list, f, categories: list[Category]):
    mode = f.account_type

    # Mode toggle
    expenses_cls = "px-4 py-1.5 rounded text-sm font-medium bg-amber-500 text-white" if mode == "expenses" else "px-4 py-1.5 rounded text-sm font-medium bg-slate-700 text-slate-300 hover:bg-slate-600"
    nw_cls = "px-4 py-1.5 rounded text-sm font-medium bg-emerald-500 text-white" if mode == "net_worth" else "px-4 py-1.5 rounded text-sm font-medium bg-slate-700 text-slate-300 hover:bg-slate-600"

    exp_href = f"/transactions?account_type=expenses"
    if f.date_preset:
        exp_href += f"&date_preset={f.date_preset}"
    if f.label:
        exp_href += f"&label={f.label}"

    nw_href = f"/transactions?account_type=net_worth"
    if f.date_preset:
        nw_href += f"&date_preset={f.date_preset}"
    if f.label:
        nw_href += f"&label={f.label}"

    mode_toggle = Div(
        A("Expenses", href=exp_href, cls=expenses_cls),
        A("Net Worth", href=nw_href, cls=nw_cls),
        cls="flex gap-1 mb-4",
    )

    # Preset buttons
    preset_btns = []
    for preset_val, preset_label in PRESETS:
        is_active = f.date_preset == preset_val
        btn_cls = "text-xs px-3 py-1 rounded-full border bg-emerald-600 text-white border-emerald-600" if is_active else "text-xs px-3 py-1 rounded-full border bg-slate-800 text-slate-400 border-slate-600 hover:border-emerald-400/50"
        preset_btns.append(Button(
            preset_label,
            type="button",
            hx_get="/partials/transactions",
            hx_vals=f'{{"date_preset":"{preset_val}"}}',
            hx_include="#transaction-filters",
            hx_target="#transaction-list",
            hx_swap="outerHTML",
            cls=btn_cls,
        ))

    # Category checkboxes
    cat_pills = []
    for cat in categories:
        is_checked = cat.id in (f.category_ids or [])
        pill_cls = "text-xs px-2 py-1 rounded-full border transition-colors bg-emerald-600 text-white border-emerald-600" if is_checked else "text-xs px-2 py-1 rounded-full border transition-colors bg-slate-800 text-slate-400 border-slate-600 hover:border-emerald-400/50"
        cat_pills.append(
            Label(
                Input(type="checkbox", name="category_id", value=str(cat.id),
                      checked=is_checked, cls="sr-only"),
                Span(cat.label, cls=pill_cls),
                cls="cursor-pointer",
            )
        )

    filter_form = Form(
        Input(type="hidden", name="account_type", value=mode),
        Div(*preset_btns, cls="flex flex-wrap gap-2 mb-3"),
        Div(
            Input(type="text", name="label", id="label-search", value=f.label or "",
                  placeholder="Search label...",
                  cls="text-sm bg-slate-900 border border-slate-600 text-slate-100 rounded px-2 py-1 flex-1 min-w-40"),
            Div(*cat_pills, cls="flex flex-wrap gap-1"),
            cls="flex flex-wrap gap-3 items-center",
        ),
        id="transaction-filters",
        hx_get="/partials/transactions",
        hx_trigger="change, keyup changed delay:300ms from:#label-search",
        hx_target="#transaction-list",
        hx_swap="outerHTML",
        cls="rounded-xl border border-slate-800 bg-slate-900/70 p-4 mb-4",
    )

    # Transaction groups
    group_sections = []
    for g in groups:
        sub_cls = "text-xs font-mono text-red-400" if g["subtotal"] < 0 else "text-xs font-mono text-emerald-400"
        rows = [transaction_row(t) for t in g["transactions"]]
        group_sections.append(
            Section(
                Div(
                    H2(fmt_date(g["date"]), cls="text-xs font-semibold uppercase tracking-widest text-slate-500"),
                    Span(cents_display(g["subtotal"]), cls=sub_cls),
                    cls="flex justify-between items-center mb-2",
                ),
                Div(*rows, cls="flex flex-col divide-y divide-slate-800 rounded-xl border border-slate-800 bg-slate-900/50"),
            )
        )

    if not groups:
        group_sections = [
            Div("No transactions found.", cls="rounded-xl border border-dashed border-slate-700 p-6 text-sm text-slate-400")
        ]

    return Div(
        mode_toggle,
        filter_form,
        Div(*group_sections, cls="flex flex-col gap-6"),
        id="transaction-list",
        data_testid="transaction-list",
    )


def transactions_page(groups, f, categories, form_data):
    return (
        Header(H1("Transactions", cls="text-4xl font-semibold text-white"), cls="space-y-2"),
        transaction_form(
            form_data["accounts"],
            form_data["categories"],
            form_data["today"],
            form_data["last_account_id"],
            form_data["account_type"],
        ),
        transactions_list(groups, f, categories),
    )
