from fasthtml.common import *
from src.components.layout import crud_page_layout
from src.models import Transaction, Category, Account
from src.services.category_recommendation import RecommendationResult
from src.utils.format import cents_display, cents_input
from src.utils.dates import fmt_date

PRESETS = [
    ("this_month", "This Month"),
    ("last_month", "Last Month"),
    ("this_year", "This Year"),
    ("all_time", "All Time"),
]


def transaction_row(txn: Transaction):
    amt_cls = "text-error" if txn.amount < 0 else "text-success"
    label_content = txn.label if txn.label else Span("—", cls="cc-subtle")
    acct_content = txn.account_label if txn.account_label else "—"
    cat_content = txn.category_label if txn.category_label else "—"

    return Div(
        Span(cents_display(txn.amount), cls=f"w-20 sm:w-24 shrink-0 text-right font-mono font-medium {amt_cls}"),
        Span(label_content, cls="flex-1 min-w-0 truncate text-base-content"),
        Span(acct_content, cls="hidden sm:block w-32 shrink-0 truncate cc-muted"),
        Span(cat_content, cls="hidden sm:block w-28 shrink-0 truncate cc-muted"),
        Div(
            Button(
                "Edit",
                hx_get=f"/partials/transactions/{txn.id}/edit",
                hx_target=f"#transaction-{txn.id}",
                hx_swap="outerHTML",
                cls="btn btn-ghost btn-xs",
            ),
            Button(
                "Delete",
                hx_delete=f"/transactions/{txn.id}",
                hx_target="#transaction-list",
                hx_swap="outerHTML",
                hx_include="#transaction-filters",
                hx_confirm="Delete this transaction?",
                cls="btn btn-ghost btn-xs text-error",
            ),
            cls="flex gap-2 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity",
        ),
        id=f"transaction-{txn.id}",
        data_testid="transaction-row",
        cls="flex items-center gap-2 sm:gap-4 px-4 py-3 text-sm group hover:bg-base-200/60",
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
              cls="input input-bordered input-sm w-32"),
        Input(type="text", name="label", value=txn.label,
              cls="input input-bordered input-sm flex-1"),
        Div(
            Input(type="number", name="amount", value=cents_input(txn.amount), step="0.01", min="0",
                  cls="input input-bordered input-sm w-24"),
            Select(
                Option("Debit", value="debit", selected=(txn.amount < 0)),
                Option("Credit", value="credit", selected=(txn.amount >= 0)),
                name="amount_mode",
                cls="select select-bordered select-sm",
            ),
            cls="flex items-center gap-1",
        ),
        Select(*acct_options, name="account_id",
               cls="select select-bordered select-sm w-32"),
        Select(*cat_options, name="category_id",
               cls="select select-bordered select-sm w-28"),
        Button(
            "Save",
            hx_put=f"/transactions/{txn.id}",
            hx_include=f"#transaction-{txn.id} input, #transaction-{txn.id} select, #transaction-filters",
            hx_target="#transaction-list",
            hx_swap="outerHTML",
            cls="btn btn-primary btn-xs",
        ),
        Button(
            "Cancel",
            hx_get=f"/partials/transactions/{txn.id}",
            hx_target=f"#transaction-{txn.id}",
            hx_swap="outerHTML",
            cls="btn btn-ghost btn-xs",
        ),
        id=f"transaction-{txn.id}",
        data_testid="transaction-row-edit",
        onkeydown="if(event.key==='Enter'&&event.target.tagName==='INPUT'){event.preventDefault();this.querySelector('button[hx-put]').click()}",
        cls="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-base-300 bg-base-200/70",
    )


def transaction_category_recommendation_panel(
    ai_enabled: bool,
    recommendation: RecommendationResult | None = None,
):
    if not ai_enabled:
        return None

    recommendation = recommendation or RecommendationResult()
    content = []
    if recommendation.has_recommendation:
        content.extend([
            Span("AI:", cls="text-xs font-semibold uppercase tracking-wide cc-subtle"),
            Span(recommendation.category_label, cls="text-sm font-medium text-base-content", data_testid="transaction-category-label"),
            Button(
                "Use",
                type="button",
                cls="btn btn-xs btn-ghost",
                data_category_id=str(recommendation.category_id),
                data_testid="transaction-category-apply",
                onclick="""
                const form = document.getElementById('transaction-form');
                const select = form?.querySelector('select[name="category_id"]');
                if (!select) return;
                select.value = this.dataset.categoryId || '0';
                select.dispatchEvent(new Event('change', { bubbles: true }));
                """,
            ),
        ])

    return Div(
        *content,
        id="transaction-category-recommendation",
        data_testid="transaction-category-recommendation",
        cls="flex min-h-9 items-center gap-2 text-sm sm:shrink-0",
    )


def _recommendation_request_attrs(trigger: str, ai_enabled: bool) -> dict:
    if not ai_enabled:
        return {}
    return {
        "hx_post": "/partials/transactions/recommend-category",
        "hx_target": "#transaction-category-recommendation",
        "hx_swap": "outerHTML",
        "hx_include": "#transaction-form input[name='date'], #transaction-form input[name='label'], #transaction-form input[name='amount'], #transaction-form select[name='amount_mode'], #transaction-form select[name='category_id']",
        "hx_trigger": trigger,
    }


def transaction_form(accounts: list[Account], categories: list[Category],
                     today: str, last_account_id: int, account_type: str, ai_enabled: bool = False):
    acct_options = [
        Option(a.label, value=str(a.id), selected=(a.id == last_account_id))
        for a in accounts
    ]
    cat_options = [Option("None", value="0")] + [
        Option(c.label, value=str(c.id)) for c in categories
    ]
    recommendation_panel = transaction_category_recommendation_panel(ai_enabled)

    return Div(
        H2("Add Transaction", cls="text-sm font-semibold text-base-content/80"),
        Form(
            Input(type="hidden", name="account_type", value=account_type),
            Div(
                Label("Date", cls="label-text"),
                Input(type="date", name="date", value=today, required=True,
                      cls="input input-bordered w-full",
                      **_recommendation_request_attrs("change", ai_enabled)),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Label", cls="label-text"),
                Input(type="text", name="label", placeholder="Description", required=True,
                      cls="input input-bordered w-full",
                      **_recommendation_request_attrs("input changed delay:500ms", ai_enabled)),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Amount", cls="label-text"),
                Div(
                    Input(type="number", name="amount", placeholder="0.00", step="0.01", min="0", required=True,
                          cls="input input-bordered w-full",
                          **_recommendation_request_attrs("input changed delay:500ms", ai_enabled)),
                    Select(
                        Option("Debit", value="debit"),
                        Option("Credit", value="credit"),
                        name="amount_mode",
                        cls="select select-bordered w-full",
                        **_recommendation_request_attrs("change", ai_enabled),
                    ),
                    cls="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]",
                ),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Category", cls="label-text"),
                Div(
                    Select(*cat_options, name="category_id",
                           cls="select select-bordered w-full",
                           **_recommendation_request_attrs("change", ai_enabled)),
                    *([recommendation_panel] if recommendation_panel is not None else []),
                    cls="flex flex-col gap-1",
                ),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Account", cls="label-text"),
                Select(*acct_options, name="account_id", required=True,
                       cls="select select-bordered w-full"),
                cls="flex flex-col gap-1",
            ),
            Div(
                Button("Add", type="submit", cls="btn btn-primary w-full sm:w-auto"),
                cls="cc-form-actions",
            ),
            id="transaction-form",
            hx_post="/transactions",
            hx_target="#transaction-list",
            hx_swap="outerHTML",
            hx_on="""
            htmx:afterRequest:
            if(event.detail.successful){
              var d=this.querySelector('[name=date]').value;
              this.reset();
              this.querySelector('[name=date]').value=d;
              var recommendation = document.getElementById('transaction-category-recommendation');
              if(recommendation){
                recommendation.innerHTML = '';
              }
            }
            """,
            cls="cc-form-stack",
        ),
        cls="cc-crud-panel",
    )


def transactions_list(groups: list, f, categories: list[Category]):
    mode = f.account_type

    # Mode toggle
    expenses_cls = "join-item btn btn-sm btn-warning" if mode == "expenses" else "join-item btn btn-sm btn-ghost"
    nw_cls = "join-item btn btn-sm btn-success" if mode == "net_worth" else "join-item btn btn-sm btn-ghost"

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
        cls="join mb-4",
    )

    # Preset buttons
    preset_btns = []
    for preset_val, preset_label in PRESETS:
        is_active = f.date_preset == preset_val
        btn_cls = "btn btn-xs btn-primary" if is_active else "btn btn-xs btn-ghost"
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
        pill_cls = "badge badge-primary badge-soft px-3 py-3" if is_checked else "badge badge-outline px-3 py-3"
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
                  cls="input input-bordered input-sm flex-1 min-w-40"),
            Div(*cat_pills, cls="flex flex-wrap gap-1"),
            cls="flex flex-wrap gap-3 items-center",
        ),
        id="transaction-filters",
        hx_get="/partials/transactions",
        hx_trigger="change, keyup changed delay:300ms from:#label-search",
        hx_target="#transaction-list",
        hx_swap="outerHTML",
        cls="cc-glass rounded-xl p-4 mb-4",
    )

    # Transaction groups
    group_sections = []
    for g in groups:
        sub_cls = "text-xs font-mono text-error" if g["subtotal"] < 0 else "text-xs font-mono text-success"
        rows = [transaction_row(t) for t in g["transactions"]]
        group_sections.append(
            Section(
                Div(
                    H2(fmt_date(g["date"]), cls="text-xs font-semibold uppercase tracking-widest cc-subtle"),
                    Span(cents_display(g["subtotal"]), cls=sub_cls, data_testid="transaction-subtotal"),
                    cls="flex justify-between items-center mb-2",
                ),
                Div(*rows, cls="cc-glass flex flex-col divide-y divide-base-300 rounded-xl"),
                data_date=fmt_date(g["date"]),
                data_testid="transaction-group",
            )
        )

    if not groups:
        group_sections = [
            Div("No transactions found.", cls="rounded-xl border border-dashed border-base-300 p-6 text-sm cc-muted")
        ]

    return Div(
        mode_toggle,
        filter_form,
        Div(*group_sections, cls="flex flex-col gap-6"),
        id="transaction-list",
        data_testid="transaction-list",
    )


def transactions_page(groups, f, categories, form_data):
    header = Header(H1("Transactions", cls="cc-page-title text-4xl font-semibold text-base-content"), cls="space-y-2")
    return crud_page_layout(
        header,
        transaction_form(
            form_data["accounts"],
            form_data["categories"],
            form_data["today"],
            form_data["last_account_id"],
            form_data["account_type"],
            form_data.get("ai_enabled", False),
        ),
        transactions_list(groups, f, categories),
    )
