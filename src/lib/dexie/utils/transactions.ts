import { liveQuery } from 'dexie';
import { db } from '..';

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

export function getNetWorthByMonth() {
	return liveQuery(async () => {
		// Get all transactions, sorted by date
		const txs = await db.tx.orderBy('unixMs').toArray();
		// Get all accounts
		const accounts = await db.account.toArray();
		const accountBalances: { [accountId: string]: number } = {};
		const netWorthByMonth: { [month: string]: { [accountId: string]: number } } = {};

		// Initialize account balances
		for (const account of accounts) {
			accountBalances[account.id] = 0;
		}

		for (const tx of txs) {
			const accountId = tx.account?.id;
			if (!accountId) {
				continue;
			}

			accountBalances[accountId] += tx.amount;

			const date = new Date(tx.unixMs);
			const yearMonth = `${date.getFullYear()}-${(date.getMonth() + 1)
				.toString()
				.padStart(2, '0')}`;

			if (!(yearMonth in netWorthByMonth)) {
				netWorthByMonth[yearMonth] = {};
			}

			netWorthByMonth[yearMonth][accountId] = accountBalances[accountId];
		}

		// Get a sorted list of all months
		const months = Object.keys(netWorthByMonth).sort();

		// Map account IDs to labels
		const accountLabels: { [accountId: string]: string } = {};
		for (const account of accounts) {
			accountLabels[account.id] = account.label;
		}

		// Build the result with filled-in balances
		const result: { [accountLabel: string]: { [month: string]: number } } = {};

		for (const accountId in accountBalances) {
			const accountLabel = accountLabels[accountId];
			let lastBalance = 0;
			result[accountLabel] = {};

			for (const month of months) {
				if (netWorthByMonth[month][accountId] !== undefined) {
					lastBalance = netWorthByMonth[month][accountId];
				}
				result[accountLabel][month] = lastBalance;
			}
		}
		return {
			months,
			data: result // { accountLabel: { 'yyyy-MM': balance } }
		};
	});
}
