import type { Category } from '$lib/dexie/models/category';
import Dexie, { type EntityTable } from 'dexie';
import type { Transaction } from './models/transaction';

export type CashCompassDexie = Dexie & {
	category: EntityTable<Category, 'id'>;
	tx: EntityTable<Transaction, 'id'>;
};

export let db: CashCompassDexie;

export function initDb() {
	if (!!db) {
		return;
	}

	db = new Dexie('cashcompass') as CashCompassDexie;

	// Schema declaration:
	db.version(1).stores({
		category: 'id, label',
		tx: 'id, unixMs, yyyyMMDd, amount, category.id, category.label, label'
	});

	return db;
}
