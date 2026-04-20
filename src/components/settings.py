from fasthtml.common import *
from src.components.layout import theme_select


def settings_page(imported_type: str = "", imported_count: int = 0,
                  error_msg: str = "", dev_mode: bool = False, reset: bool = False):
    alerts = []

    if reset:
        alerts.append(
            Div("Database reset successfully.",
                data_testid="settings-alert-success",
                cls="alert alert-success shadow-sm")
        )

    if imported_type == "backup":
        alerts.append(
            Div("Backup restored successfully.",
                data_testid="settings-alert-success",
                cls="alert alert-success shadow-sm")
        )

    if error_msg:
        alerts.append(
            Div(f"Error: {error_msg}",
                data_testid="settings-alert-error",
                cls="alert alert-error shadow-sm")
        )

    theme_section = Section(
        Div(
            H2("Theme", cls="text-lg font-semibold text-base-content"),
            P("Change the app theme instantly to verify colors, surfaces, and controls across the interface.", cls="text-sm cc-muted"),
            cls="space-y-1",
        ),
        Div(
            Label("Choose theme", fr="settings-theme-picker", cls="label-text"),
            theme_select("settings-theme-picker", width_cls="w-full sm:w-56"),
            P("Saved on this device and synced with the navigation theme picker.", cls="text-xs cc-subtle"),
            cls="flex flex-col gap-2",
        ),
        data_testid="settings-theme-section",
        cls="cc-glass rounded-2xl p-6 space-y-4",
    )

    backup_section = Section(
        Div(
            H2("Backup & Restore", cls="text-lg font-semibold text-base-content"),
            P("Canonical CashCompass backup format for exact restore and long-term portability.", cls="text-sm cc-muted"),
            cls="space-y-1",
        ),
        Div(
            Form(
                P("Restore from backup JSON", cls="text-sm font-medium text-base-content"),
                Input(type="file", name="file", accept=".json,application/json", required=True,
                      id="settings-backup-file",
                      cls="file-input file-input-bordered w-full"),
                Button("Restore Backup", type="submit",
                       id="settings-import-backup-submit",
                       cls="btn btn-secondary self-start"),
                id="settings-import-backup-form",
                data_testid="settings-import-backup-form",
                action="/settings/import/backup",
                method="POST",
                enctype="multipart/form-data",
                onsubmit="return confirm('This replaces the current database. Continue?')",
                cls="cc-glass flex-1 flex flex-col gap-3 rounded-xl p-4",
            ),
            Div(
                P("Export canonical backup", cls="text-sm font-medium text-base-content"),
                P("Single JSON file with accounts, categories, and transactions using stable IDs.", cls="text-xs cc-subtle"),
                A("Export Backup", href="/settings/export/backup",
                  id="settings-export-backup-link",
                  cls="btn btn-neutral btn-sm self-start"),
                cls="cc-glass flex-1 flex flex-col gap-3 rounded-xl p-4",
            ),
            cls="flex flex-col sm:flex-row gap-4",
        ),
        data_testid="settings-backup-section",
        cls="cc-glass rounded-2xl p-6 space-y-4",
    )

    transactions_section = Section(
        Div(
            H2("Transactions CSV", cls="text-lg font-semibold text-base-content"),
            P("Flat ledger export for spreadsheets, pandas, and other tools outside CashCompass.", cls="text-sm cc-muted"),
            cls="space-y-1",
        ),
        Div(
            P("Export interoperability CSV", cls="text-sm font-medium text-base-content"),
            P(
                "Columns: ",
                Code("transaction_id, date, amount_cents, amount, label, account, account_type, category, archived_account"),
                cls="text-xs cc-subtle",
            ),
            A("Export Transactions CSV", href="/settings/export/transactions.csv",
              id="settings-export-transactions-link",
              cls="btn btn-neutral btn-sm self-start"),
            cls="cc-glass flex flex-col gap-3 rounded-xl p-4",
        ),
        data_testid="settings-transactions-export-section",
        cls="cc-glass rounded-2xl p-6 space-y-4",
    )

    sections = [
        Header(H1("Settings", cls="cc-page-title text-4xl font-semibold text-base-content"), cls="space-y-2"),
        *alerts,
        theme_section,
        backup_section,
        transactions_section,
    ]

    if dev_mode:
        sections.append(
            Section(
                Div(
                    Div(
                        H2("Reset Database", cls="text-lg font-semibold text-error"),
                        Span("dev only", cls="badge badge-error badge-outline"),
                        cls="flex items-center gap-2",
                    ),
                    P("Deletes all transactions, categories, and accounts. Cannot be undone.", cls="text-sm cc-muted"),
                    cls="space-y-1",
                ),
                Form(
                    Button("Reset Database", type="submit",
                           id="settings-reset-submit",
                           cls="btn btn-error"),
                    id="settings-reset-form",
                    data_testid="settings-reset-form",
                    action="/settings/reset-database",
                    method="POST",
                    onsubmit="return confirm('This will permanently delete all data. Are you sure?')",
                ),
                data_testid="settings-reset-section",
                cls="rounded-2xl border border-error/30 bg-error/10 p-6 space-y-4",
            )
        )

    return tuple(sections)
