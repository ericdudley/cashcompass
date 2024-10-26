import type { Category } from '$lib/dexie/models/category';
import Dexie, { type EntityTable } from 'dexie';
import type { Transaction } from './models/transaction';
import { dexieCloud } from 'dexie-cloud-addon';
import type { Account } from './models/account';

export type CashCompassDexie = Dexie & {
	category: EntityTable<Category, 'id'>;
	tx: EntityTable<Transaction, 'id'>;
	account: EntityTable<Account, 'id'>;
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
		tx: 'id, unixMs, yyyyMMDd, amount, category.id, category.label, label',
		account: 'id, label'
	});

	db.cloud.configure({
		databaseUrl: 'https://zosfaqgud.dexie.cloud',
		requireAuth: true
	});

	return db;
}
