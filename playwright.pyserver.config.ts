import { defineConfig, devices } from '@playwright/test';

const TEST_PORT = 18081;
const TEST_DB = '/tmp/cashcompass_py_test.db';

export default defineConfig({
	webServer: {
		command: `CASHCOMPASS_DB_PATH=${TEST_DB} CASHCOMPASS_PORT=${TEST_PORT} CASHCOMPASS_DEV=true .venv/bin/python -m uvicorn src.main:app --port ${TEST_PORT} --no-access-log`,
		port: TEST_PORT,
		reuseExistingServer: false,
		timeout: 30000,
	},
	testDir: 'tests/server',
	testMatch: /(.+\.)?(test|spec)\.[jt]s/,
	workers: 1,
	use: { baseURL: `http://localhost:${TEST_PORT}` },
	projects: [
		{
			name: 'desktop',
			use: { ...devices['Desktop Chrome'] },
		},
		{
			name: 'mobile',
			use: { ...devices['Pixel 5'] },
		},
	],
});
