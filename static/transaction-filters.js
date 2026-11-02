(() => {
  const breakdownKey = 'cashcompass-transaction-categories-open';
  const initializedBreakdowns = new WeakSet();
  const restoreBreakdown = () => {
    const panel = document.getElementById('transaction-category-breakdown');
    // Restore each new panel once; unrelated swaps must not undo a user's toggle.
    if (panel && !initializedBreakdowns.has(panel)) {
      initializedBreakdowns.add(panel);
      panel.open = sessionStorage.getItem(breakdownKey) === 'true';
    }
  };
  // Save user intent synchronously. Native toggle events and HTMX swaps can arrive
  // out of order, so a transient closed replacement must not overwrite the choice.
  document.addEventListener('click', event => {
    const summary = event.target.closest('#transaction-category-breakdown > summary');
    if (summary) sessionStorage.setItem(breakdownKey, String(!summary.parentElement.open));
  });
  document.addEventListener('DOMContentLoaded', restoreBreakdown);
  document.addEventListener('htmx:afterSwap', restoreBreakdown);
  document.addEventListener('htmx:historyRestore', restoreBreakdown);

  const form = () => document.getElementById('transaction-filters');
  const updateControls = () => {
    const filters = form();
    if (!filters) return;
    const preset = filters.elements.date_preset.value;
    filters.querySelectorAll('[data-date-preset]').forEach(button => {
      const active = button.dataset.datePreset === preset;
      button.classList.toggle('btn-primary', active);
      button.classList.toggle('btn-ghost', !active);
    });
    const params = new URLSearchParams(new FormData(filters));
    document.querySelectorAll('[data-transaction-mode]').forEach(link => {
      const target = new URLSearchParams(params);
      target.set('account_type', link.dataset.transactionMode);
      link.href = '/transactions?' + target.toString();
    });
  };

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-date-preset]');
    if (!button) return;
    const filters = form();
    filters.elements.date_preset.value = button.dataset.datePreset;
    filters.elements.date_from.value = '';
    filters.elements.date_to.value = '';
    updateControls();
    htmx.trigger(filters, 'change');
  });
  document.addEventListener('input', event => {
    if (event.target.closest('#transaction-filters')) updateControls();
  });
  document.addEventListener('change', event => {
    if (event.target.closest('#transaction-filters')) updateControls();
  });

  // History snapshots can contain controls edited after their URL was saved.
  // Restore the URL's authoritative filter state when navigating back/forward.
  document.addEventListener('htmx:historyRestore', () => {
    const filters = form();
    if (!filters) return;
    const params = new URLSearchParams(location.search);
    for (const key of ['label', 'date_from', 'date_to']) filters.elements[key].value = params.get(key) || '';
    filters.elements.account_type.value = params.get('account_type') || 'expenses';
    filters.elements.date_preset.value = params.get('date_preset') ||
      (params.has('date_from') || params.has('date_to') ? 'custom' : 'this_month');
    const categories = params.getAll('category_id');
    filters.querySelectorAll('[name="category_id"]').forEach(input => {
      input.checked = categories.includes(input.value);
    });
    updateControls();
    // Refresh checklist summaries after restoring checkbox properties.
    document.body.dispatchEvent(new Event('htmx:afterSwap', { bubbles: true }));
  });
  document.addEventListener('DOMContentLoaded', updateControls);
})();
