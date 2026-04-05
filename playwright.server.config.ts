import type { PlaywrightTestConfig } from '@playwright/test';

const TEST_PORT = 18080;
const TEST_DB = '/tmp/cashcompass_test.db';

const config: PlaywrightTestConfig = {
	webServer: {
		command: `CASHCOMPASS_DB_PATH=${TEST_DB} CASHCOMPASS_PORT=${TEST_PORT} /usr/local/go/bin/go run ./cmd/server`,
		cwd: './server',
		port: TEST_PORT,
		reuseExistingServer: false,
		timeout: 30000
	},
	testDir: 'tests/server',
	testMatch: /(.+\.)?(test|spec)\.[jt]s/,
	workers: 1,
	use: { baseURL: `http://localhost:${TEST_PORT}` }
};

export default config;
