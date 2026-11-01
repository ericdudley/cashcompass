(() => {
  let activeForm;
  let controller;
  const initTransactionForm = () => {
    const form = document.getElementById('transaction-form');
    if (form === activeForm) return;
    controller?.abort();
    activeForm = form;
    if (!form) return;
    controller = new AbortController();
    const listen = (target, type, callback) => target?.addEventListener(type, callback, { signal: controller.signal });

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

    listen(dateInput, 'change', () => {
      if (dateInput.dataset.systemDateChange !== 'true') {
        dateDirty = true;
        dismissedNoticeKey = '';
      }
      if (dateInput.value === localToday()) {
        hideNotice();
      }
    });

    listen(todayButton, 'click', () => {
      setDateFromSystem(localToday());
      dateDirty = false;
      dismissedNoticeKey = '';
      hideNotice();
      setStatus('');
    });

    listen(useTodayButton, 'click', () => {
      setDateFromSystem(localToday());
      dateDirty = false;
      dismissedNoticeKey = '';
      hideNotice();
    });

    listen(keepDateButton, 'click', () => {
      dismissedNoticeKey = `${dateInput.value}|${localToday()}`;
      hideNotice();
    });

    listen(document.body, 'htmx:beforeSwap', (event) => {
      const target = event.detail?.target;
      if (target?.id !== 'transaction-category-recommendation') return;
      if ((labelInput?.value || '').trim() && (amountInput?.value || '').trim()) return;

      event.detail.shouldSwap = false;
      target.innerHTML = '';
    });

    listen(form, 'htmx:afterRequest', (event) => {
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

    listen(document, 'visibilitychange', () => {
      if (!document.hidden) checkStaleDate();
    });
    listen(window, 'focus', checkStaleDate);
    checkStaleDate();
  };

  document.addEventListener('htmx:historyRestore', initTransactionForm);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTransactionForm);
  } else {
    initTransactionForm();
  }
})();
