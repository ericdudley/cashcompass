import { test, expect } from './fixtures';
import { CategoriesPage } from './pages/categories.page';

test('create category', async ({ page }) => {
	const cp = new CategoriesPage(page);
	await cp.goto();

	await cp.createCategory('TestCreate');

	await expect(cp.getCard('TestCreate')).toBeVisible();
	await expect(cp.getList()).toContainText('TestCreate');
});

test('edit label via overlay — save', async ({ page }) => {
	const cp = new CategoriesPage(page);
	await cp.goto();

	await cp.createCategory('EditMe');
	await cp.editLabel('EditMe', 'EditedLabel');

	await expect(cp.getCard('EditedLabel')).toBeVisible();
	await expect(page.locator('[data-label="EditMe"]')).not.toBeAttached();
});

test('edit label via overlay — cancel', async ({ page }) => {
	const cp = new CategoriesPage(page);
	await cp.goto();

	await cp.createCategory('CancelEdit');
	await cp.cancelEdit('CancelEdit');

	await expect(cp.getCard('CancelEdit')).toBeVisible();
});

test('delete category with confirm', async ({ page }) => {
	const cp = new CategoriesPage(page);
	await cp.goto();

	await cp.createCategory('DeleteMe');
	await expect(cp.getCard('DeleteMe')).toBeVisible();

	await cp.deleteCategory('DeleteMe');

	await expect(page.locator('[data-label="DeleteMe"]')).not.toBeAttached();
});

test('multiple categories appear in list', async ({ page }) => {
	const cp = new CategoriesPage(page);
	await cp.goto();

	await cp.createCategory('Alpha');
	await cp.createCategory('Beta');
	await cp.createCategory('Gamma');

	await expect(cp.getList()).toContainText('Alpha');
	await expect(cp.getList()).toContainText('Beta');
	await expect(cp.getList()).toContainText('Gamma');
});
