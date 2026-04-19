from fasthtml.common import *


def settings_page(imported_type: str = "", imported_count: int = 0,
                  error_msg: str = "", dev_mode: bool = False, reset: bool = False):
    alerts = []

    if reset:
        alerts.append(
            Div("Database reset successfully.",
                data_testid="settings-alert-success",
                cls="rounded-xl border border-emerald-600 bg-emerald-900/30 px-5 py-4 text-sm text-emerald-300")
        )

    if imported_type == "expenses":
        alerts.append(
            Div(f"Imported {imported_count} expense transaction(s) successfully.",
                data_testid="settings-alert-success",
                cls="rounded-xl border border-emerald-600 bg-emerald-900/30 px-5 py-4 text-sm text-emerald-300")
        )
    elif imported_type == "accounts":
        alerts.append(
            Div(f"Imported {imported_count} reconciliation transaction(s) successfully.",
                data_testid="settings-alert-success",
                cls="rounded-xl border border-emerald-600 bg-emerald-900/30 px-5 py-4 text-sm text-emerald-300")
        )

    if error_msg:
        alerts.append(
            Div(f"Error: {error_msg}",
                data_testid="settings-alert-error",
                cls="rounded-xl border border-red-600 bg-red-900/30 px-5 py-4 text-sm text-red-300")
        )

    expenses_section = Section(
        Div(
            H2("Expenses", cls="text-lg font-semibold text-white"),
            P(
                "CSV columns: ",
                Code("Amount, Category, Date, Description", cls="text-slate-300"),
                cls="text-sm text-slate-400",
            ),
            cls="space-y-1",
        ),
        Div(
            Form(
                Input(type="hidden", name="timezone", value="UTC"),
                P("Import from CSV", cls="text-sm font-medium text-slate-300"),
                Input(type="file", name="file", accept=".csv,text/csv", required=True,
                      id="settings-expenses-file",
                      cls="text-sm text-slate-300 file:mr-3 file:rounded file:border-0 file:bg-slate-700 file:px-3 file:py-1 file:text-sm file:text-slate-200 hover:file:bg-slate-600"),
                Button("Import Expenses", type="submit",
                       id="settings-import-expenses-submit",
                       cls="self-start rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500"),
                id="settings-import-expenses-form",
                data_testid="settings-import-expenses-form",
                action="/settings/import/expenses",
                method="POST",
                enctype="multipart/form-data",
                onsubmit="this.querySelector('[name=timezone]').value=Intl.DateTimeFormat().resolvedOptions().timeZone",
                cls="flex-1 flex flex-col gap-3 rounded-xl border border-slate-700 bg-slate-900 p-4",
            ),
            Div(
                P("Export to CSV", cls="text-sm font-medium text-slate-300"),
                P("All transactions from expenses-type accounts.", cls="text-xs text-slate-500"),
                A("Export Expenses", href="/settings/export/expenses",
                  id="settings-export-expenses-link",
                  cls="self-start rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"),
                cls="flex-1 flex flex-col gap-3 rounded-xl border border-slate-700 bg-slate-900 p-4",
            ),
            cls="flex flex-col sm:flex-row gap-4",
        ),
        data_testid="settings-expenses-section",
        cls="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4",
    )

    accounts_section = Section(
        Div(
            H2("Accounts (Net Worth)", cls="text-lg font-semibold text-white"),
            P(
                "CSV columns: ",
                Code("Account, Date, Balance", cls="text-slate-300"),
                cls="text-sm text-slate-400",
            ),
            cls="space-y-1",
        ),
        Div(
            Form(
                Input(type="hidden", name="timezone", value="UTC"),
                P("Import from CSV", cls="text-sm font-medium text-slate-300"),
                Input(type="file", name="file", accept=".csv,text/csv", required=True,
                      id="settings-accounts-file",
                      cls="text-sm text-slate-300 file:mr-3 file:rounded file:border-0 file:bg-slate-700 file:px-3 file:py-1 file:text-sm file:text-slate-200 hover:file:bg-slate-600"),
                Button("Import Accounts", type="submit",
                       id="settings-import-accounts-submit",
                       cls="self-start rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"),
                id="settings-import-accounts-form",
                data_testid="settings-import-accounts-form",
                action="/settings/import/accounts",
                method="POST",
                enctype="multipart/form-data",
                onsubmit="this.querySelector('[name=timezone]').value=Intl.DateTimeFormat().resolvedOptions().timeZone",
                cls="flex-1 flex flex-col gap-3 rounded-xl border border-slate-700 bg-slate-900 p-4",
            ),
            Div(
                P("Export to CSV", cls="text-sm font-medium text-slate-300"),
                P("Cumulative balance per date for all net-worth accounts.", cls="text-xs text-slate-500"),
                A("Export Accounts", href="/settings/export/accounts",
                  id="settings-export-accounts-link",
                  cls="self-start rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"),
                cls="flex-1 flex flex-col gap-3 rounded-xl border border-slate-700 bg-slate-900 p-4",
            ),
            cls="flex flex-col sm:flex-row gap-4",
        ),
        data_testid="settings-accounts-section",
        cls="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4",
    )

    sections = [
        Header(H1("Settings", cls="text-4xl font-semibold text-white"), cls="space-y-2"),
        *alerts,
        expenses_section,
        accounts_section,
    ]

    if dev_mode:
        sections.append(
            Section(
                Div(
                    Div(
                        H2("Reset Database", cls="text-lg font-semibold text-red-400"),
                        Span("dev only", cls="text-xs rounded px-2 py-0.5 bg-red-900/60 text-red-400 font-mono"),
                        cls="flex items-center gap-2",
                    ),
                    P("Deletes all transactions, categories, and accounts. Cannot be undone.", cls="text-sm text-slate-400"),
                    cls="space-y-1",
                ),
                Form(
                    Button("Reset Database", type="submit",
                           id="settings-reset-submit",
                           cls="rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-600"),
                    id="settings-reset-form",
                    data_testid="settings-reset-form",
                    action="/settings/reset-database",
                    method="POST",
                    onsubmit="return confirm('This will permanently delete all data. Are you sure?')",
                ),
                data_testid="settings-reset-section",
                cls="rounded-2xl border border-red-900 bg-red-950/40 p-6 space-y-4",
            )
        )

    return tuple(sections)
