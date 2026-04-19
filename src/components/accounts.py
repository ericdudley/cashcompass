from fasthtml.common import *
from src.models import Account


def account_card(acct: Account):
    if acct.account_type == "net_worth":
        type_cls = "bg-emerald-400/10 text-emerald-400"
        toggle_label = "→ expenses"
        toggle_type = "expenses"
        toggle_cls = "rounded px-2 py-1 text-xs text-slate-400 border border-slate-700 hover:border-amber-400/50 hover:text-amber-400 transition"
    else:
        type_cls = "bg-amber-400/10 text-amber-400"
        toggle_label = "→ net_worth"
        toggle_type = "net_worth"
        toggle_cls = "rounded px-2 py-1 text-xs text-slate-400 border border-slate-700 hover:border-emerald-400/50 hover:text-emerald-400 transition"

    if acct.is_archived:
        archive_btn = Button(
            "Unarchive",
            cls="rounded px-2 py-1 text-xs text-slate-400 border border-slate-700 hover:border-emerald-400/50 hover:text-emerald-400 transition",
            title="Unarchive account",
            hx_put=f"/accounts/{acct.id}/archive",
            hx_target="#account-list",
            hx_swap="outerHTML",
        )
    else:
        archive_btn = Button(
            "Archive",
            cls="rounded px-2 py-1 text-xs text-slate-400 border border-slate-700 hover:border-slate-400/50 transition",
            title="Archive account",
            hx_put=f"/accounts/{acct.id}/archive",
            hx_target="#account-list",
            hx_swap="outerHTML",
        )

    return Div(
        Div(
            Div(
                P(acct.label, cls="text-sm font-medium text-slate-100"),
                Span(
                    acct.account_type,
                    cls=f"inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold {type_cls}",
                ),
                cls="flex flex-col gap-1",
            ),
            Button(
                "✎",
                cls="rounded p-1 text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition",
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
                cls="rounded px-2 py-1 text-xs text-red-400/70 border border-slate-700 hover:border-red-400/50 hover:text-red-400 transition ml-auto",
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
        cls="relative rounded-xl border border-emerald-200/20 bg-slate-900/70 p-4 flex flex-col gap-3",
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
            cls="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-400 focus:outline-none",
        ),
        Div(
            Button(
                "Save",
                cls="rounded px-3 py-1.5 text-xs font-semibold bg-emerald-400 text-slate-950 hover:bg-emerald-300 transition",
                hx_put=f"/accounts/{acct.id}/label",
                hx_include=f"#label-{acct.id}",
                hx_target=f"#account-{acct.id}",
                hx_swap="outerHTML",
            ),
            Button(
                "Cancel",
                cls="rounded px-3 py-1.5 text-xs text-slate-400 border border-slate-700 hover:text-slate-100 transition",
                hx_get=f"/partials/accounts/{acct.id}",
                hx_target=f"#account-{acct.id}",
                hx_swap="outerHTML",
            ),
            cls="flex gap-2",
        ),
        id=f"account-{acct.id}",
        data_label=acct.label,
        data_testid="account-card",
        cls="rounded-xl border border-emerald-400/40 bg-slate-900/70 p-4 flex flex-col gap-3",
    )


def accounts_list(active: list[Account], archived: list[Account]):
    active_cards = [account_card(a) for a in active] if active else [
        Div("No active accounts.", cls="rounded-xl border border-dashed border-slate-700 p-6 text-sm text-slate-400")
    ]

    sections = [
        Section(
            H2("Active", cls="mb-3 text-lg font-semibold text-slate-200"),
            Div(*active_cards, cls="grid gap-3 md:grid-cols-2"),
            data_testid="active-accounts",
        )
    ]

    if archived:
        sections.append(
            Section(
                H2("Archived", cls="mb-3 text-lg font-semibold text-slate-400"),
                Div(*[account_card(a) for a in archived], cls="grid gap-3 md:grid-cols-2"),
                data_testid="archived-accounts",
            )
        )

    return Div(*sections, id="account-list", cls="flex flex-col gap-8")


def account_form():
    return Form(
        Div(
            Label("Label", fr="account-label", cls="text-xs text-slate-400"),
            Input(
                id="account-label",
                type="text",
                name="label",
                required=True,
                placeholder="e.g. Checking",
                cls="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-400 focus:outline-none",
            ),
            cls="flex flex-col gap-1",
        ),
        Div(
            Label("Type", fr="account-type", cls="text-xs text-slate-400"),
            Select(
                Option("net_worth", value="net_worth"),
                Option("expenses", value="expenses"),
                id="account-type",
                name="account_type",
                cls="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-400 focus:outline-none",
            ),
            cls="flex flex-col gap-1",
        ),
        Button(
            "Add account",
            type="submit",
            cls="rounded-full bg-emerald-400 px-5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300",
        ),
        hx_post="/accounts",
        hx_target="#account-list",
        hx_swap="outerHTML",
        hx_on="htmx:afterRequest: if(event.detail.successful) this.reset()",
        cls="flex flex-wrap items-end gap-3 rounded-xl border border-slate-700 bg-slate-900/50 p-4",
    )


def accounts_page(active: list[Account], archived: list[Account]):
    return (
        Header(H1("Accounts", cls="text-4xl font-semibold text-white"), cls="space-y-2"),
        account_form(),
        accounts_list(active, archived),
    )
