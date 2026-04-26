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
                Label("Date", fr="transaction-date", cls="label-text"),
                Div(
                    Input(type="date", id="transaction-date", name="date", value=today, required=True,
                          cls="input input-bordered w-full",
                          **_recommendation_request_attrs("change", ai_enabled)),
                    Button("Today", type="button", id="transaction-date-today",
                           cls="btn btn-outline w-full sm:w-auto",
                           data_testid="transaction-date-today"),
                    cls="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]",
                ),
                Div(
                    Span(id="transaction-date-notice-text"),
                    Div(
                        Button("Use today", type="button", id="transaction-date-use-today",
                               cls="btn btn-xs btn-primary",
                               data_testid="transaction-date-use-today"),
                        Button("Keep date", type="button", id="transaction-date-keep",
                               cls="btn btn-xs btn-ghost",
                               data_testid="transaction-date-keep"),
                        cls="flex shrink-0 gap-2",
                    ),
                    id="transaction-date-notice",
                    data_testid="transaction-date-notice",
                    cls="hidden items-center justify-between gap-3 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-base-content",
                ),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Label", fr="transaction-label", cls="label-text"),
                Input(type="text", id="transaction-label", name="label", placeholder="Description", required=True,
                      cls="input input-bordered w-full",
                      **_recommendation_request_attrs("input changed delay:500ms", ai_enabled)),
                cls="flex flex-col gap-1",
            ),
            Div(
                Label("Amount", fr="transaction-amount", cls="label-text"),
                Div(
                    Input(type="number", id="transaction-amount", name="amount", placeholder="0.00", step="0.01", min="0", required=True,
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
                Span("", id="transaction-form-status",
                     data_testid="transaction-form-status",
                     cls="hidden text-xs cc-muted"),
                cls="cc-form-actions items-center gap-3",
            ),
            id="transaction-form",
            hx_post="/transactions",
            hx_target="#transaction-list",
            hx_swap="outerHTML",
            cls="cc-form-stack",
        ),
        Script(
            """
            (() => {
              const initTransactionForm = () => {
                const form = document.getElementById('transaction-form');
                if (!form || form.dataset.transactionFormReady === 'true') return;
                form.dataset.transactionFormReady = 'true';

                const dateInput = form.querySelector('input[name="date"]');
                const labelInput = form.querySelector('input[name="label"]');
                const amountInput = form.querySelector('input[name="amount"]');
                const amountMode = form.querySelector('select[name="amount_mode"]');
                const accountSelect = form.querySelector('select[name="account_id"]');
                const categorySelect = form.querySelector('select[name="category_id"]');
                const status = document.getElementById('transaction-form-status');
                const todayButton = document.getElementById('transaction-date-today');
                const notice = document.getElementById('transaction-date-notice');
                const noticeText = document.getElementById('transaction-date-notice-text');
                const useTodayButton = document.getElementById('transaction-date-use-today');
                const keepDateButton = document.getElementById('transaction-date-keep');

                if (!dateInput) return;

                let dateDirty = false;
                let dismissedNoticeKey = '';
                const recommendationPanel = () => document.getElementById('transaction-category-recommendation');

                const localToday = () => {
                  const now = new Date();
                  const month = String(now.getMonth() + 1).padStart(2, '0');
                  const day = String(now.getDate()).padStart(2, '0');
                  return `${now.getFullYear()}-${month}-${day}`;
                };

                const formatDate = (isoDate) => {
                  if (!isoDate) return '';
                  return new Date(`${isoDate}T12:00:00`).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                  });
                };

                const setStatus = (message) => {
                  if (!status) return;
                  status.textContent = message || '';
                  status.classList.toggle('hidden', !message);
                };

                const hideNotice = () => {
                  if (!notice) return;
                  notice.classList.add('hidden');
                  notice.classList.remove('flex');
                };

                const showNotice = (selectedDate, today) => {
                  if (!notice || !noticeText) return;
                  noticeText.textContent = `This form is dated ${formatDate(selectedDate)}. Today is ${formatDate(today)}.`;
                  notice.classList.remove('hidden');
                  notice.classList.add('flex');
                };

                const setDateFromSystem = (value) => {
                  dateInput.dataset.systemDateChange = 'true';
                  dateInput.value = value;
                  dateInput.dispatchEvent(new Event('change', { bubbles: true }));
                  delete dateInput.dataset.systemDateChange;
                };

                const hasDraft = () => {
                  if (dateDirty) return true;
                  if ((labelInput?.value || '').trim()) return true;
                  if ((amountInput?.value || '').trim()) return true;
                  return !!categorySelect && categorySelect.value !== '0';
                };

                const checkStaleDate = () => {
                  const today = localToday();
                  const selectedDate = dateInput.value;
                  if (!selectedDate || selectedDate === today) {
                    hideNotice();
                    return;
                  }

                  const noticeKey = `${selectedDate}|${today}`;
                  if (!hasDraft()) {
                    setDateFromSystem(today);
                    hideNotice();
                    return;
                  }

                  if (dismissedNoticeKey !== noticeKey) {
                    showNotice(selectedDate, today);
                  }
                };

                dateInput.addEventListener('change', () => {
                  if (dateInput.dataset.systemDateChange !== 'true') {
                    dateDirty = true;
                    dismissedNoticeKey = '';
                  }
                  if (dateInput.value === localToday()) {
                    hideNotice();
                  }
                });

                todayButton?.addEventListener('click', () => {
                  setDateFromSystem(localToday());
                  dateDirty = false;
                  dismissedNoticeKey = '';
                  hideNotice();
                  setStatus('');
                });

                useTodayButton?.addEventListener('click', () => {
                  setDateFromSystem(localToday());
                  dateDirty = false;
                  dismissedNoticeKey = '';
                  hideNotice();
                });

                keepDateButton?.addEventListener('click', () => {
                  dismissedNoticeKey = `${dateInput.value}|${localToday()}`;
                  hideNotice();
                });

                document.body.addEventListener('htmx:beforeSwap', (event) => {
                  const target = event.detail?.target;
                  if (target?.id !== 'transaction-category-recommendation') return;
                  if ((labelInput?.value || '').trim() && (amountInput?.value || '').trim()) return;

                  event.detail.shouldSwap = false;
                  target.innerHTML = '';
                });

                form.addEventListener('htmx:afterRequest', (event) => {
                  const source = event.detail?.elt || event.target;
                  if (source !== form || !event.detail?.successful) return;

                  const preservedDate = dateInput.value;
                  const preservedAccount = accountSelect?.value || '';
                  const preservedMode = amountMode?.value || 'debit';

                  form.reset();
                  dateInput.value = preservedDate;
                  if (accountSelect) accountSelect.value = preservedAccount;
                  if (amountMode) amountMode.value = preservedMode;
                  if (categorySelect) categorySelect.value = '0';
                  const recommendation = recommendationPanel();
                  if (recommendation) recommendation.innerHTML = '';

                  dateDirty = preservedDate !== localToday();
                  dismissedNoticeKey = '';
                  hideNotice();
                  setStatus(`Added. Ready for another transaction on ${formatDate(preservedDate)}.`);
                  labelInput?.focus();
                });

                document.addEventListener('visibilitychange', () => {
                  if (!document.hidden) checkStaleDate();
                });
                window.addEventListener('focus', checkStaleDate);
                checkStaleDate();
              };

              if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initTransactionForm);
              } else {
                initTransactionForm();
              }
            })();
            """
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
