import type { Category } from '$lib/dexie/models/category';
import Dexie, { type EntityTable } from 'dexie';
import type { Transaction } from './models/transaction';
import { dexieCloud } from 'dexie-cloud-addon';

export type CashCompassDexie = Dexie & {
	category: EntityTable<Category, 'id'>;
	tx: EntityTable<Transaction, 'id'>;
};

export let db: CashCompassDexie;

export function initDb() {
	if (db) {
		return;
	}

	db = new Dexie('cashcompass', {
		addons: [dexieCloud]
	}) as CashCompassDexie;

	// Schema declaration:
	db.version(1).stores({
		category: 'id, label',
		tx: 'id, unixMs, yyyyMMDd, amount, category.id, category.label, label'
	});

	db.cloud.configure({
		databaseUrl: 'https://zosfaqgud.dexie.cloud',
		requireAuth: true
	});

	return db;
}
