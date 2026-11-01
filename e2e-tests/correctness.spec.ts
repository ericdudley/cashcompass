import type { Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { TransactionsPage } from './pages/transactions.page';
import { AccountsPage } from './pages/accounts.page';
import { CategoriesPage } from './pages/categories.page';
import { IncomePage } from './pages/income.page';

async function holdFirstFilterResponse(page: Page) {
  let release!: () => void;
  let started!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  const firstStarted = new Promise<void>(resolve => { started = resolve; });
  let first = true;
  await page.route('**/partials/transactions?**', async route => {
    const isFirst = first;
    first = false;
    const response = await route.fetch();
    if (isFirst) {
      started();
      await held;
    }
    await route.fulfill({ response });
  });
  return { firstStarted, release };
}

test('rapid category filters keep the latest selection when an older response arrives', async ({ page }) => {
  const tp = new TransactionsPage(page);
  await page.goto('/transactions?date_preset=all_time');
  const held = await holdFirstFilterResponse(page);
  await tp.checkCategoryFilter('Groceries');
  await held.firstStarted;
  await tp.checkCategoryFilter('Utilities');
  await expect(page).toHaveURL(/category_id=1&category_id=2/);
  held.release();
  await expect(tp.getCategoryCheckbox('1')).toBeChecked();
  await expect(tp.getCategoryCheckbox('2')).toBeChecked();
  await expect(tp.getRows()).toHaveCount(2);
  await expect(tp.getBreakdownTotal('net')).toHaveText('$152.32');
});

test('rapid date preset and category changes preserve both filters', async ({ page }) => {
  const tp = new TransactionsPage(page);
  await page.goto('/transactions?date_preset=all_time');
  const held = await holdFirstFilterResponse(page);
  await tp.checkCategoryFilter('Groceries');
  await held.firstStarted;
  await tp.getPresetButton('this_year').click();
  await expect(page).toHaveURL(/date_preset=this_year.*category_id=1/);
  held.release();
  await expect(tp.getPresetButton('this_year')).toHaveClass(/btn-primary/);
  await expect(tp.getCategoryCheckbox('1')).toBeChecked();
  await expect(tp.getRows()).toHaveCount(1);
  await expect(tp.getRows()).toContainText('Weekly shop');
});

test('pending filter results preserve search text and focus during debounce', async ({ page }) => {
  const tp = new TransactionsPage(page);
  await page.goto('/transactions?date_preset=all_time');
  const held = await holdFirstFilterResponse(page);
  await tp.checkCategoryFilter('Groceries');
  await held.firstStarted;
  await tp.getLabelSearch().fill('shop');
  held.release();
  await expect(tp.getLabelSearch()).toHaveValue('shop');
  await expect(tp.getLabelSearch()).toBeFocused();
  await expect(page).toHaveURL(/label=shop.*category_id=1/);
  await expect(tp.getCategoryCheckbox('1')).toBeChecked();
  await expect(tp.getRows()).toHaveCount(1);
  await expect(tp.getBreakdownTotal('net')).toHaveText('$54.32');
});

test('combined filters survive reload and browser history', async ({ page }) => {
  const tp = new TransactionsPage(page);
  await page.goto('/transactions?date_preset=all_time');
  await tp.checkCategoryFilter('Groceries');
  await expect(page).toHaveURL(/category_id=1/);
  await tp.checkCategoryFilter('Utilities');
  await expect(page).toHaveURL(/category_id=1&category_id=2/);
  await tp.getLabelSearch().fill('shop');
  await expect(page).toHaveURL(/label=shop/);
  await page.goBack();
  await expect(page).not.toHaveURL(/label=shop/);
  await expect(tp.getLabelSearch()).toHaveValue('');
  await expect(tp.getCategoryCheckbox('1')).toBeChecked();
  await expect(tp.getCategoryCheckbox('2')).toBeChecked();
  await expect(tp.getRows()).toHaveCount(2);
  await page.goForward();
  await expect(tp.getLabelSearch()).toHaveValue('shop');
  await expect(tp.getRows()).toHaveCount(1);
  await tp.fillCreateForm({ label: 'History shop', amount: '1.00', categoryId: '1' });
  await tp.submitCreate();
  await expect(tp.getCreateLabelInput()).toHaveValue('');
  await expect(tp.getCreateStatus()).toContainText('Added. Ready for another transaction');
  await page.reload();
  await expect(tp.getLabelSearch()).toHaveValue('shop');
  await expect(tp.getCategoryCheckbox('2')).toBeChecked();
  await expect(tp.getRows()).toHaveCount(2);
});

test('transaction validation is visible and mutations preserve settled filters', async ({ page, request }) => {
  const tp = new TransactionsPage(page);
  await page.goto('/transactions?date_preset=all_time&label=Regression&category_id=1');
  await expect(page.locator('script[src*="htmx.org"]')).toHaveCount(1);
  await tp.fillCreateForm({ label: 'Regression transaction', amount: '0.00', categoryId: '1' });
  await tp.submitCreate();
  await expect(tp.getCreateError()).toContainText('amount must be non-zero');
  await expect(tp.getCreateLabelInput()).toHaveValue('Regression transaction');
  await tp.getCreateLabelInput().fill('   ');
  await tp.getCreateAmountInput().fill('10.00');
  await tp.submitCreate();
  await expect(tp.getCreateError()).toContainText('label is required');
  await tp.getCreateLabelInput().fill('Regression transaction');
  await tp.submitCreate();
  await expect(tp.getCreateError()).toBeHidden();
  await expect(tp.getRows()).toHaveCount(1);
  await tp.clickEditOnRow(tp.getRows().first());
  const edit = tp.getEditRows();
  const originalDate = await edit.locator('[name="date"]').inputValue();
  await edit.locator('[name="date"]').fill('2025-01-01');
  await edit.locator('[name="label"]').fill('   ');
  await tp.saveEditRow(edit);
  await expect(tp.getEditError()).toContainText('label is required');
  const backup = await (await request.get('/settings/export/backup')).json();
  expect(backup.transactions.find((t: any) => t.label === 'Regression transaction').occurred_at).toBe(originalDate);
  await edit.locator('[name="date"]').fill(originalDate);
  await edit.locator('[name="label"]').fill('Regression transaction');
  await edit.locator('[name="amount"]').fill('12.00');
  await tp.saveEditRow(edit);
  await expect(tp.getRows()).toContainText('-$12.00');
  page.once('dialog', dialog => dialog.accept());
  await tp.clickDeleteOnRow(tp.getRows().first());
  await expect(tp.getRows()).toHaveCount(0);
  await expect(tp.getLabelSearch()).toHaveValue('Regression');
  await expect(tp.getCategoryCheckbox('1')).toBeChecked();
  await expect(page).toHaveURL(/label=Regression&category_id=1/);
});

test('populated account deletion shows a conflict and empty account creation resets', async ({ page }) => {
  const ap = new AccountsPage(page);
  await ap.goto();
  for (const archived of [false, true]) {
    if (archived) await ap.archiveAccount('Daily Expenses');
    page.once('dialog', dialog => dialog.accept());
    await ap.getCard('Daily Expenses').getByRole('button', { name: 'Delete', exact: true }).click();
    await expect(ap.getCard('Daily Expenses').getByRole('alert')).toContainText('Archive it or move its transactions');
    await expect(ap.getCard('Daily Expenses')).toBeVisible();
  }
  await ap.createAccount('Empty regression account', 'expenses');
  await expect(page.locator('#account-label')).toHaveValue('');
  await ap.deleteAccount('Empty regression account');
});

test('category recommendations do not clear transaction validation errors', async ({ page }) => {
  const tp = new TransactionsPage(page);
  await tp.goto();
  let release!: () => void;
  let started!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  const requestStarted = new Promise<void>(resolve => { started = resolve; });
  await page.route('**/partials/transactions/recommend-category', async route => {
    const response = await route.fetch();
    started();
    await pending;
    await route.fulfill({ response });
  });
  await tp.fillCreateForm({ label: 'Invalid transaction', amount: '0.00', mode: 'credit' });
  await requestStarted;
  await tp.submitCreate();
  await expect(tp.getCreateError()).toContainText('amount must be non-zero');
  const recommendation = page.waitForResponse('**/partials/transactions/recommend-category');
  release();
  await recommendation;
  await expect(tp.getCreateError()).toContainText('amount must be non-zero');
  await expect(tp.getCreateLabelInput()).toHaveValue('Invalid transaction');
});

test('category forms reset after success and show inline label errors', async ({ page }) => {
  const cp = new CategoriesPage(page);
  await cp.goto();
  await cp.createCategory('Regression category');
  await expect(page.locator('#cat-label')).toHaveValue('');
  await cp.getCard('Regression category').getByTitle('Edit label').click();
  await cp.getCard('Regression category').locator('[name="label"]').fill('   ');
  await cp.getCard('Regression category').getByRole('button', { name: 'Save', exact: true }).click();
  await expect(cp.getCard('Regression category').getByRole('alert')).toContainText('label is required');
});

test('income forms reset after success and preserve rejected duplicate input', async ({ page }) => {
  const ip = new IncomePage(page);
  await ip.goto();
  await ip.create({ year: 2024, gross: '10000' });
  await expect(ip.getForm().locator('[name="gross_income"]')).toHaveValue('');
  await ip.getForm().locator('[name="tax_year"]').fill('2024');
  await ip.getForm().locator('[name="gross_income"]').fill('12000');
  await ip.getForm().getByRole('button', { name: 'Add annual income' }).click();
  await expect(ip.getForm().getByRole('alert')).toContainText('already exists');
  await expect(ip.getForm().locator('[name="gross_income"]')).toHaveValue('12000');
  await expect(ip.getCards()).toHaveCount(1);
});
