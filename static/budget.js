(() => {
  document.addEventListener('change', event => {
    if (event.target.id !== 'budget-type') return;
    const select = event.target;
    const form = select.form;
    const annual = select.value === 'annual';
    form.querySelector('[data-monthly-only]').classList.toggle('hidden', annual);
    form.querySelector('#budget-amount-label').textContent = annual ? 'Annual amount ($)' : 'Monthly amount ($)';
    const input = form.querySelector('#budget-amount');
    const switching = select.value !== select.dataset.initialPeriod;
    input.value = switching ? '' : input.dataset.initialAmount;
    input.required = switching;
  });
})();
