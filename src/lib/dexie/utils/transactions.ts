import { liveQuery } from 'dexie';
import { db } from '..';

export function getTransactionTotal() {
	return liveQuery(() =>
		db.tx.toArray().then((txs) => txs.reduce((acc, tx) => acc + tx.amount, 0))
	);
}
