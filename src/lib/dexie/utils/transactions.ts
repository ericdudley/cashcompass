import { formatYyyyMMDd } from '$lib/utils/date';
import { parseISO } from 'date-fns';
import { liveQuery, type Observable } from 'dexie';
import sortBy from 'lodash-es/sortBy';
import { db } from '..';
import type { Transaction } from '../models/transaction';
import type { Account } from '../models/account';

export function searchLiveQuery({
	startDate,
	endDate,
	prefix,
	accountType
}: {
	startDate: Date;
	endDate: Date;
	prefix?: string;
	accountType?: Account['accountType'];
}): Observable<Transaction[]> {
	return liveQuery(() =>
		db.tx
			.where('yyyyMMDd')
			.between(formatYyyyMMDd(startDate), formatYyyyMMDd(endDate), true, true)
			.and((tx) => (!!tx?.label?.startsWith && !!prefix ? tx.label.startsWith(prefix) : true))
			.and(
				(tx) =>
					!!(!!accountType
						? tx.account?.accountType && tx.account.accountType === accountType
						: true)
			)
			.sortBy('iso8601')
	);
}

function getMonthlyTotals(txs: Transaction[]): { [month: string]: number } {
	const totals: { [month: string]: number } = {};

	txs.forEach((tx) => {
		const yearMonth = tx.yyyyMMDd.slice(0, 7);
		totals[yearMonth] = (totals[yearMonth] || 0) + tx.amount;
	});

	return totals;
}

export function getTotalThisMonth(txs: Transaction[]): number {
	const now = new Date();
	const yearMonth = `${now.getFullYear()}-${(now.getMonth() + 1).toString().padStart(2, '0')}`;

	return txs
		.filter((tx) => tx.amount < 0 && tx.iso8601.startsWith(yearMonth))
		.reduce((acc, tx) => acc + tx.amount, 0);
}

export function getPercentageDiffFromLastMonth(txs: Transaction[]): number {
	const now = new Date();
	const year = now.getFullYear();
	const month = now.getMonth() + 1;
	const currentYearMonth = year * 12 + month;

	const monthlyTotals = getMonthlyTotals(txs);
	const lastMonth = `${year}-${(month - 1).toString().padStart(2, '0')}`;

	const lastMonthTotal = monthlyTotals[lastMonth] || 0;
	const thisMonthTotal = monthlyTotals[`${year}-${month.toString().padStart(2, '0')}`] || 0;

	if (lastMonthTotal === 0) {
		return thisMonthTotal > 0 ? 100 : thisMonthTotal < 0 ? -100 : 0;
	}

	return ((thisMonthTotal - lastMonthTotal) / lastMonthTotal) * 100;
}

/**
 * Get the average monthly spending. Only considers months that have fully passed.
 */
export function getAverageMonthly(txs: Transaction[]): number {
	const now = new Date();
	const year = now.getFullYear();
	const month = now.getMonth() + 1;
	const currentYearMonth = year * 12 + month;

	const monthlyTotals = getMonthlyTotals(txs);
	const fullMonths = Object.keys(monthlyTotals).filter((month) => {
		const [txYear, txMonth] = month.split('-').map(Number);
		return txYear * 12 + txMonth < currentYearMonth;
	});

	const total = fullMonths.reduce((acc, month) => acc + monthlyTotals[month], 0);
	return fullMonths.length ? total / fullMonths.length : 0;
}

export function getTransactionTotal() {
	return liveQuery(() =>
		db.tx.toArray().then((txs) => txs.reduce((acc, tx) => acc + tx.amount, 0))
	);
}

export function getTransactionTotalByYear() {
	return liveQuery(() =>
		db.tx.toArray().then((txs) => {
			const totals: { [year: string]: number } = {};
			txs.forEach((tx) => {
				const year = tx.yyyyMMDd.slice(0, 4);
				totals[year] = (totals[year] || 0) + tx.amount;
			});
			return totals;
		})
	);
}

export function getNetWorthByMonth(txs: Transaction[]) {
	const accountBalances: { [accountId: string]: number } = {};
	const netWorthByMonth: { [month: string]: { [accountId: string]: number } } = {};

	// Extract accounts from transactions
	const accountsSet = new Set<string>();
	const accountLabels: { [accountId: string]: string } = {};

	// Collect all account IDs and labels from transactions
	txs.forEach((tx) => {
		const accountId = tx.account?.id;
		const accountLabel = tx.account?.label;

		if (accountId && accountLabel) {
			accountsSet.add(accountId);
			accountLabels[accountId] = accountLabel;
		}
	});

	// Initialize account balances
	accountsSet.forEach((accountId) => {
		accountBalances[accountId] = 0;
	});

	const sortedTxs = sortBy(txs, 'iso8601');

	// Process each transaction
	for (const tx of sortedTxs) {
		const accountId = tx.account?.id;
		if (!accountId) {
			continue;
		}

		// Update account balance
		accountBalances[accountId] += tx.amount;

		const date = parseISO(tx.iso8601);
		const yearMonth = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;

		if (!(yearMonth in netWorthByMonth)) {
			netWorthByMonth[yearMonth] = {};
		}

		// Record net worth for the month
		netWorthByMonth[yearMonth][accountId] = accountBalances[accountId];
	}

	// Get a sorted list of all months
	const months = Object.keys(netWorthByMonth).sort();

	// Build the result with filled-in balances
	const result: { [accountLabel: string]: { [month: string]: number } } = {};

	accountsSet.forEach((accountId) => {
		const accountLabel = accountLabels[accountId];
		let lastBalance = 0;
		result[accountLabel] = {};

		for (const month of months) {
			if (netWorthByMonth[month][accountId] !== undefined) {
				lastBalance = netWorthByMonth[month][accountId];
			}
			result[accountLabel][month] = lastBalance;
		}
	});

	return {
		months,
		data: result // { accountLabel: { 'yyyy-MM': balance } }
	};
}

interface CategoryMonthlyTotals {
	[category: string]: {
		[month: string]: number;
		Total: number;
		Average: number;
	};
}

interface AggregatedData {
	data: CategoryMonthlyTotals;
	months: string[];
	totalsPerMonth: { [month: string]: number };
	totalOverall: number;
	averagePerCategory: { [category: string]: number };
}

export function getCategoryMonthlyTotals(txs: Transaction[]): AggregatedData {
	const data: CategoryMonthlyTotals = {};
	const totalsPerMonth: { [month: string]: number } = {};
	const monthsSet: Set<string> = new Set();
	const categoryTotals: { [category: string]: number } = {};
	const categoryCounts: { [category: string]: number } = {};

	// Process each transaction
	txs.forEach((tx) => {
		const month = tx.yyyyMMDd.slice(0, 7); // Extract 'YYYY-MM'
		const category = tx.category?.label || 'Uncategorized';

		monthsSet.add(month);

		// Initialize nested objects if they don't exist
		if (!data[category]) {
			data[category] = { Total: 0, Average: 0 };
		}
		if (!data[category][month]) {
			data[category][month] = 0;
		}
		if (!totalsPerMonth[month]) {
			totalsPerMonth[month] = 0;
		}
		if (!categoryTotals[category]) {
			categoryTotals[category] = 0;
			categoryCounts[category] = 0;
		}

		// Aggregate amounts
		data[category][month] += tx.amount;
		data[category]['Total'] += tx.amount;
		totalsPerMonth[month] += tx.amount;
		categoryTotals[category] += tx.amount;
		categoryCounts[category] += 1;
	});

	// Calculate averages for each category
	for (const category in data) {
		const monthsWithData = Object.keys(data[category]).filter(
			(key) => key !== 'Total' && key !== 'Average'
		);
		const monthsCount = monthsWithData.length;
		data[category]['Average'] = monthsCount ? data[category]['Total'] / monthsCount : 0;
	}

	// Get sorted list of months
	const months = Array.from(monthsSet).sort();

	// Calculate total overall
	const totalOverall = Object.values(totalsPerMonth).reduce((acc, val) => acc + val, 0);

	// Prepare average per category
	const averagePerCategory: { [category: string]: number } = {};
	for (const category in categoryTotals) {
		averagePerCategory[category] = categoryCounts[category]
			? categoryTotals[category] / categoryCounts[category]
			: 0;
	}

	return {
		data,
		months,
		totalsPerMonth,
		totalOverall,
		averagePerCategory
	};
}
