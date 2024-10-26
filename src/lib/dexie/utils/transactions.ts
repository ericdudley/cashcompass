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
