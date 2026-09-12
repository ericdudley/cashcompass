import type { Page, Locator } from '@playwright/test';

export class FlowPage {
	constructor(private page: Page) {}

	async goto(year?: number) {
		await this.page.goto(year ? `/flow?year=${year}` : '/flow');
	}

	getYearSelect(): Locator {
		return this.page.locator('[data-testid="flow-year-select"]');
	}

	getSummary(): Locator {
		return this.page.locator('[data-testid="flow-summary"]');
	}

	getChart(): Locator {
		return this.page.locator('[data-testid="flow-chart"]');
	}

	getSankey(): Locator {
		return this.page.locator('[data-testid="flow-sankey"]');
	}

	getNode(id: string): Locator {
		return this.page.locator(`[data-flow-node-id="${id}"]`);
	}

	getGroup(id: string): Locator {
		return this.page.locator(`[data-flow-group-id="${id}"]`);
	}

	getNetWorthComparison(): Locator {
		return this.page.locator('[data-testid="flow-net-worth-comparison"]');
	}

	getComparisonMessage(): Locator {
		return this.page.locator('[data-testid="flow-comparison-message"]');
	}

	getTooltip(): Locator {
		return this.page.locator('[data-testid="flow-tooltip"]');
	}

	getDetails(): Locator {
		return this.page.locator('[data-testid="flow-details"]');
	}

	getEmptyIncome(): Locator {
		return this.page.locator('[data-testid="flow-empty-income"]');
	}
}
