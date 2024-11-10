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
		tx: 'id, iso8601, yyyyMMDd, amount, category.id, category.label, label, account.id, account.accountType',
		account: 'id, label'
	});

	const isLocal = window.location.hostname === 'localhost';
	const databaseUrl = isLocal ? 'https://zosfaqgud.dexie.cloud' : 'https://zknh9tjsp.dexie.cloud';
	db.cloud.configure({
		databaseUrl,
		requireAuth: true
	});

	db.tx.hook('creating', function (primKey, tx, transaction) {
		tx.yyyyMMDd = tx.iso8601.slice(0, 10);
	});

	db.tx.hook('updating', function (mods: Partial<Transaction>, primKey, tx, transaction) {
		if (mods.hasOwnProperty('iso8601') && typeof mods.iso8601 === 'string') {
			return {
				yyyyMMDd: mods.iso8601.slice(0, 10)
			};
		}
	});

	return db;
}
