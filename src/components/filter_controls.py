from fasthtml.common import *


def checklist_filter(
    label: str,
    name: str,
    items: list,
    selected_ids: set[int],
    testid: str,
    help_text: str = "",
    empty_summary: str = "None",
    all_summary: str = "All",
):
    rows = []
    for item in items:
        checked = item.id in selected_ids
        rows.append(
            Label(
                Input(
                    type="checkbox",
                    name=name,
                    value=str(item.id),
                    checked=checked,
                    data_cc_checklist_input="true",
                    cls="checkbox checkbox-xs",
                ),
                Span(item.label, cls="text-sm text-base-content"),
                data_cc_checklist_row="true",
                data_cc_checklist_text=item.label.lower(),
                cls="cc-checklist-row",
            )
        )

    if not rows:
        rows = [P(f"No {label.lower()} available.", cls="text-sm cc-muted")]

    return Div(
        Span(label, cls="text-xs font-medium cc-muted"),
        Div(
            Button(
                Span(empty_summary, data_cc_checklist_summary="true", cls="cc-checklist-summary"),
                type="button",
                data_cc_checklist_button="true",
                cls="cc-checklist-button",
            ),
            Div(
                Input(
                    type="search",
                    placeholder=f"Search {label.lower()}...",
                    data_cc_checklist_search="true",
                    data_testid=f"{testid}-search",
                    cls="input input-bordered input-sm w-full",
                ),
                Div(
                    Button("All", type="button", data_cc_checklist_all="true", cls="btn btn-xs btn-ghost"),
                    Button("Clear", type="button", data_cc_checklist_clear="true", cls="btn btn-xs btn-ghost"),
                    cls="flex justify-end gap-1",
                ),
                Div(*rows, cls="cc-checklist-options"),
                cls="cc-checklist-panel cc-glass",
            ),
            data_cc_checklist="true",
            data_empty_summary=empty_summary,
            data_all_summary=all_summary,
            data_testid=testid,
            cls="cc-checklist",
        ),
        P(help_text, cls="text-xs cc-subtle mt-1") if help_text else "",
        _checklist_filter_script(),
        cls="form-control",
    )


def _checklist_filter_script():
    return Script(
        """
        (() => {
          if (window.cashCompassChecklistFiltersReady) return;
          window.cashCompassChecklistFiltersReady = true;

          const roots = () => Array.from(document.querySelectorAll('[data-cc-checklist]'));
          const inputs = (root) => Array.from(root.querySelectorAll('[data-cc-checklist-input]'));

          const closeOthers = (activeRoot) => {
            roots().forEach((root) => {
              if (root !== activeRoot) root.classList.remove('cc-open');
            });
          };

          const update = (root) => {
            const allInputs = inputs(root);
            const checked = allInputs.filter((input) => input.checked);
            const summary = root.querySelector('[data-cc-checklist-summary]');
            if (!summary) return;

            if (checked.length === 0) {
              summary.textContent = root.dataset.emptySummary || 'None';
            } else {
              const labels = checked.map((input) => {
                const row = input.closest('[data-cc-checklist-row]');
                return row?.textContent?.trim();
              }).filter(Boolean);
              summary.textContent = labels.join(', ');
            }
          };

          const dispatchChange = (root) => {
            const firstInput = inputs(root)[0];
            firstInput?.dispatchEvent(new Event('change', { bubbles: true }));
          };

          document.addEventListener('click', (event) => {
            const button = event.target.closest('[data-cc-checklist-button]');
            if (button) {
              const root = button.closest('[data-cc-checklist]');
              if (!root) return;
              const willOpen = !root.classList.contains('cc-open');
              closeOthers(root);
              root.classList.toggle('cc-open', willOpen);
              if (willOpen) {
                const search = root.querySelector('[data-cc-checklist-search]');
                setTimeout(() => search?.focus(), 0);
              }
              return;
            }

            const allButton = event.target.closest('[data-cc-checklist-all]');
            if (allButton) {
              const root = allButton.closest('[data-cc-checklist]');
              inputs(root).forEach((input) => { input.checked = true; });
              update(root);
              dispatchChange(root);
              root.classList.remove('cc-open');
              return;
            }

            const clearButton = event.target.closest('[data-cc-checklist-clear]');
            if (clearButton) {
              const root = clearButton.closest('[data-cc-checklist]');
              inputs(root).forEach((input) => { input.checked = false; });
              update(root);
              dispatchChange(root);
              root.classList.remove('cc-open');
              return;
            }

            if (!event.target.closest('[data-cc-checklist]')) {
              closeOthers(null);
            }
          });

          document.addEventListener('input', (event) => {
            if (!event.target.matches('[data-cc-checklist-search]')) return;
            const root = event.target.closest('[data-cc-checklist]');
            const query = event.target.value.trim().toLowerCase();
            root.querySelectorAll('[data-cc-checklist-row]').forEach((row) => {
              row.classList.toggle('hidden', query && !row.dataset.ccChecklistText.includes(query));
            });
          });

          document.addEventListener('change', (event) => {
            if (!event.target.matches('[data-cc-checklist-input]')) return;
            const root = event.target.closest('[data-cc-checklist]');
            update(root);
            root.classList.remove('cc-open');
          });

          document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') closeOthers(null);
          });

          document.addEventListener('DOMContentLoaded', () => roots().forEach(update));
          document.body.addEventListener('htmx:afterSwap', () => roots().forEach(update));
          roots().forEach(update);
        })();
        """
    )
