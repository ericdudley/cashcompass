import { test as base } from '@playwright/test';

export const test = base.extend<{ resetDB: void }>({
    resetDB: [async ({ request }, use) => {
        const response = await request.post('/dev/reset');
        if (!response.ok()) {
            throw new Error(`DB reset failed: ${response.status()} ${await response.text()}`);
        }
        await use();
    }, { auto: true }]
});

export { expect } from '@playwright/test';
