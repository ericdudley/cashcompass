from fasthtml.common import *
from src.components.layout import crud_page_layout
from src.models import Account


def account_card(acct: Account):
    if acct.account_type == "net_worth":
        type_cls = "badge badge-success badge-soft"
        toggle_label = "→ expenses"
        toggle_type = "expenses"
        toggle_cls = "btn btn-ghost btn-xs"
    else:
        type_cls = "badge badge-warning badge-soft"
        toggle_label = "→ net_worth"
        toggle_type = "net_worth"
        toggle_cls = "btn btn-ghost btn-xs"

    if acct.is_archived:
        archive_btn = Button(
            "Unarchive",
            cls="btn btn-ghost btn-xs",
            title="Unarchive account",
            hx_put=f"/accounts/{acct.id}/archive",
            hx_target="#account-list",
            hx_swap="outerHTML",
        )
    else:
        archive_btn = Button(
            "Archive",
            cls="btn btn-ghost btn-xs",
            title="Archive account",
            hx_put=f"/accounts/{acct.id}/archive",
            hx_target="#account-list",
            hx_swap="outerHTML",
        )

    return Div(
        Div(
            Div(
                P(acct.label, cls="text-sm font-medium text-base-content"),
                Span(
                    acct.account_type,
                    cls=type_cls,
                ),
                cls="flex flex-col gap-1",
            ),
            Button(
                "✎",
                cls="btn btn-ghost btn-sm",
                title="Edit label",
                hx_get=f"/partials/accounts/{acct.id}/edit",
                hx_target=f"#account-{acct.id}",
                hx_swap="outerHTML",
            ),
            cls="flex items-start justify-between gap-2",
        ),
        Div(
            Button(
                toggle_label,
                cls=toggle_cls,
                hx_put=f"/accounts/{acct.id}/type",
                hx_vals=f'{{"account_type":"{toggle_type}"}}',
                hx_target=f"#account-{acct.id}",
                hx_swap="outerHTML",
            ),
            archive_btn,
            Button(
                "Delete",
                cls="btn btn-ghost btn-xs text-error ml-auto",
                hx_delete=f"/accounts/{acct.id}",
                hx_target=f"#account-{acct.id}",
                hx_swap="outerHTML",
                hx_confirm=f"Delete account '{acct.label}'? This cannot be undone.",
            ),
            cls="flex items-center gap-2 flex-wrap",
        ),
        id=f"account-{acct.id}",
        data_label=acct.label,
        data_testid="account-card",
        cls="card cc-glass p-4 flex flex-col gap-3",
    )


def account_card_edit(acct: Account):
    return Div(
        Input(
            type="text",
            id=f"label-{acct.id}",
            name="label",
            value=acct.label,
            autofocus=True,
            onkeydown="if(event.key==='Enter'){event.preventDefault();this.closest('[id^=account-]').querySelector('button[hx-put]').click()}",
            cls="input input-bordered input-sm w-full",
        ),
        Div(
            Button(
                "Save",
                cls="btn btn-primary btn-sm",
                hx_put=f"/accounts/{acct.id}/label",
                hx_include=f"#label-{acct.id}",
                hx_target=f"#account-{acct.id}",
                hx_swap="outerHTML",
            ),
            Button(
                "Cancel",
                cls="btn btn-ghost btn-sm",
                hx_get=f"/partials/accounts/{acct.id}",
                hx_target=f"#account-{acct.id}",
                hx_swap="outerHTML",
            ),
            cls="flex gap-2",
        ),
        id=f"account-{acct.id}",
        data_label=acct.label,
        data_testid="account-card",
        cls="card cc-glass p-4 flex flex-col gap-3",
    )


def accounts_list(active: list[Account], archived: list[Account]):
    active_cards = [account_card(a) for a in active] if active else [
        Div("No active accounts.", cls="rounded-xl border border-dashed border-base-300 p-6 text-sm cc-muted")
    ]

    sections = [
        Section(
            H2("Active", cls="mb-3 text-lg font-semibold text-base-content"),
            Div(*active_cards, cls="grid gap-3 md:grid-cols-2"),
            data_testid="active-accounts",
        )
    ]

    if archived:
        sections.append(
            Section(
                H2("Archived", cls="mb-3 text-lg font-semibold cc-muted"),
                Div(*[account_card(a) for a in archived], cls="grid gap-3 md:grid-cols-2"),
                data_testid="archived-accounts",
            )
        )

    return Div(*sections, id="account-list", cls="flex flex-col gap-8")


def account_form():
    return Div(
        H2("Add Account", cls="text-sm font-semibold text-base-content/80"),
        Form(
            Div(
                Label("Label", fr="account-label", cls="label-text"),
                Input(
                    id="account-label",
                    type="text",
                    name="label",
                    required=True,
                    placeholder="e.g. Checking",
                    cls="input input-bordered w-full",
                ),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Type", fr="account-type", cls="label-text"),
                Select(
                    Option("net_worth", value="net_worth"),
                    Option("expenses", value="expenses"),
                    id="account-type",
                    name="account_type",
                    cls="select select-bordered w-full",
                ),
                cls="flex flex-col gap-1",
            ),
            Div(
                Button(
                    "Add account",
                    type="submit",
                    cls="btn btn-primary w-full sm:w-auto",
                ),
                cls="cc-form-actions",
            ),
            hx_post="/accounts",
            hx_target="#account-list",
            hx_swap="outerHTML",
            hx_on="htmx:afterRequest: if(event.detail.successful) this.reset()",
            cls="cc-form-stack",
        ),
        cls="cc-crud-panel",
    )


def accounts_page(active: list[Account], archived: list[Account]):
    header = Header(
        Div(
            H1("Accounts", cls="cc-page-title text-4xl font-semibold text-base-content"),
            A(
                "Reconcile net worth",
                href="/accounts/reconcile",
                data_testid="accounts-reconcile-link",
                cls="btn btn-secondary btn-sm",
            ),
            cls="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
        ),
        cls="space-y-2",
    )
    return crud_page_layout(
        header,
        account_form(),
        accounts_list(active, archived),
    )
