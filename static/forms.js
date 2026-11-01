(() => {
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
