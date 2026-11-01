(() => {
  // Keep inherited contributions out of the submission unless the user edits them.
  document.addEventListener('formdata', (event) => {
    if (!event.target.matches('[data-testid="budget-limits-form"]')) return;
    for (const input of event.target.querySelectorAll('input[name^="limit_"]')) {
      const value = input.value.trim();
      const original = input.defaultValue.trim();
      if (value === original) {
        event.formData.delete(input.name);
      }
    }
  });

  document.addEventListener('htmx:afterRequest', (event) => {
    const source = event.detail.requestConfig?.elt || event.detail.elt;
    const scope = source?.closest('[data-error-scope]');
    const error = scope?.querySelector('[data-form-error]');
    const status = event.detail.xhr?.status;
    if (error && (status === 400 || status === 409)) {
      error.textContent = event.detail.xhr.responseText;
      error.classList.remove('hidden');
    } else if (event.detail.successful && source?.matches('form, button')) {
      if (error) {
        error.textContent = '';
        error.classList.add('hidden');
      }
      if (source?.matches('form[data-reset-on-success]')) source.reset();
    }
  });
})();
