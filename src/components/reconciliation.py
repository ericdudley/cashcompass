from __future__ import annotations

from fasthtml.common import *

from src.services.reconciliation import ReconciliationRow
from src.utils.format import cents_diff, cents_dollars


def _diff_tone_cls(cents: int | None) -> str:
    if cents is None:
        return "cc-muted"
    if cents > 0:
        return "text-success"
    if cents < 0:
        return "text-error"
    return "cc-muted"


def _server_diff(latest_value: str, current_balance: int) -> tuple[str, str]:
    raw = (latest_value or "").strip()
    if not raw:
        return "—", _diff_tone_cls(None)
    try:
        normalized = raw.replace("$", "").replace(",", "")
        latest_cents = int(round(float(normalized) * 100))
    except (TypeError, ValueError):
        return "Invalid", "text-error"
    diff = latest_cents - current_balance
    return cents_diff(diff), _diff_tone_cls(diff)


def reconciliation_page(
    rows: list[ReconciliationRow],
    latest_values: dict[int, str] | None = None,
    invalid_accounts: set[int] | None = None,
    success_count: int = 0,
    status_msg: str = "",
    error_msg: str = "",
):
    latest_values = latest_values or {}
    invalid_accounts = invalid_accounts or set()

    alerts = []
    if success_count:
        noun = "adjustment" if success_count == 1 else "adjustments"
        alerts.append(
            Div(
                f"Created {success_count} {noun}.",
                data_testid="reconcile-alert-success",
                cls="alert alert-success shadow-sm",
            )
        )
    elif status_msg:
        alerts.append(
            Div(
                status_msg,
                data_testid="reconcile-alert-status",
                cls="alert alert-info shadow-sm",
            )
        )
    if error_msg:
        alerts.append(
            Div(
                f"Error: {error_msg}",
                data_testid="reconcile-alert-error",
                cls="alert alert-error shadow-sm",
            )
        )

    body_rows = []
    for row in rows:
        latest_value = latest_values.get(row.account.id, "")
        diff_text, diff_cls = _server_diff(latest_value, row.current_balance)
        body_rows.append(
            Tr(
                Td(
                    Div(
                        P(row.account.label, cls="font-medium text-base-content"),
                        P("net worth", cls="text-xs cc-subtle"),
                        cls="space-y-1",
                    ),
                    data_testid="reconcile-account-label",
                    cls="px-4 py-3",
                ),
                Td(
                    Span(cents_dollars(row.current_balance), cls="block w-full font-mono"),
                    data_testid="reconcile-current-balance",
                    cls="px-4 py-3 text-right text-base-content",
                ),
                Td(
                    Input(
                        type="text",
                        name=f"latest_balance_{row.account.id}",
                        value=latest_value,
                        placeholder="0.00",
                        autocomplete="off",
                        data_reconcile_input="true",
                        data_account_id=str(row.account.id),
                        cls=f"input input-bordered w-full font-mono {'input-error' if row.account.id in invalid_accounts else ''}",
                    ),
                    cls="px-4 py-3",
                ),
                Td(
                    Span(
                        diff_text,
                        data_reconcile_diff="true",
                        data_account_id=str(row.account.id),
                        cls=f"block w-full font-mono {diff_cls}",
                    ),
                    data_testid="reconcile-diff",
                    cls="px-4 py-3 text-right",
                ),
                data_testid="reconcile-row",
                data_account_id=str(row.account.id),
                data_current_balance_cents=str(row.current_balance),
                data_label=row.account.label,
                cls="border-b border-base-300/70 align-top",
            )
        )

    if not body_rows:
        body_rows.append(
            Tr(
                Td("No active net worth accounts.", colspan="4", cls="px-4 py-6 text-sm cc-muted text-center"),
            )
        )

    summary_card = Section(
        Div(
            H1("Reconcile Net Worth", cls="cc-page-title text-4xl font-semibold text-base-content"),
            P(
                "Enter the latest real-world balances. Saving creates balance adjustment transactions dated today.",
                cls="text-sm cc-muted",
            ),
            cls="space-y-2",
        ),
        data_testid="reconcile-summary",
        cls="space-y-2",
    )

    form = Form(
        Div(
            Table(
                Colgroup(
                    Col(),
                    Col(cls="w-44"),
                    Col(cls="w-56"),
                    Col(cls="w-36"),
                ),
                Thead(
                    Tr(
                        Th("Account", cls="px-4 py-3 text-left font-medium cc-muted"),
                        Th("Current Balance", cls="w-44 px-4 py-3 text-right font-medium cc-muted"),
                        Th("Latest Balance", cls="w-56 px-4 py-3 text-left font-medium cc-muted"),
                        Th("Diff", cls="w-36 px-4 py-3 text-right font-medium cc-muted"),
                        cls="border-b border-base-300",
                    )
                ),
                Tbody(*body_rows),
                Tfoot(
                    Tr(
                        Td("Total Diff", colspan="3", cls="px-4 py-3 text-right font-medium text-base-content"),
                        Td(
                            Span(
                                "$0.00",
                                id="reconcile-total-diff",
                                data_testid="reconcile-total-diff",
                                cls="block w-full font-mono cc-muted",
                            ),
                            cls="px-4 py-3 text-right",
                        ),
                        cls="border-t border-base-300",
                    )
                ),
                cls="table table-fixed min-w-[52rem] w-full text-sm",
            ),
            cls="cc-glass overflow-x-auto rounded-2xl",
        ),
        Div(
            Button("Save Adjustments", type="submit", cls="btn btn-primary"),
            cls="flex justify-end",
        ),
        data_testid="reconcile-form",
        action="/accounts/reconcile",
        method="POST",
        cls="space-y-4",
    )

    script = Script(
        """
        (() => {
          const formatCents = (cents) => {
            const abs = Math.abs(cents);
            const dollars = Math.floor(abs / 100).toLocaleString('en-US');
            const centsPart = String(abs % 100).padStart(2, '0');
            if (cents > 0) return `+$${dollars}.${centsPart}`;
            if (cents < 0) return `-$${dollars}.${centsPart}`;
            return `$${dollars}.${centsPart}`;
          };
          const parseCents = (raw) => {
            const value = (raw || '').trim();
            if (!value) return null;
            const normalized = value.replace(/[$,]/g, '');
            if (!/^-?(?:\\d+|\\d*\\.\\d{1,2})$/.test(normalized)) return Number.NaN;
            return Math.round(Number(normalized) * 100);
          };
          const sync = () => {
            let total = 0;
            let hasInvalid = false;
            document.querySelectorAll('[data-testid="reconcile-row"]').forEach((row) => {
              const input = row.querySelector('[data-reconcile-input="true"]');
              const diffNode = row.querySelector('[data-reconcile-diff="true"]');
              const currentBalance = Number(row.dataset.currentBalanceCents || '0');
              const parsed = parseCents(input?.value || '');
              input?.classList.remove('input-error');
              diffNode?.classList.remove('text-success', 'text-error', 'cc-muted');
              if (parsed === null) {
                diffNode.textContent = '—';
                diffNode.classList.add('cc-muted');
                return;
              }
              if (Number.isNaN(parsed)) {
                hasInvalid = true;
                input?.classList.add('input-error');
                diffNode.textContent = 'Invalid';
                diffNode.classList.add('text-error');
                return;
              }
              const diff = parsed - currentBalance;
              total += diff;
              diffNode.textContent = formatCents(diff);
              diffNode.classList.add(diff > 0 ? 'text-success' : diff < 0 ? 'text-error' : 'cc-muted');
            });
            const totalNode = document.getElementById('reconcile-total-diff');
            if (!totalNode) return;
            totalNode.classList.remove('text-success', 'text-error', 'cc-muted');
            if (hasInvalid) {
              totalNode.textContent = 'Invalid';
              totalNode.classList.add('text-error');
              return;
            }
            totalNode.textContent = formatCents(total);
            totalNode.classList.add(total > 0 ? 'text-success' : total < 0 ? 'text-error' : 'cc-muted');
          };
          document.addEventListener('input', (event) => {
            if (event.target instanceof HTMLElement && event.target.matches('[data-reconcile-input="true"]')) {
              sync();
            }
          });
          document.addEventListener('DOMContentLoaded', sync);
          sync();
        })();
        """
    )

    return (
        summary_card,
        *alerts,
        Section(form, cls="space-y-4"),
        script,
    )
